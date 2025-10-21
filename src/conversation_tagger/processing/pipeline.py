# conversation_tagger/processing/pipeline.py
"""
Processing pipeline machinery for batch conversation processing.
"""

from typing import List, Dict, Any, Optional, Set, Callable
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

from ..core.conversation import Conversation
from ..core.generate import generate_notes
from ..factory import create_default_tagger
from ..data.loaders import load_conversations
from .filters import ConversationFilter, FilterCriteria


@dataclass
class ProcessingConfig:
    """Configuration for processing pipeline."""
    
    sources: List[str]  # List of sources to process (e.g., ['oai', 'claude'])
    output_dir: str = "../data/staging"
    
    # Custom rules to add per source
    source_rules: Dict[str, Dict[str, Callable]] = None
    
    # Filtering criteria
    filter_criteria: Optional[FilterCriteria] = None
    
    # Note generation settings
    generate_notes_enabled: bool = True
    template_name: str = 'article_body.md.jinja'
    
    def __post_init__(self):
        if self.source_rules is None:
            self.source_rules = {}


class ProcessingPipeline:
    """Handles processing conversations from a single source."""
    
    def __init__(self, source: str, config: ProcessingConfig):
        self.source = source
        self.config = config
        
        # Create tagger for this source
        self.tagger = create_default_tagger(source=source)
        
        # Add any custom rules for this source
        if source in config.source_rules:
            for rule_name, rule_func in config.source_rules[source].items():
                self.tagger.add_conversation_rule(rule_name, rule_func)
        
        logger.info(f"Initialized processing pipeline for source: {source}")
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load conversation data for this source."""
        logger.info(f"Loading conversations for source: {self.source}")
        return load_conversations(self.source)
    
    def tag_conversations(self, conversations: List[Dict[str, Any]]) -> List[Conversation]:
        """Apply tagging to all conversations."""
        logger.info(f"Tagging {len(conversations)} conversations for source: {self.source}")
        
        tagged_conversations = []
        for i, conv_data in enumerate(conversations):
            try:
                tagged_conv = self.tagger.tag_conversation(conv_data)
                tagged_conversations.append(tagged_conv)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Tagged {i + 1}/{len(conversations)} conversations")
                    
            except Exception as e:
                logger.error(f"Error tagging conversation {i}: {e}")
                continue
        
        logger.info(f"Successfully tagged {len(tagged_conversations)} conversations")
        return tagged_conversations
    
    def filter_conversations(self, conversations: List[Conversation]) -> List[Conversation]:
        """Apply filtering criteria to conversations."""
        if not self.config.filter_criteria:
            return conversations
        
        logger.info(f"Applying filters to {len(conversations)} conversations")
        filtered = ConversationFilter.filter_conversations(
            conversations, 
            self.config.filter_criteria
        )
        
        logger.info(f"Filtering resulted in {len(filtered)} conversations")
        return filtered
    
    def generate_outputs(self, conversations: List[Conversation]) -> int:
        """Generate outputs (notes) for conversations."""
        if not self.config.generate_notes_enabled:
            logger.info("Note generation disabled")
            return 0
        
        generated_count = 0
        
        for conversation in conversations:
            try:
                generate_notes(
                    conversation,
                    template_name=self.config.template_name,
                    output_dir=self.config.output_dir
                )
                generated_count += 1
                
            except Exception as e:
                logger.error(f"Error generating notes for conversation {conversation.conversation_id}: {e}")
                continue
        
        logger.info(f"Generated notes for {generated_count} conversations")
        return generated_count
    
    def process(self) -> Dict[str, Any]:
        """
        Run the complete processing pipeline for this source.
        
        Returns:
            Processing results summary
        """
        logger.info(f"Starting processing pipeline for source: {self.source}")
        
        # Load data
        raw_conversations = self.load_data()
        
        # Tag conversations
        tagged_conversations = self.tag_conversations(raw_conversations)
        
        # Apply filtering
        filtered_conversations = self.filter_conversations(tagged_conversations)
        
        # Generate outputs
        generated_count = self.generate_outputs(filtered_conversations)
        
        results = {
            'source': self.source,
            'raw_count': len(raw_conversations),
            'tagged_count': len(tagged_conversations),
            'filtered_count': len(filtered_conversations),
            'generated_count': generated_count
        }
        
        logger.info(f"Pipeline completed for {self.source}: {results}")
        return results


class BatchProcessor:
    """Handles batch processing across multiple sources."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        
        # Ensure output directory exists
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized batch processor for sources: {config.sources}")
    
    def process_all(self) -> Dict[str, Any]:
        """
        Process all configured sources.
        
        Returns:
            Summary results for all sources
        """
        all_results = {}
        total_generated = 0
        
        logger.info(f"Starting batch processing for {len(self.config.sources)} sources")
        
        for source in self.config.sources:
            try:
                pipeline = ProcessingPipeline(source, self.config)
                results = pipeline.process()
                
                all_results[source] = results
                total_generated += results['generated_count']
                
            except Exception as e:
                logger.error(f"Error processing source {source}: {e}")
                all_results[source] = {'error': str(e)}
        
        summary = {
            'sources_processed': len(all_results),
            'total_generated': total_generated,
            'results_by_source': all_results
        }
        
        logger.info(f"Batch processing completed: {summary}")
        return summary


# Convenience functions for common processing patterns
def process_single_source(source: str, 
                         output_dir: str = "../data/staging",
                         filter_criteria: Optional[FilterCriteria] = None) -> Dict[str, Any]:
    """Process conversations from a single source."""
    config = ProcessingConfig(
        sources=[source],
        output_dir=output_dir,
        filter_criteria=filter_criteria
    )
    
    pipeline = ProcessingPipeline(source, config)
    return pipeline.process()


def process_with_gizmo_filter(gizmo_id: str,
                            sources: List[str] = ['oai', 'claude'],
                            output_dir: str = "../data/staging") -> Dict[str, Any]:
    """Process conversations that use a specific gizmo."""
    from .filters import create_gizmo_filter
    
    config = ProcessingConfig(
        sources=sources,
        output_dir=output_dir,
        filter_criteria=create_gizmo_filter(gizmo_id)
    )
    
    processor = BatchProcessor(config)
    return processor.process_all()


def process_claude_obsidian_chats(obsidian_chat_ids: Set[str],
                                output_dir: str = "../data/staging") -> Dict[str, Any]:
    """Process Claude conversations that are Obsidian chats."""
    from .filters import create_claude_obsidian_filter
    
    # Custom rule for Claude obsidian chats
    source_rules = {
        'claude': {
            'llm_obsidian_chat': lambda conv: conv.conversation_id in obsidian_chat_ids
        }
    }
    
    config = ProcessingConfig(
        sources=['claude'],
        output_dir=output_dir,
        source_rules=source_rules,
        filter_criteria=create_claude_obsidian_filter(obsidian_chat_ids)
    )
    
    processor = BatchProcessor(config)
    return processor.process_all()
