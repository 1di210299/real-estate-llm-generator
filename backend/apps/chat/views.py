"""
Views for Chat API with RAG.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from core.llm.rag import RAGPipeline, RAGError
from apps.conversations.models import Conversation, Message

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    Main chat endpoint with RAG.
    
    POST /chat
    {
        "message": "What's the ROI for Villa Mar?",
        "conversation_id": "uuid" (optional),
        "stream": false (optional)
    }
    """
    
    # Temporarily allow access without authentication for testing
    # permission_classes = [IsAuthenticated]
    permission_classes = []
    
    def post(self, request):
        """Process chat message with RAG."""
        
        # DEBUG LOGS
        print(f"🎯 ChatView POST - Path: {request.path}")
        print(f"🎯 ChatView POST - Full Path: {request.get_full_path()}")
        print(f"🎯 ChatView POST - Headers: {dict(request.headers)}")
        print(f"🎯 ChatView POST - Data: {request.data}")
        logger.info(f"Chat request received: path={request.path}, data={request.data}")
        
        message_text = request.data.get('message')
        conversation_id = request.data.get('conversation_id')
        stream = request.data.get('stream', False)
        
        if not message_text:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # For testing without auth, use first available tenant/user
            if request.user and request.user.is_authenticated:
                user = request.user
                tenant = request.user.tenant
                user_role = request.user.role
            else:
                # Anonymous access for testing
                from apps.tenants.models import Tenant
                from apps.users.models import CustomUser
                
                tenant = Tenant.objects.first()
                user = CustomUser.objects.filter(tenant=tenant).first()
                user_role = 'client' if user else 'client'
                
                if not tenant:
                    return Response(
                        {'error': 'No tenant configured. Please run migrations and create test data.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            # Get or create conversation
            if conversation_id:
                try:
                    conversation = Conversation.objects.get(
                        id=conversation_id,
                        tenant=tenant
                    )
                except Conversation.DoesNotExist:
                    return Response(
                        {'error': 'Conversation not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new conversation
                # Generate title from first message
                title = message_text[:100] + ('...' if len(message_text) > 100 else '')
                
                conversation = Conversation.objects.create(
                    tenant=tenant,
                    user=user if user else None,
                    user_role=user_role,
                    title=title
                )
                logger.info(f"Created new conversation: {conversation.id}")
            
            # Save user message
            user_message = Message.objects.create(
                conversation=conversation,
                role=Message.Role.USER,
                content=message_text
            )
            
            # Initialize RAG pipeline
            rag = RAGPipeline(
                tenant_id=str(tenant.id),
                user_role=user_role
            )
            
            # Query RAG
            username = user.username if user else 'anonymous'
            logger.info(f"Processing query for user {username}")
            result = rag.query(
                query=message_text,
                conversation=conversation,
                stream=stream
            )
            
            # Save assistant message
            assistant_message = Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=result['response'],
                model_used=result.get('model', 'unknown'),
                tokens_input=result.get('tokens_used', 0) // 2,  # Rough estimate
                tokens_output=result.get('tokens_used', 0) // 2,
                retrieved_documents=result.get('sources', []),
                latency_ms=result.get('latency_ms')
            )
            
            # Update conversation costs
            conversation.update_costs()
            
            # Format sources for response
            sources = []
            for doc in result.get('sources', [])[:5]:  # Top 5 sources
                sources.append({
                    'document_id': doc['id'],
                    'content_type': doc['content_type'],
                    'excerpt': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                    'relevance_score': round(doc['relevance_score'], 3),
                    'source_reference': doc.get('source_reference', 'N/A'),
                    'updated_at': doc['freshness_date'],
                    'metadata': doc.get('metadata', {})
                })
            
            return Response({
                'conversation_id': str(conversation.id),
                'message_id': str(assistant_message.id),
                'response': result['response'],
                'sources': sources,
                'model': result.get('model'),
                'latency_ms': result.get('latency_ms'),
                'cached': result.get('cached', False),
                'tokens_used': result.get('tokens_used', 0)
            }, status=status.HTTP_200_OK)
            
        except RAGError as e:
            logger.error(f"RAG error: {e}")
            return Response(
                {'error': f'RAG processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationListView(APIView):
    """
    List user's conversations.
    
    GET /chat/conversations
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's conversations."""
        
        conversations = Conversation.objects.filter(
            user=request.user,
            tenant=request.user.tenant,
            is_archived=False
        ).order_by('-updated_at')[:50]
        
        results = []
        for conv in conversations:
            results.append({
                'id': str(conv.id),
                'title': conv.title,
                'user_role': conv.user_role,
                'message_count': conv.get_message_count(),
                'total_tokens': conv.total_tokens,
                'total_cost_usd': float(conv.total_cost_usd),
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat()
            })
        
        return Response({
            'conversations': results,
            'count': len(results)
        }, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """
    Get conversation with messages.
    
    GET /chat/conversations/{id}
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, conversation_id):
        """Get conversation details."""
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=request.user,
                tenant=request.user.tenant
            )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get messages
        messages = conversation.messages.order_by('created_at')
        
        message_list = []
        for msg in messages:
            message_list.append({
                'id': str(msg.id),
                'role': msg.role,
                'content': msg.content,
                'model_used': msg.model_used,
                'tokens_input': msg.tokens_input,
                'tokens_output': msg.tokens_output,
                'sources': msg.get_sources() if msg.role == Message.Role.ASSISTANT else [],
                'created_at': msg.created_at.isoformat()
            })
        
        return Response({
            'id': str(conversation.id),
            'title': conversation.title,
            'user_role': conversation.user_role,
            'total_tokens': conversation.total_tokens,
            'total_cost_usd': float(conversation.total_cost_usd),
            'messages': message_list,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat()
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, conversation_id):
        """Archive conversation."""
        
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                user=request.user,
                tenant=request.user.tenant
            )
            conversation.is_archived = True
            conversation.save(update_fields=['is_archived'])
            
            return Response({
                'status': 'success',
                'message': 'Conversation archived'
            }, status=status.HTTP_200_OK)
            
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
