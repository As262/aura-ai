from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('aesthetic-analysis/', views.AestheticAnalysisView.as_view(), name='aesthetic_analysis'),
    path('conversation-analysis/', views.ConversationAnalysisView.as_view(), name='conversation_analysis'),
]