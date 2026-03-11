from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('usage-status/', views.usage_status, name='usage_status'),
    path('usage-increment/', views.usage_increment, name='usage_increment'),
    path('reset-usage/', views.reset_usage, name='reset_usage'),
    path('aesthetic-analysis/', views.AestheticAnalysisView.as_view(), name='aesthetic_analysis'),
    path('social-media-analysis/', views.SocialMediaAnalysisView.as_view(), name='social_media_analysis'),
    path('conversation-analysis/', views.ConversationAnalysisView.as_view(), name='conversation_analysis'),
    path('detailed-image-analysis/', views.detailed_image_analysis, name='detailed_image_analysis'),
]