# conversation_tagger/db/queries.py
"""
Query interface for efficient database-based conversation analysis.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from .manager import DatabaseManager
from .models import ConversationDB, AnnotationDB


@dataclass
class QueryFilter:
    """Filter for conversation queries."""
    
    # Annotation filters
    has_annotation: Optional[str] = None
    annotation_equals: Optional[Dict[str, Any]] = None
    annotation_contains: Optional[Dict[str, str]] = None
    
    # Metadata filters
    source: Optional[str] = None
    min_exchanges: Optional[int] = None
    max_exchanges: Optional[int] = None
    min_messages: Optional[int] = None
    max_messages: Optional[int] = None
    
    # Time filters
    after_date: Optional[float] = None
    before_date: Optional[float] = None
    
    # Processing status
    processed_only: bool = False
    unprocessed_only: bool = False


class ConversationQuery:
    """Efficient query interface for conversations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def find_conversations(self, filter: QueryFilter, limit: Optional[int] = None) -> List[ConversationDB]:
        """Find conversations matching the filter criteria."""
        
        # Build SQL query dynamically
        query_parts = ["SELECT DISTINCT c.* FROM conversations c"]
        params = []
        conditions = []
        
        # Join with annotations if needed
        if (filter.has_annotation or filter.annotation_equals or filter.annotation_contains):
            query_parts.append("LEFT JOIN annotations a ON c.conversation_id = a.conversation_id")
        
        # Add WHERE conditions
        if filter.source:
            conditions.append("c.source = ?")
            params.append(filter.source)
        
        if filter.min_exchanges:
            conditions.append("c.exchange_count >= ?")
            params.append(filter.min_exchanges)
        
        if filter.max_exchanges:
            conditions.append("c.exchange_count <= ?")
            params.append(filter.max_exchanges)
        
        if filter.min_messages:
            conditions.append("c.total_message_count >= ?")
            params.append(filter.min_messages)
        
        if filter.max_messages:
            conditions.append("c.total_message_count <= ?")
            params.append(filter.max_messages)
        
        if filter.after_date:
            conditions.append("c.last_message_time >= ?")
            params.append(filter.after_date)
        
        if filter.before_date:
            conditions.append("c.last_message_time <= ?")
            params.append(filter.before_date)
        
        if filter.processed_only:
            conditions.append("c.processed_at IS NOT NULL")
        
        if filter.unprocessed_only:
            conditions.append("c.processed_at IS NULL")
        
        # Annotation filters
        if filter.has_annotation:
            conditions.append("a.annotation_name = ?")
            params.append(filter.has_annotation)
        
        if filter.annotation_equals:
            annotation_conditions = []
            for name, value in filter.annotation_equals.items():
                if isinstance(value, bool):
                    annotation_conditions.append("(a.annotation_name = ? AND a.boolean_value = ?)")
                    params.extend([name, value])
                elif isinstance(value, (int, float)):
                    annotation_conditions.append("(a.annotation_name = ? AND a.number_value = ?)")
                    params.extend([name, float(value)])
                elif isinstance(value, str):
                    annotation_conditions.append("(a.annotation_name = ? AND a.string_value = ?)")
                    params.extend([name, value])
            
            if annotation_conditions:
                conditions.append(f"({' OR '.join(annotation_conditions)})")
        
        if filter.annotation_contains:
            for name, value in filter.annotation_contains.items():
                conditions.append("(a.annotation_name = ? AND a.string_value LIKE ?)")
                params.extend([name, f"%{value}%"])
        
        # Combine query parts
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        
        query_parts.append("ORDER BY c.last_message_time DESC")
        
        if limit:
            query_parts.append("LIMIT ?")
            params.append(limit)
        
        query = " ".join(query_parts)
        
        # Execute query
        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append(ConversationDB(
                conversation_id=row['conversation_id'],
                source=row['source'],
                title=row['title'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                last_updated=row['last_updated'],
                processed_at=row['processed_at'],
                exchange_count=row['exchange_count'],
                total_message_count=row['total_message_count'],
                total_user_messages=row['total_user_messages'],
                total_assistant_messages=row['total_assistant_messages'],
                raw_data=row['raw_data'],
                annotations=row['annotations']
            ))
        
        return conversations
    
    def get_annotation_stats(self, annotation_name: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a specific annotation."""
        
        query = """
            SELECT 
                annotation_type,
                COUNT(*) as count,
                COUNT(DISTINCT conversation_id) as unique_conversations
            FROM annotations a
            JOIN conversations c ON a.conversation_id = c.conversation_id
            WHERE a.annotation_name = ?
        """
        params = [annotation_name]
        
        if source:
            query += " AND c.source = ?"
            params.append(source)
        
        query += " GROUP BY annotation_type"
        
        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        
        stats = {
            'annotation_name': annotation_name,
            'total_annotations': 0,
            'unique_conversations': 0,
            'types': {}
        }
        
        for row in cursor.fetchall():
            stats['types'][row['annotation_type']] = {
                'count': row['count'],
                'unique_conversations': row['unique_conversations']
            }
            stats['total_annotations'] += row['count']
            stats['unique_conversations'] = max(stats['unique_conversations'], row['unique_conversations'])
        
        return stats
    
    def get_top_annotations(self, limit: int = 20, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get most common annotations."""
        
        query = """
            SELECT 
                a.annotation_name,
                COUNT(*) as count,
                COUNT(DISTINCT a.conversation_id) as unique_conversations,
                ROUND(COUNT(DISTINCT a.conversation_id) * 100.0 / 
                      (SELECT COUNT(DISTINCT conversation_id) FROM conversations WHERE source = COALESCE(?, source)), 2) as percentage
            FROM annotations a
            JOIN conversations c ON a.conversation_id = c.conversation_id
        """
        params = []
        
        if source:
            query += " WHERE c.source = ?"
            params.append(source)
        
        query += """
            GROUP BY a.annotation_name
            ORDER BY unique_conversations DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        
        annotations = []
        for row in cursor.fetchall():
            annotations.append({
                'name': row['annotation_name'],
                'count': row['count'],
                'unique_conversations': row['unique_conversations'],
                'percentage': row['percentage']
            })
        
        return annotations
    
    def facet_conversations(self, 
                          annotation_name: str, 
                          facet_attribute: Optional[str] = None,
                          source: Optional[str] = None,
                          limit: int = 50) -> Dict[str, List[ConversationDB]]:
        """Group conversations by annotation facets."""
        
        # Get all values for the annotation
        if facet_attribute:
            # For structured annotations, extract the specific attribute
            query = """
                SELECT DISTINCT 
                    JSON_EXTRACT(a.annotation_value, '$.' || ?) as facet_value,
                    c.*
                FROM annotations a
                JOIN conversations c ON a.conversation_id = c.conversation_id
                WHERE a.annotation_name = ?
            """
            params = [facet_attribute, annotation_name]
        else:
            # For simple annotations, use the value directly
            query = """
                SELECT DISTINCT
                    COALESCE(a.string_value, CAST(a.number_value AS TEXT), CAST(a.boolean_value AS TEXT)) as facet_value,
                    c.*
                FROM annotations a
                JOIN conversations c ON a.conversation_id = c.conversation_id
                WHERE a.annotation_name = ?
            """
            params = [annotation_name]
        
        if source:
            query += " AND c.source = ?"
            params.append(source)
        
        query += " ORDER BY c.last_message_time DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.db.connection.cursor()
        cursor.execute(query, params)
        
        facets = {}
        for row in cursor.fetchall():
            facet_value = row['facet_value'] or '<none>'
            
            if facet_value not in facets:
                facets[facet_value] = []
            
            facets[facet_value].append(ConversationDB(
                conversation_id=row['conversation_id'],
                source=row['source'],
                title=row['title'],
                first_message_time=row['first_message_time'],
                last_message_time=row['last_message_time'],
                last_updated=row['last_updated'],
                processed_at=row['processed_at'],
                exchange_count=row['exchange_count'],
                total_message_count=row['total_message_count'],
                total_user_messages=row['total_user_messages'],  
                total_assistant_messages=row['total_assistant_messages'],
                raw_data=row['raw_data'],
                annotations=row['annotations']
            ))
        
        return facets
