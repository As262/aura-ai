from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile, AestheticAnalysis, ConversationAnalysis
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    AestheticAnalysisSerializer,
    ConversationAnalysisSerializer
)
import json


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class AestheticAnalysisView(generics.CreateAPIView):
    serializer_class = AestheticAnalysisSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Mock aesthetic analysis - replace with actual AI analysis
            mock_result = {
                "aesthetic_score": 7.5,
                "dominant_colors": ["#3498db", "#2ecc71", "#e74c3c"],
                "composition": {
                    "rule_of_thirds": True,
                    "symmetry": False,
                    "balance": "good"
                },
                "emotions": ["joy", "calm", "energetic"],
                "style": "modern",
                "recommendations": [
                    "Consider adjusting brightness slightly",
                    "The color palette works well",
                    "Good composition overall"
                ]
            }
            
            analysis = serializer.save(
                user=request.user if request.user.is_authenticated else None,
                result=mock_result
            )
            return Response(
                AestheticAnalysisSerializer(analysis).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationAnalysisView(generics.CreateAPIView):
    serializer_class = ConversationAnalysisSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Mock conversation analysis - replace with actual AI analysis
            conversation_text = serializer.validated_data['conversation_text']
            
            mock_analysis = {
                "sentiment": "positive",
                "confidence": 0.85,
                "key_topics": ["technology", "future", "innovation"],
                "emotion_breakdown": {
                    "joy": 0.4,
                    "excitement": 0.3,
                    "neutral": 0.2,
                    "concern": 0.1
                },
                "communication_style": "enthusiastic",
                "suggestions": [
                    "Great use of positive language",
                    "Consider more specific examples",
                    "Maintain the enthusiastic tone"
                ],
                "word_count": len(conversation_text.split()),
                "readability_score": 7.2
            }
            
            analysis = serializer.save(
                user=request.user if request.user.is_authenticated else None,
                analysis_result=mock_analysis
            )
            return Response(
                ConversationAnalysisSerializer(analysis).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'Aura AI Backend is running successfully'
    })


@api_view(['POST'])
def register_user(request):
    try:
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        UserProfile.objects.create(user=user)
        
        return Response(
            {'message': 'User created successfully'}, 
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def login_user(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )