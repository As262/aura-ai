from rest_framework import serializers
from .models import AestheticAnalysis, ConversationAnalysis


class AestheticAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AestheticAnalysis
        fields = ['id', 'image', 'result', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConversationAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationAnalysis
        fields = ['id', 'conversation_text', 'analysis_result', 'created_at']
        read_only_fields = ['id', 'created_at', 'analysis_result']