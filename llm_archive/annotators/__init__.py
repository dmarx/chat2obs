# llm_archive/annotators/__init__.py
"""Annotation infrastructure for entities.

Annotators analyze entities and produce annotations stored in derived.annotations.

Annotation Types:
- tag: For filtering (topic:physics, quality:high)
- title: For generation (wiki article titles)
- summary: Brief description
- feature: Detected features (has_code_blocks, has_latex)
- topic: Subject classification
- quality: Quality assessment

Creating Custom Annotators:
-------------------------
1. Subclass Annotator
2. Set ANNOTATION_TYPE, ENTITY_TYPE, SOURCE
3. Implement compute() method
4. Use add_annotation() to persist

Example:
    class MyAnnotator(Annotator):
        ANNOTATION_TYPE = 'custom'
        ENTITY_TYPE = 'exchange'
        SOURCE = 'heuristic'
        VERSION = '1.0'
        
        def compute(self) -> int:
            exchanges = self.session.query(Exchange).all()
            count = 0
            for ex in exchanges:
                if self._my_condition(ex):
                    if self.add_annotation(
                        entity_id=ex.id,
                        value='my_value',
                        key='optional_key',
                    ):
                        count += 1
            return count
"""

from llm_archive.annotators.base import Annotator, AnnotationManager
from llm_archive.annotators.features import (
    WikiLinkAnnotator,
    CodeBlockAnnotator,
    LatexAnnotator,
    ContinuationAnnotator,
)

__all__ = [
    "Annotator",
    "AnnotationManager",
    "WikiLinkAnnotator",
    "CodeBlockAnnotator",
    "LatexAnnotator",
    "ContinuationAnnotator",
]
