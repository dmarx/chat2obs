# llm_archive/builders/trees.py
"""Dialogue tree analysis and materialization."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session
from loguru import logger

from llm_archive.models import (
    Dialogue, Message,
    DialogueTree, MessagePath, LinearSequence, SequenceMessage,
)


@dataclass
class TreeNode:
    """In-memory representation of a message in the tree."""
    message_id: UUID
    parent_id: UUID | None
    role: str
    created_at: datetime | None
    children: list['TreeNode'] = field(default_factory=list)
    
    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    @property
    def timestamp(self) -> float:
        if self.created_at is None:
            return 0.0
        return self.created_at.timestamp()


@dataclass
class TreeAnalysis:
    """Results of analyzing a dialogue tree."""
    dialogue_id: UUID
    total_nodes: int
    max_depth: int
    branch_count: int
    leaf_count: int
    primary_leaf: TreeNode | None
    primary_path_ids: set[UUID]
    has_regenerations: bool
    has_edits: bool
    nodes: dict[UUID, TreeNode]
    leaves: list[TreeNode]


class TreeBuilder:
    """
    Analyzes dialogue trees and materializes derived structures.
    
    Works uniformly across all sources:
    - Linear dialogues (Claude) produce degenerate trees (branch_count=0)
    - Branched dialogues (ChatGPT) produce full tree analysis
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def build_all(self) -> dict[str, int]:
        """Build tree analysis for all dialogues."""
        dialogues = self.session.query(Dialogue).all()
        
        counts = {
            'dialogues': 0,
            'linear': 0,
            'branched': 0,
            'paths': 0,
            'sequences': 0,
            'sequence_messages': 0,
        }
        
        for dialogue in dialogues:
            try:
                result = self.build_for_dialogue(dialogue.id)
                counts['dialogues'] += 1
                counts['paths'] += result['paths']
                counts['sequences'] += result['sequences']
                counts['sequence_messages'] += result['sequence_messages']
                
                if result['is_linear']:
                    counts['linear'] += 1
                else:
                    counts['branched'] += 1
                    
            except Exception as e:
                logger.error(f"Failed to build tree for {dialogue.id}: {e}")
                self.session.rollback()
        
        self.session.commit()
        logger.info(f"Tree building complete: {counts}")
        return counts
    
    def build_for_dialogue(self, dialogue_id: UUID) -> dict[str, int]:
        """Build tree analysis for a single dialogue."""
        # Clear existing derived data
        self._clear_derived(dialogue_id)
        
        # Load messages
        messages = (
            self.session.query(Message)
            .filter(Message.dialogue_id == dialogue_id)
            .all()
        )
        
        if not messages:
            return {'paths': 0, 'sequences': 0, 'sequence_messages': 0, 'is_linear': True}
        
        # Analyze tree structure
        analysis = self._analyze_tree(dialogue_id, messages)
        
        # Persist dialogue tree
        self._persist_dialogue_tree(analysis)
        
        # Persist message paths
        paths_count = self._persist_message_paths(analysis)
        
        # Persist linear sequences
        sequences_count, seq_msgs_count = self._persist_linear_sequences(analysis)
        
        self.session.flush()
        
        return {
            'paths': paths_count,
            'sequences': sequences_count,
            'sequence_messages': seq_msgs_count,
            'is_linear': analysis.branch_count == 0,
        }
    
    def _analyze_tree(self, dialogue_id: UUID, messages: list[Message]) -> TreeAnalysis:
        """Analyze the tree structure of a dialogue."""
        # Build in-memory tree
        nodes, roots = self._build_tree(messages)
        
        if not roots:
            # No root found - create empty analysis
            return TreeAnalysis(
                dialogue_id=dialogue_id,
                total_nodes=0,
                max_depth=0,
                branch_count=0,
                leaf_count=0,
                primary_leaf=None,
                primary_path_ids=set(),
                has_regenerations=False,
                has_edits=False,
                nodes={},
                leaves=[],
            )
        
        # Use first root (should typically be only one)
        root = roots[0]
        
        # Compute depths
        depths = self._compute_depths(root)
        max_depth = max(depths.values()) if depths else 0
        
        # Find leaves and branches
        leaves = [n for n in nodes.values() if n.is_leaf]
        branch_count = sum(1 for n in nodes.values() if len(n.children) > 1)
        
        # Select primary leaf (longest path, then most recent)
        primary_leaf = self._select_primary_leaf(leaves, nodes)
        primary_path_ids = self._get_path_ids(primary_leaf, nodes) if primary_leaf else set()
        
        # Classify branches
        has_regenerations, has_edits = self._classify_branches(nodes)
        
        return TreeAnalysis(
            dialogue_id=dialogue_id,
            total_nodes=len(nodes),
            max_depth=max_depth,
            branch_count=branch_count,
            leaf_count=len(leaves),
            primary_leaf=primary_leaf,
            primary_path_ids=primary_path_ids,
            has_regenerations=has_regenerations,
            has_edits=has_edits,
            nodes=nodes,
            leaves=leaves,
        )
    
    def _build_tree(self, messages: list[Message]) -> tuple[dict[UUID, TreeNode], list[TreeNode]]:
        """Build in-memory tree from messages."""
        nodes: dict[UUID, TreeNode] = {}
        children_by_parent: dict[UUID | None, list[TreeNode]] = defaultdict(list)
        
        for msg in messages:
            node = TreeNode(
                message_id=msg.id,
                parent_id=msg.parent_id,
                role=msg.role,
                created_at=msg.created_at,
            )
            nodes[msg.id] = node
            children_by_parent[msg.parent_id].append(node)
        
        # Link children (sorted by timestamp)
        for node in nodes.values():
            node.children = sorted(
                children_by_parent.get(node.message_id, []),
                key=lambda n: n.timestamp
            )
        
        # Find roots (nodes with no parent or parent not in set)
        roots = sorted(
            children_by_parent.get(None, []),
            key=lambda n: n.timestamp
        )
        
        return nodes, roots
    
    def _compute_depths(self, root: TreeNode) -> dict[UUID, int]:
        """Compute depth for each node starting from root."""
        depths = {}
        
        def traverse(node: TreeNode, depth: int):
            depths[node.message_id] = depth
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(root, 0)
        return depths
    
    def _select_primary_leaf(
        self, 
        leaves: list[TreeNode], 
        nodes: dict[UUID, TreeNode]
    ) -> TreeNode | None:
        """Select primary leaf (longest path, then most recent)."""
        if not leaves:
            return None
        
        def score(leaf: TreeNode) -> tuple[int, float]:
            path_length = len(self._get_ancestor_ids(leaf, nodes)) + 1
            return (path_length, leaf.timestamp)
        
        return max(leaves, key=score)
    
    def _get_ancestor_ids(self, node: TreeNode, nodes: dict[UUID, TreeNode]) -> list[UUID]:
        """Get ancestor IDs from root to parent (excluding node)."""
        ancestors = []
        current = node
        
        while current.parent_id is not None:
            ancestors.append(current.parent_id)
            current = nodes.get(current.parent_id)
            if current is None:
                break
        
        ancestors.reverse()
        return ancestors
    
    def _get_path_ids(self, node: TreeNode, nodes: dict[UUID, TreeNode]) -> set[UUID]:
        """Get all IDs on path from root to node (inclusive)."""
        ids = set(self._get_ancestor_ids(node, nodes))
        ids.add(node.message_id)
        return ids
    
    def _classify_branches(self, nodes: dict[UUID, TreeNode]) -> tuple[bool, bool]:
        """Determine if tree has regenerations and/or edits."""
        has_regenerations = False
        has_edits = False
        
        for node in nodes.values():
            if len(node.children) <= 1:
                continue
            
            child_roles = [c.role for c in node.children]
            
            if len(set(child_roles)) == 1:
                has_regenerations = True
            else:
                has_edits = True
        
        return has_regenerations, has_edits
    
    def _persist_dialogue_tree(self, analysis: TreeAnalysis):
        """Persist dialogue tree record."""
        tree = DialogueTree(
            dialogue_id=analysis.dialogue_id,
            total_nodes=analysis.total_nodes,
            max_depth=analysis.max_depth,
            branch_count=analysis.branch_count,
            leaf_count=analysis.leaf_count,
            primary_leaf_id=analysis.primary_leaf.message_id if analysis.primary_leaf else None,
            primary_path_length=len(analysis.primary_path_ids),
            has_regenerations=analysis.has_regenerations,
            has_edits=analysis.has_edits,
        )
        self.session.add(tree)
    
    def _persist_message_paths(self, analysis: TreeAnalysis) -> int:
        """Persist message path records."""
        if not analysis.nodes:
            return 0
        
        # Compute sibling indices
        sibling_indices = self._compute_sibling_indices(analysis.nodes)
        
        count = 0
        for node in analysis.nodes.values():
            ancestors = self._get_ancestor_ids(node, analysis.nodes)
            
            path = MessagePath(
                message_id=node.message_id,
                dialogue_id=analysis.dialogue_id,
                ancestor_path=ancestors,
                depth=len(ancestors),
                is_root=node.parent_id is None,
                is_leaf=node.is_leaf,
                child_count=len(node.children),
                sibling_index=sibling_indices.get(node.message_id, 0),
                is_on_primary_path=node.message_id in analysis.primary_path_ids,
            )
            self.session.add(path)
            count += 1
        
        return count
    
    def _compute_sibling_indices(self, nodes: dict[UUID, TreeNode]) -> dict[UUID, int]:
        """Compute sibling index for each node."""
        indices = {}
        
        for node in nodes.values():
            for idx, child in enumerate(node.children):
                indices[child.message_id] = idx
        
        # Roots get index 0
        for node in nodes.values():
            if node.parent_id is None:
                indices[node.message_id] = 0
        
        return indices
    
    def _persist_linear_sequences(self, analysis: TreeAnalysis) -> tuple[int, int]:
        """Persist linear sequences for each leaf."""
        if not analysis.leaves:
            return 0, 0
        
        seq_count = 0
        msg_count = 0
        
        for leaf in analysis.leaves:
            is_primary = analysis.primary_leaf and leaf.message_id == analysis.primary_leaf.message_id
            path_ids = self._get_ancestor_ids(leaf, analysis.nodes) + [leaf.message_id]
            
            # Find branch point for non-primary paths
            branch_reason = None
            branched_at_id = None
            branched_at_depth = None
            
            if not is_primary and analysis.primary_path_ids:
                for depth, msg_id in enumerate(path_ids):
                    if msg_id not in analysis.primary_path_ids:
                        if depth > 0:
                            branched_at_id = path_ids[depth - 1]
                            branched_at_depth = depth - 1
                            
                            # Classify branch
                            branch_node = analysis.nodes.get(branched_at_id)
                            if branch_node:
                                child_roles = [c.role for c in branch_node.children]
                                if len(set(child_roles)) == 1:
                                    branch_reason = 'regeneration'
                                else:
                                    branch_reason = 'edit'
                        break
            
            sequence = LinearSequence(
                dialogue_id=analysis.dialogue_id,
                leaf_message_id=leaf.message_id,
                sequence_length=len(path_ids),
                is_primary=is_primary,
                branch_reason=branch_reason,
                branched_at_message_id=branched_at_id,
                branched_at_depth=branched_at_depth,
            )
            self.session.add(sequence)
            self.session.flush()
            
            # Create sequence messages
            for pos, msg_id in enumerate(path_ids):
                seq_msg = SequenceMessage(
                    sequence_id=sequence.id,
                    message_id=msg_id,
                    position=pos,
                )
                self.session.add(seq_msg)
                msg_count += 1
            
            seq_count += 1
        
        return seq_count, msg_count
    
    def _clear_derived(self, dialogue_id: UUID):
        """Clear existing derived data for a dialogue."""
        did = str(dialogue_id)
        
        # Delete in dependency order
        self.session.execute(
            text("""
                DELETE FROM derived.sequence_messages 
                WHERE sequence_id IN (
                    SELECT id FROM derived.linear_sequences 
                    WHERE dialogue_id = :did
                )
            """),
            {'did': did}
        )
        self.session.execute(
            text("DELETE FROM derived.linear_sequences WHERE dialogue_id = :did"),
            {'did': did}
        )
        self.session.execute(
            text("DELETE FROM derived.message_paths WHERE dialogue_id = :did"),
            {'did': did}
        )
        self.session.execute(
            text("DELETE FROM derived.dialogue_trees WHERE dialogue_id = :did"),
            {'did': did}
        )