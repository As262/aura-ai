from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, AestheticAnalysis, ConversationAnalysis


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'created_at', 'updated_at']


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