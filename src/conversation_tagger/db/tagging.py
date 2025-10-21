# conversation_tagger/db/tagging.py
"""
Database-backed tagging engine for incremental processing.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.tagger import ConversationTagger
from ..core.generate import generate_notes
from ..factory import create_default_tagger
from .manager import DatabaseManager
from .ingestion import DatabaseToObjectConverter
from .queries import ConversationQuery, QueryFilter
from .models import ConversationDB


class DatabaseTagger:
    """Database-backed conversation tagger with incremental processing."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.converter = DatabaseToObjectConverter(db_manager)
        self.query = ConversationQuery(db_manager)
        self.taggers = {}  # Cache taggers by source
    
    def get_tagger(self, source: str) -> ConversationTagger:
        """Get or create tagger for source."""
        if source not in self.taggers:
            self.taggers[source] = create_default_tagger(source)
        return self.taggers[source]
    
    def tag_unprocessed_conversations(self, source: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Tag all unprocessed conversations."""
        
        # Find unprocessed conversations
        filter = QueryFilter(unprocessed_only=True, source=source)
        conv_dbs = self.query.find_conversations(filter, limit=limit)
        
        stats = {
            'conversations_tagged': 0,
            'conversations_failed': 0,
            'total_annotations': 0,
            'sources_processed': set()
        }
        
        for conv_db in conv_dbs:
            try:
                result = self.tag_conversation(conv_db.conversation_id)
                if result['success']:
                    stats['conversations_tagged'] += 1
                    stats['total_annotations'] += result['annotation_count']
                    stats['sources_processed'].add(conv_db.source)
                else:
                    stats['conversations_failed'] += 1
                    
            except Exception as e:
                print(f"Failed to tag conversation {conv_db.conversation_id}: {e}")
                stats['conversations_failed'] += 1
        
        stats['sources_processed'] = list(stats['sources_processed'])
        return stats
    
    def tag_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Tag a single conversation and update database."""
        
        # Load conversation from database
        conversation = self.converter.load_conversation(conversation_id)
        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}
        
        # Get conversation metadata to determine source
        conv_db = self.db.get_conversation(conversation_id)
        if not conv_db:
            return {'success': False, 'error': 'Conversation metadata not found'}
        
        # Tag conversation
        tagger = self.get_tagger(conv_db.source)
        tagged_conversation = tagger.tag_conversation(conversation.raw or {})
        
        # Update database with new annotations
        self._update_conversation_annotations(tagged_conversation)
        
        # Mark as processed
        self.db.mark_conversation_processed(conversation_id)
        
        return {
            'success': True,
            'conversation_id': conversation_id,
            'annotation_count': len(tagged_conversation.annotations),
            'annotations': list(tagged_conversation.annotations.keys())
        }
    
    def retag_conversation(self, conversation_id: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Re-tag a conversation, optionally clearing existing annotations."""
        
        if clear_existing:
            # Clear existing annotations
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM annotations WHERE conversation_id = ?", (conversation_id,))
            self.db.connection.commit()
            
            # Mark as unprocessed
            cursor.execute(
                "UPDATE conversations SET processed_at = NULL WHERE conversation_id = ?", 
                (conversation_id,)
            )
            self.db.connection.commit()
        
        return self.tag_conversation(conversation_id)
    
    def _update_conversation_annotations(self, conversation) -> None:
        """Update conversation and exchange annotations in database."""
        
        # Clear existing annotations for this conversation
        cursor = self.db.connection.cursor()
        cursor.execute("DELETE FROM annotations WHERE conversation_id = ?", (conversation.conversation_id,))
        
        # Store conversation-level annotations
        for name, value in conversation.annotations.items():
            from .models import AnnotationDB
            annotation = AnnotationDB(
                conversation_id=conversation.conversation_id,
                exchange_id=None,
                annotation_name=name
            )
            annotation.set_value(value)
            self.db.upsert_annotation(annotation)
        
        # Store exchange-level annotations
        for exchange in conversation.exchanges:
            for name, value in exchange.annotations.items():
                annotation = AnnotationDB(
                    conversation_id=conversation.conversation_id,
                    exchange_id=exchange.exchange_id,
                    annotation_name=name
                )
                annotation.set_value(value)
                self.db.upsert_annotation(annotation)
        
        self.db.connection.commit()
    
    def generate_notes_for_conversations(self, 
                                       conversation_ids: List[str], 
                                       output_dir: str = "data/notes",
                                       template_name: str = 'article_body.md.jinja') -> Dict[str, Any]:
        """Generate Obsidian notes for specified conversations."""
        
        stats = {
            'notes_generated': 0,
            'notes_failed': 0,
            'conversations_processed': 0,
            'files_created': []
        }
        
        for conv_id in conversation_ids:
            try:
                # Load conversation
                conversation = self.converter.load_conversation(conv_id)
                if not conversation:
                    stats['notes_failed'] += 1
                    continue
                
                # Generate notes
                files = generate_notes(conversation, template_name, output_dir)
                stats['files_created'].extend(files)
                stats['notes_generated'] += len(files)
                stats['conversations_processed'] += 1
                
            except Exception as e:
                print(f"Failed to generate notes for {conv_id}: {e}")
                stats['notes_failed'] += 1
        
        return stats
    
    def generate_notes_for_query(self, 
                                query_filter: QueryFilter,
                                output_dir: str = "data/notes",
                                template_name: str = 'article_body.md.jinja',
                                limit: Optional[int] = None) -> Dict[str, Any]:
        """Generate notes for conversations matching query."""
        
        # Find matching conversations
        conv_dbs = self.query.find_conversations(query_filter, limit=limit)
        conversation_ids = [conv.conversation_id for conv in conv_dbs]
        
        # Generate notes
        return self.generate_notes_for_conversations(conversation_ids, output_dir, template_name)
    
    def get_tagging_stats(self, source: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about tagged conversations."""
        
        cursor = self.db.connection.cursor()
        
        # Base query
        base_query = "FROM conversations c"
        params = []
        where_clause = ""
        
        if source:
            where_clause = "WHERE c.source = ?"
            params.append(source)
        
        # Total conversations
        cursor.execute(f"SELECT COUNT(*) {base_query} {where_clause}", params)
        total_conversations = cursor.fetchone()[0]
        
        # Processed conversations
        processed_where = f"{where_clause} {'AND' if where_clause else 'WHERE'} c.processed_at IS NOT NULL"
        cursor.execute(f"SELECT COUNT(*) {base_query} {processed_where}", params)
        processed_conversations = cursor.fetchone()[0]
        
        # Annotation stats
        annotation_query = """
            SELECT 
                COUNT(DISTINCT a.conversation_id) as annotated_conversations,
                COUNT(*) as total_annotations,
                COUNT(DISTINCT a.annotation_name) as unique_annotation_types
            FROM annotations a
            JOIN conversations c ON a.conversation_id = c.conversation_id
        """
        
        if source:
            annotation_query += " WHERE c.source = ?"
        
        cursor.execute(annotation_query, params)
        annotation_stats = cursor.fetchone()
        
        return {
            'total_conversations': total_conversations,
            'processed_conversations': processed_conversations,
            'unprocessed_conversations': total_conversations - processed_conversations,
            'processing_percentage': round((processed_conversations / total_conversations * 100), 2) if total_conversations > 0 else 0,
            'annotated_conversations': annotation_stats[0] if annotation_stats[0] else 0,
            'total_annotations': annotation_stats[1] if annotation_stats[1] else 0,
            'unique_annotation_types': annotation_stats[2] if annotation_stats[2] else 0,
            'source': source
        }


class DatabaseBatchProcessor:
    """Database-backed batch processor for large-scale incremental conversation analysis."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.tagger = DatabaseTagger(db_manager)
        self.query = ConversationQuery(db_manager)
    
    def process_export_incrementally(self, 
                                   export_data: List[Dict[str, Any]], 
                                   source: str,
                                   auto_tag: bool = True,
                                   generate_notes: bool = False,
                                   output_dir: str = "data/notes") -> Dict[str, Any]:
        """Process export with full incremental pipeline."""
        
        from .ingestion import IncrementalIngester
        
        # Step 1: Incremental ingestion
        ingester = IncrementalIngester(self.db)
        ingestion_stats = ingester.ingest_from_export(export_data, source)
        
        results = {
            'ingestion': ingestion_stats,
            'tagging': {},
            'note_generation': {}
        }
        
        # Step 2: Auto-tag new/updated conversations
        if auto_tag and ingestion_stats['conversations_processed'] > 0:
            tagging_stats = self.tagger.tag_unprocessed_conversations(source)
            results['tagging'] = tagging_stats
        
        # Step 3: Generate notes for processed conversations
        if generate_notes and results.get('tagging', {}).get('conversations_tagged', 0) > 0:
            # Generate notes for recently processed conversations
            filter = QueryFilter(source=source, processed_only=True)
            note_stats = self.tagger.generate_notes_for_query(filter, output_dir, limit=100)
            results['note_generation'] = note_stats
        
        return results
