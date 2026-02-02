# llm_archive/annotators/chatgpt.py
"""ChatGPT-specific annotators based on platform features.

These annotators query ChatGPT-specific database tables to detect
platform features like:
- Web search (ChatGPTSearchGroup)
- Code execution (ChatGPTCodeExecution)
- Canvas operations (ChatGPTCanvasDoc)
- Custom GPT/Gizmo usage (ChatGPTMessageMeta)
- File attachments (Attachment)

These are the highest-priority detectors for their respective features
since they represent ground truth from the platform.
"""

from llm_archive.annotators.base import (
    ExchangePlatformAnnotator,
    ExchangePlatformData,
    AnnotationResult,
)


class ChatGPTWebSearchAnnotator(ExchangePlatformAnnotator):
    """Detect web search usage in ChatGPT exchanges.
    
    Queries ChatGPTSearchGroup table for evidence of web search.
    Highest priority detector for 'web_search' annotation key.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'web_search'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import ChatGPTSearchGroup
        
        # Check for search groups on any message in this exchange
        search_groups = (
            self.session.query(ChatGPTSearchGroup)
            .filter(ChatGPTSearchGroup.message_id.in_(data.message_ids))
            .all()
        )
        
        if search_groups:
            domains = list(set(g.domain for g in search_groups if g.domain))
            return [AnnotationResult(
                value='has_web_search',
                confidence=1.0,
                data={
                    'search_group_count': len(search_groups),
                    'domains': domains[:10],
                },
            )]
        return []


class ChatGPTCodeExecutionAnnotator(ExchangePlatformAnnotator):
    """Detect code execution (Jupyter/Python) in ChatGPT exchanges.
    
    Queries ChatGPTCodeExecution table for evidence of code execution.
    Highest priority detector for 'code' annotation key since it
    represents actual executed code.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'code'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import ChatGPTCodeExecution
        
        # Check for code executions on any message in this exchange
        executions = (
            self.session.query(ChatGPTCodeExecution)
            .filter(ChatGPTCodeExecution.message_id.in_(data.message_ids))
            .all()
        )
        
        if executions:
            successful = sum(1 for e in executions if e.status == 'success')
            failed = sum(1 for e in executions if e.exception_name)
            
            return [AnnotationResult(
                value='has_code_execution',
                confidence=1.0,
                data={
                    'execution_count': len(executions),
                    'successful': successful,
                    'failed': failed,
                },
            )]
        return []


class ChatGPTCanvasAnnotator(ExchangePlatformAnnotator):
    """Detect canvas/document operations in ChatGPT exchanges.
    
    Queries ChatGPTCanvasDoc table for evidence of canvas usage.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'canvas'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import ChatGPTCanvasDoc
        
        # Check for canvas docs on any message in this exchange
        canvas_docs = (
            self.session.query(ChatGPTCanvasDoc)
            .filter(ChatGPTCanvasDoc.message_id.in_(data.message_ids))
            .all()
        )
        
        if canvas_docs:
            doc_types = list(set(d.textdoc_type for d in canvas_docs if d.textdoc_type))
            
            return [AnnotationResult(
                value='has_canvas_operations',
                confidence=1.0,
                data={
                    'doc_count': len(canvas_docs),
                    'doc_types': doc_types,
                },
            )]
        return []


class ChatGPTGizmoAnnotator(ExchangePlatformAnnotator):
    """Detect Custom GPT/Gizmo usage in ChatGPT exchanges.
    
    Queries ChatGPTMessageMeta table for gizmo_id field.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'gizmo'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import ChatGPTMessageMeta
        
        # Check for gizmo usage on any message in this exchange
        gizmo_metas = (
            self.session.query(ChatGPTMessageMeta)
            .filter(ChatGPTMessageMeta.message_id.in_(data.message_ids))
            .filter(ChatGPTMessageMeta.gizmo_id.isnot(None))
            .all()
        )
        
        if gizmo_metas:
            gizmo_ids = list(set(m.gizmo_id for m in gizmo_metas))
            
            results = [AnnotationResult(
                value='has_gizmo_usage',
                confidence=1.0,
                data={
                    'gizmo_count': len(gizmo_ids),
                    'gizmo_ids': gizmo_ids,
                },
            )]
            
            # Also add individual gizmo annotations for filtering
            for gizmo_id in gizmo_ids:
                results.append(AnnotationResult(
                    value=gizmo_id,
                    key='gizmo_id',
                    confidence=1.0,
                ))
            
            return results
        return []


class ChatGPTAttachmentAnnotator(ExchangePlatformAnnotator):
    """Detect file attachments in ChatGPT user messages.
    
    Queries Attachment table for files uploaded by users.
    Also detects code-related file attachments.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'attachment'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    # Code-related file extensions
    CODE_EXTENSIONS = [
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs',
        '.jsx', '.tsx', '.sql', '.sh', '.rb', '.php', '.swift', '.kt',
    ]
    
    # Code-related MIME types
    CODE_MIMES = [
        'text/x-python', 'text/x-java', 'application/javascript',
        'text/x-script', 'text/x-c', 'text/x-c++',
    ]
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import Attachment
        
        # Check for attachments on user messages
        attachments = (
            self.session.query(Attachment)
            .filter(Attachment.message_id.in_(data.user_message_ids))
            .all()
        )
        
        if not attachments:
            return []
        
        results = []
        code_attachments = []
        
        for att in attachments:
            name = (att.file_name or '').lower()
            mime = (att.file_type or '').lower()
            
            is_code = (
                any(name.endswith(ext) for ext in self.CODE_EXTENSIONS) or
                any(m in mime for m in self.CODE_MIMES)
            )
            
            if is_code:
                code_attachments.append(name)
        
        # Basic attachment annotation
        results.append(AnnotationResult(
            value='has_attachments',
            confidence=1.0,
            data={
                'count': len(attachments),
                'file_types': list(set(a.file_type for a in attachments if a.file_type)),
            },
        ))
        
        # Code-specific attachment annotation (also contributes to 'code' key)
        if code_attachments:
            results.append(AnnotationResult(
                value='has_code_attachments',
                key='code',  # Contributes to code detection
                confidence=1.0,
                data={
                    'count': len(code_attachments),
                    'files': code_attachments[:10],
                },
            ))
        
        return results


class ChatGPTDalleAnnotator(ExchangePlatformAnnotator):
    """Detect DALL-E image generation in ChatGPT exchanges.
    
    Queries ChatGPTDalleGeneration table (via ContentPart) for
    evidence of image generation.
    """
    
    ANNOTATION_TYPE = 'feature'
    ANNOTATION_KEY = 'image_generation'
    PRIORITY = 100  # Platform feature = ground truth
    VERSION = '1.0'
    
    def annotate(self, data: ExchangePlatformData) -> list[AnnotationResult]:
        from llm_archive.models.raw import (
            ChatGPTDalleGeneration, ContentPart, Message
        )
        
        # Get content parts for messages in this exchange
        content_part_ids = (
            self.session.query(ContentPart.id)
            .filter(ContentPart.message_id.in_(data.message_ids))
            .subquery()
        )
        
        # Check for DALL-E generations
        generations = (
            self.session.query(ChatGPTDalleGeneration)
            .filter(ChatGPTDalleGeneration.content_part_id.in_(content_part_ids))
            .all()
        )
        
        if generations:
            return [AnnotationResult(
                value='has_dalle_generation',
                confidence=1.0,
                data={
                    'generation_count': len(generations),
                    'has_edits': any(g.edit_op for g in generations),
                },
            )]
        return []