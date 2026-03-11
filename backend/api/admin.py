from django.contrib import admin
from .models import AestheticAnalysis, ConversationAnalysis


@admin.register(AestheticAnalysis)
class AestheticAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(ConversationAnalysis)
class ConversationAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    list_filter = ['created_at']
    search_fields = ['conversation_text']
    readonly_fields = ['created_at']