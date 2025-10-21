# conversation_tagger/data/validation.py
"""
Schema validation machinery for conversation data formats.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

try:
    from genson import SchemaBuilder
    HAS_GENSON = True
except ImportError:
    HAS_GENSON = False
    logger.warning("genson not available - schema validation disabled")


# Schema seeds for different conversation formats
SEED_SCHEMA_CHATGPT = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'mapping': {
                'type': 'object',
                'patternProperties': {
                    # UUID pattern - GenSON will fill in the actual schema
                    r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$': None,
                    # Also handle the client-created-root pattern
                    r'^client-created-': None
                }
            }
        }
    }
}

SEED_SCHEMA_CLAUDE = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'uuid': {
                'type': 'string',
                'pattern': r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
            },
            'name': {
                'type': 'string'
            },
            'created_at': {
                'type': 'string',
                'format': 'date-time'
            },
            'updated_at': {
                'type': 'string',
                'format': 'date-time'
            },
            'account': {
                'type': 'object',
                'properties': {
                    'uuid': {
                        'type': 'string',
                        'pattern': r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
                    },
                    'name': {
                        'type': 'string'
                    }
                }
            }
        }
    }
}


class ConversationSchemaValidator:
    """Handles schema validation and generation for conversation data."""
    
    def __init__(self, dataset_type: str):
        """
        Initialize validator for a specific dataset type.
        
        Args:
            dataset_type: 'chatgpt'/'oai' or 'claude'
        """
        self.dataset_type = dataset_type.lower()
        if self.dataset_type in ['chatgpt', 'oai']:
            self.seed_schema = SEED_SCHEMA_CHATGPT
        elif self.dataset_type == 'claude':
            self.seed_schema = SEED_SCHEMA_CLAUDE
        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
        
        self.builder = None
        if HAS_GENSON:
            self.builder = SchemaBuilder()
            self.builder.add_schema(self.seed_schema)
    
    def validate_conversations(self, conversations: List[Dict[str, Any]]) -> bool:
        """
        Validate conversation data against expected schema.
        
        Args:
            conversations: List of conversation dictionaries
            
        Returns:
            True if validation passes
        """
        if not HAS_GENSON:
            logger.warning("genson not available - skipping schema validation")
            return True
        
        try:
            # Add the actual data to the schema builder
            self.builder.add_object(conversations)
            
            # Generate the complete schema
            schema = self.builder.to_schema()
            
            logger.info(f"Schema validation passed for {len(conversations)} conversations")
            return True
            
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
    
    def get_schema(self) -> Optional[Dict[str, Any]]:
        """
        Get the generated schema.
        
        Returns:
            Schema dictionary or None if genson not available
        """
        if not HAS_GENSON or not self.builder:
            return None
        
        return self.builder.to_schema()
    
    def save_schema(self, output_path: str) -> bool:
        """
        Save the generated schema to a file.
        
        Args:
            output_path: Path to save schema JSON file
            
        Returns:
            True if saved successfully
        """
        schema = self.get_schema()
        if not schema:
            logger.warning("No schema available to save")
            return False
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2)
            
            logger.info(f"Schema saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save schema: {e}")
            return False


def validate_and_generate_schema(conversations: List[Dict[str, Any]], 
                               dataset_type: str,
                               output_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Convenience function to validate conversations and optionally save schema.
    
    Args:
        conversations: List of conversation dictionaries
        dataset_type: 'chatgpt'/'oai' or 'claude'
        output_path: Optional path to save generated schema
        
    Returns:
        Generated schema dictionary or None
    """
    validator = ConversationSchemaValidator(dataset_type)
    
    if not validator.validate_conversations(conversations):
        logger.error("Schema validation failed")
        return None
    
    schema = validator.get_schema()
    
    if output_path and schema:
        validator.save_schema(output_path)
    
    return schema
