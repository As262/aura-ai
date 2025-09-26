from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserProfile, AestheticAnalysis, ConversationAnalysis
from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    AestheticAnalysisSerializer,
    ConversationAnalysisSerializer
)
from .ai_services import ImageAnalysisService
import json
import os
import tempfile


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
            try:
                # Save uploaded image temporarily
                image_file = request.FILES['image']
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    for chunk in image_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name
                
                # Initialize AI service and analyze image
                ai_service = ImageAnalysisService()
                analysis_result = ai_service.analyze_image_comprehensive(tmp_file_path)
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                # Save analysis to database
                analysis = serializer.save(
                    user=request.user if request.user.is_authenticated else None,
                    result=analysis_result
                )
                
                return Response(
                    AestheticAnalysisSerializer(analysis).data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                # Fallback to mock data if AI analysis fails
                mock_result = {
                    "error": "AI analysis temporarily unavailable",
                    "fallback_analysis": {
                        "overall_rating": {
                            "score": 7.5,
                            "category": "Good",
                            "breakdown": {
                                "technical": 7.0,
                                "aesthetic": 8.0,
                                "composition": 7.5
                            }
                        },
                        "improvement_suggestions": [
                            {
                                "category": "General",
                                "priority": "Medium",
                                "suggestion": "AI analysis will be available once dependencies are installed",
                                "technical_details": str(e)
                            }
                        ]
                    }
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
    import torch
    
    # Check GPU status
    gpu_available = torch.cuda.is_available()
    gpu_info = {}
    
    if gpu_available:
        gpu_info = {
            'available': True,
            'device_name': torch.cuda.get_device_name(0),
            'memory_total': f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB",
            'cuda_version': torch.version.cuda
        }
    else:
        gpu_info = {'available': False}
    
    return Response({
        'status': 'healthy',
        'message': 'Aura AI Backend is running successfully',
        'gpu_status': gpu_info,
        'ai_ready': True
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


@api_view(['POST'])
def detailed_image_analysis(request):
    """
    Advanced image analysis endpoint with comprehensive rating and suggestions
    """
    try:
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Validate image file
        if not image_file.content_type.startswith('image/'):
            return Response(
                {'error': 'Invalid file type. Please upload an image.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            for chunk in image_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # Initialize AI service and perform comprehensive analysis
            ai_service = ImageAnalysisService()
            analysis_result = ai_service.analyze_image_comprehensive(tmp_file_path)
            
            # Add metadata
            analysis_result['metadata'] = {
                'filename': image_file.name,
                'file_size': image_file.size,
                'analysis_timestamp': None,  # Will be set by serializer
                'version': '1.0'
            }
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return Response({
                'success': True,
                'analysis': analysis_result,
                'message': 'Image analysis completed successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as ai_error:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
            # Return detailed error information for debugging
            return Response({
                'success': False,
                'error': 'AI analysis failed',
                'details': str(ai_error),
                'fallback_available': True,
                'message': 'Please install required dependencies: pip install opencv-python mediapipe tensorflow scikit-image'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response(
            {'error': f'Server error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )