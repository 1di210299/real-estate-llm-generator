from django.urls import path
from .views import ChatView, ConversationListView, ConversationDetailView

print("🔥 CHAT URLS LOADED - Available routes:")
print("  - /chat/ -> ChatView")
print("  - /chat/conversations/ -> ConversationListView")
print("  - /chat/conversations/<id>/ -> ConversationDetailView")

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<uuid:conversation_id>/', ConversationDetailView.as_view(), name='conversation-detail'),
]
