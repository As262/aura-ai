from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import AestheticAnalysis, ConversationAnalysis
from .serializers import (
    AestheticAnalysisSerializer,
    ConversationAnalysisSerializer
)
from .ai_services_optimized import OptimizedImageAnalysisService as ImageAnalysisService
from .conversation_decoder import ConversationDecoder
from ml_models.conversation_interest_model import ConversationAnalysisService
import json
import os
import tempfile
import uuid
import time
import json as _json
from django.utils import timezone
from django.conf import settings
from .models import IPUsage
import threading


class AestheticAnalysisView(generics.CreateAPIView):
    serializer_class = AestheticAnalysisSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def create(self, request, *args, **kwargs):
        # Check usage limit before processing
        req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
        can_use, current_usage = _check_usage_limit(req_ip)
        
        if not can_use:
            return Response({
                'error': 'Usage limit exceeded',
                'message': f'You have reached the limit of {_USAGE_LIMIT} analyses. Current usage: {current_usage}',
                'usage_limit_exceeded': True,
                'current_usage': current_usage,
                'limit': _USAGE_LIMIT
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
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
                    result=analysis_result
                )

                # Record usage for this IP
                try:
                    req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
                    _increment_usage_for_ip(req_ip)
                except Exception:
                    pass
                
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
                    result=mock_result
                )

                # Record usage even for fallback
                try:
                    req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
                    _increment_usage_for_ip(req_ip)
                except Exception:
                    pass
                
                return Response(
                    AestheticAnalysisSerializer(analysis).data,
                    status=status.HTTP_201_CREATED
                )
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConversationAnalysisView(APIView):
    """
    Multi-format conversation analysis endpoint
    Supports: PDF, TXT, JSON, CSV, LOG files
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def _basic_conversation_analysis(self, messages, user_identifier=None):
        """
        Fallback basic conversation analysis when ML model is unavailable
        """
        # Identify participants
        senders = {}
        for msg in messages:
            sender = msg['sender']
            senders[sender] = senders.get(sender, 0) + 1
        
        top_senders = sorted(senders.items(), key=lambda x: x[1], reverse=True)[:2]
        
        if len(top_senders) < 2:
            return {
                'error': 'Need at least 2 participants',
                'participants_found': len(top_senders)
            }
        
        user = user_identifier if user_identifier else top_senders[0][0]
        other = next((s for s, _ in top_senders if s != user), top_senders[1][0])
        
        your_messages = [msg for msg in messages if msg['sender'] == user]
        their_messages = [msg for msg in messages if msg['sender'] == other]
        
        # Calculate basic metrics
        your_avg_len = sum(len(m['message'].split()) for m in your_messages) / max(len(your_messages), 1)
        their_avg_len = sum(len(m['message'].split()) for m in their_messages) / max(len(their_messages), 1)
        
        your_questions = sum(1 for m in your_messages if '?' in m['message'])
        their_questions = sum(1 for m in their_messages if '?' in m['message'])
        
        # Estimate interest level based on simple heuristics
        interest_score = 50.0  # Start at moderate
        
        # Longer responses = more interest
        if their_avg_len > your_avg_len * 0.8:
            interest_score += 15
        
        # Questions back = more interest
        if their_questions > 0:
            interest_score += 15
        
        # Check for positive indicators
        positive_count = sum(
            1 for m in their_messages 
            if any(word in m['message'].lower() for word in ['haha', 'lol', '😂', '😊', '!'])
        )
        if positive_count > len(their_messages) * 0.3:
            interest_score += 20
        
        interest_score = min(max(interest_score, 0), 100)
        
        # Map to interest level
        if interest_score >= 80:
            interest_level = "Very High"
        elif interest_score >= 65:
            interest_level = "High"
        elif interest_score >= 45:
            interest_level = "Moderate"
        elif interest_score >= 25:
            interest_level = "Low"
        else:
            interest_level = "Very Low"
        
        # Generate 2-3 personalized suggestions based on basic analysis
        suggestions = []
        
        # Suggestion 1: Based on question asking
        if your_questions < len(your_messages) * 0.2:
            suggestions.append({
                'category': 'Curiosity & Questions',
                'priority': 'High',
                'suggestion': 'You\'re not asking many questions. Show more interest by asking about their day, opinions, and experiences.',
                'tip': 'Use the 5 W\'s: Who, What, When, Where, Why (and How!) to keep conversations dynamic.'
            })
        else:
            suggestions.append({
                'category': 'Questions',
                'priority': 'Info',
                'suggestion': 'Good job asking questions! This shows genuine interest and keeps conversations flowing.',
                'tip': 'Continue asking open-ended questions that invite detailed responses.'
            })
        
        # Suggestion 2: Based on message length balance
        if your_avg_len > their_avg_len * 2:
            suggestions.append({
                'category': 'Message Length',
                'priority': 'Medium',
                'suggestion': 'Your messages are significantly longer than theirs. Try being more concise and giving them space to contribute.',
                'tip': 'Break long messages into smaller parts and pause to let them respond.'
            })
        elif your_avg_len < their_avg_len * 0.5:
            suggestions.append({
                'category': 'Message Length',
                'priority': 'Medium',
                'suggestion': 'Your messages are quite short. Try elaborating more to show you\'re invested in the conversation.',
                'tip': 'Add your thoughts, feelings, or follow-up questions to make responses more engaging.'
            })
        else:
            suggestions.append({
                'category': 'Balance',
                'priority': 'Info',
                'suggestion': 'Great message length balance! You\'re matching their communication style well.',
                'tip': 'Keep maintaining this natural back-and-forth rhythm.'
            })
        
        # Suggestion 3: Based on engagement indicators
        if positive_count > len(their_messages) * 0.3:
            suggestions.append({
                'category': 'Positive Signs',
                'priority': 'Info',
                'suggestion': 'Great news! They\'re using lots of positive language, which shows they enjoy talking to you.',
                'tip': 'Keep doing what you\'re doing and continue building on shared interests.'
            })
        else:
            suggestions.append({
                'category': 'Engagement',
                'priority': 'Medium',
                'suggestion': 'Try to create more fun and engaging moments in your conversations.',
                'tip': 'Share interesting stories, use humor appropriately, and show enthusiasm about their interests.'
            })
        
        return {
            'overall_interest_level': interest_level,
            'interest_percentage': round(interest_score, 2),
            'total_messages': len(messages),
            'your_messages': len(your_messages),
            'their_messages': len(their_messages),
            'engagement_metrics': {
                'your_avg_message_length': round(your_avg_len, 2),
                'their_avg_message_length': round(their_avg_len, 2),
                'response_length_ratio': round(their_avg_len / max(your_avg_len, 1), 2),
                'your_questions_asked': your_questions,
                'their_questions_asked': their_questions,
                'their_positive_reactions': positive_count,
                'engagement_balance': round(min(their_avg_len / max(your_avg_len, 1), 
                                               your_avg_len / max(their_avg_len, 1)), 2)
            },
            'improvement_suggestions': suggestions,
            'participants': {
                'you': user,
                'other_person': other
            },
            'analysis_mode': 'basic_fallback'
        }
    
    def post(self, request):
        # Check usage limit before processing
        req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
        can_use, current_usage = _check_usage_limit(req_ip)
        
        if not can_use:
            return Response({
                'error': 'Usage limit exceeded',
                'message': f'You have reached the limit of {_USAGE_LIMIT} analyses. Current usage: {current_usage}',
                'usage_limit_exceeded': True,
                'current_usage': current_usage,
                'limit': _USAGE_LIMIT
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        print("🗨️ Conversation Analysis API called")
        print(f"📄 Request files: {list(request.FILES.keys())}")
        print(f"📄 Request data: {list(request.data.keys())}")
        
        try:
            # Check if file is provided
            if 'file' not in request.FILES:
                return Response({
                    'error': 'No file provided',
                    'message': 'Please upload a conversation file (.txt, .json, .csv, .log, .pdf)',
                    'supported_formats': ['txt', 'json', 'csv', 'log', 'pdf']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            uploaded_file = request.FILES['file']
            platform = request.data.get('platform', 'instagram')  # Default platform
            user_identifier = request.data.get('user_identifier', None)  # Optional user ID
            
            print(f"📁 File: {uploaded_file.name}")
            print(f"📱 Platform: {platform}")
            
            # Get file extension
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Validate file type
            supported_formats = ['txt', 'json', 'csv', 'log', 'pdf']
            if file_extension not in supported_formats:
                return Response({
                    'error': 'Unsupported file format',
                    'message': f'Please upload one of: {", ".join(supported_formats)}',
                    'uploaded_format': file_extension
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Phase 1: Decode conversation file
                print("🔍 Phase 1: Decoding conversation file...")
                decoder = ConversationDecoder()
                decoded_data = decoder.decode_file(temp_file_path, file_extension)
                
                messages = decoded_data['messages']
                metadata = decoded_data['metadata']
                
                print(f"✅ Decoded {len(messages)} messages")
                
                if len(messages) < 2:
                    return Response({
                        'error': 'Not enough messages',
                        'message': 'Need at least 2 messages for analysis',
                        'messages_found': len(messages)
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Phase 2: ML-based interest analysis
                print("🤖 Phase 2: Running ML analysis...")
                
                try:
                    # Load ML model
                    model_path = os.path.join(
                        os.path.dirname(__file__),
                        '..',
                        'ml_models',
                        'trained',
                        'conversation_interest_model_best.pth'
                    )
                    
                    # If model doesn't exist, use untrained model
                    if not os.path.exists(model_path):
                        print(f"⚠️ Trained model not found at {model_path}, using untrained model")
                        model_path = None
                    
                    analysis_service = ConversationAnalysisService(model_path)
                    analysis_result = analysis_service.analyze_conversation(
                        messages,
                        user_identifier=user_identifier
                    )
                except Exception as ml_error:
                    print(f"⚠️ ML analysis failed: {ml_error}")
                    print("🔄 Falling back to basic analysis...")
                    
                    # Fallback to basic analysis if ML fails
                    analysis_result = self._basic_conversation_analysis(messages, user_identifier)
                
                print(f"✅ Analysis complete!")
                print(f"   Interest Level: {analysis_result.get('overall_interest_level', 'N/A')}")
                print(f"   Interest %: {analysis_result.get('interest_percentage', 'N/A')}%")
                
                # Combine metadata
                analysis_result['file_metadata'] = {
                    'filename': uploaded_file.name,
                    'format': file_extension,
                    'platform': platform,
                    'total_messages_decoded': len(messages),
                    **metadata
                }
                
                # Add sample messages
                analysis_result['sample_messages'] = messages[:5]  # First 5 messages
                
                # Phase 3: Save to database
                print("💾 Phase 3: Saving analysis...")
                
                # Convert messages to text for storage
                conversation_text = "\n".join([
                    f"{msg.get('sender', 'Unknown')}: {msg.get('message', '')}"
                    for msg in messages[:100]  # Store first 100 messages
                ])
                
                conversation_analysis = ConversationAnalysis.objects.create(
                    conversation_text=conversation_text,
                    analysis_result=analysis_result
                )
                
                # Increment usage
                try:
                    _increment_usage_for_ip(req_ip)
                except Exception:
                    pass
                
                print("✅ All phases complete!")
                
                return Response({
                    'success': True,
                    'analysis': analysis_result,
                    'message': 'Conversation analysis completed successfully',
                    'analysis_id': conversation_analysis.id
                }, status=status.HTTP_201_CREATED)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"❌ Conversation analysis error: {str(e)}")
            import traceback
            error_traceback = traceback.format_exc()
            print(error_traceback)
            
            # Provide more specific error messages
            error_message = str(e)
            error_details = 'Please ensure the file is properly formatted'
            
            # Check for specific error types
            if 'module' in error_message.lower() or 'import' in error_message.lower():
                error_details = 'AI model dependencies not installed. Please run: pip install torch torchvision scikit-learn'
            elif 'model' in error_message.lower():
                error_details = 'ML model not found. The analysis will use basic heuristics.'
            elif 'decode' in error_message.lower() or 'parse' in error_message.lower():
                error_details = 'Failed to parse conversation file. Please check the file format.'
            elif 'memory' in error_message.lower():
                error_details = 'File too large or insufficient memory. Try a smaller file.'
            
            return Response({
                'error': 'Analysis failed',
                'message': error_message,
                'details': error_details,
                'traceback': error_traceback if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SocialMediaAnalysisView(APIView):
    """
    Social media-specific aesthetic analysis endpoint
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        # Check usage limit before processing
        req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
        can_use, current_usage = _check_usage_limit(req_ip)
        
        if not can_use:
            return Response({
                'error': 'Usage limit exceeded',
                'message': f'You have reached the limit of {_USAGE_LIMIT} analyses. Current usage: {current_usage}',
                'usage_limit_exceeded': True,
                'current_usage': current_usage,
                'limit': _USAGE_LIMIT
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        print("🚀 Social Media Analysis API called")
        print(f"📄 Request data keys: {list(request.data.keys())}")
        print(f"📄 Request files: {list(request.FILES.keys())}")
        print(f"📄 Request method: {request.method}")
        print(f"📄 Content type: {request.content_type}")
        
        try:
            if 'image' in request.FILES:
                print("✅ Image file found in request")
                image_file = request.FILES['image']
                platform = request.data.get('analysis_type', 'instagram')  # Default to Instagram
                caption = request.data.get('caption', '')  # Optional caption
                print(f"📄 Platform: {platform}, Caption: {caption[:50]}...")
                
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                try:
                    # Initialize AI service and run social media analysis
                    ai_service = ImageAnalysisService()
                    print(f"🎯 Running social media analysis for platform: {platform}")
                    
                    # Use the new social media analysis method
                    analysis_result = ai_service.analyze_social_media(
                        temp_file_path, 
                        platform=platform,
                        caption=caption
                    )
                    
                    print(f"✅ Social media analysis completed with score: {analysis_result.get('aesthetic_score', 'N/A')}")
                    
                    # Convert numpy arrays to JSON-serializable format
                    import json
                    import numpy as np
                    
                    def convert_numpy_types(obj):
                        if isinstance(obj, np.ndarray):
                            return obj.tolist()
                        elif isinstance(obj, np.floating):
                            return float(obj)
                        elif isinstance(obj, np.integer):
                            return int(obj)
                        elif isinstance(obj, dict):
                            return {key: convert_numpy_types(value) for key, value in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_numpy_types(item) for item in obj]
                        return obj
                    
                    # Make analysis result JSON serializable
                    serializable_result = convert_numpy_types(analysis_result)
                    
                    # Create AestheticAnalysis object directly (bypassing serializer validation issues)
                    from .models import AestheticAnalysis
                    analysis = AestheticAnalysis.objects.create(
                        image=image_file,
                        result=serializable_result
                    )

                    try:
                        req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
                        _increment_usage_for_ip(req_ip)
                    except Exception:
                        pass
                    
                    return Response(
                        AestheticAnalysisSerializer(analysis).data,
                        status=status.HTTP_201_CREATED
                    )
                    
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
            else:
                print("❌ No image file found in request")
                return Response(
                    {'error': 'No image file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            print(f"❌ Social media analysis error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Analysis failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
def detailed_image_analysis(request):
    """
    Advanced image analysis endpoint with comprehensive rating and suggestions
    """
    # Check usage limit before processing
    req_ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    can_use, current_usage = _check_usage_limit(req_ip)
    
    if not can_use:
        return Response({
            'error': 'Usage limit exceeded',
            'message': f'You have reached the limit of {_USAGE_LIMIT} analyses. Current usage: {current_usage}',
            'usage_limit_exceeded': True,
            'current_usage': current_usage,
            'limit': _USAGE_LIMIT
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
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
            
            # Record usage for this IP after successful analysis
            try:
                _increment_usage_for_ip(req_ip)
            except Exception:
                pass
            
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


# --- Simple in-memory IP usage tracker + debounce cache (ephemeral) ---
# NOTE: This is intentionally lightweight for development. Replace with
# a persistent DB-backed model for production use.
_IP_USAGE_COUNTS = {}  # ip -> int
_USAGE_LIMIT = 5
_DEBOUNCE_CACHE = {}  # ip -> (timestamp, response_data)
_DEBOUNCE_TTL = 1.5  # seconds

# File-backed store to persist usage across restarts (simple dev-only store)
_USAGE_STORE_PATH = getattr(settings, 'USAGE_STORE_PATH', None)
_USAGE_STORE_LOCK = threading.Lock()

def _get_usage_count_for_ip(ip):
    try:
        obj = IPUsage.objects.filter(ip_address=ip).first()
        return int(obj.count) if obj else 0
    except Exception:
        return 0


def _increment_usage_for_ip(ip):
    try:
        obj, created = IPUsage.objects.get_or_create(ip_address=ip)
        obj.count = obj.count + 1
        obj.save()
        return obj.count
    except Exception:
        # Fallback to in-memory increment if DB fails
        count = _IP_USAGE_COUNTS.get(ip, 0) + 1
        _IP_USAGE_COUNTS[ip] = count
        return count


def _reset_usage_for_ip(ip):
    """Reset usage count to 0 for the specified IP address"""
    try:
        obj = IPUsage.objects.filter(ip_address=ip).first()
        if obj:
            obj.count = 0
            obj.save()
            print(f"✅ Reset usage count to 0 for IP: {ip}")
        else:
            print(f"ℹ️  No usage record found for IP: {ip}")
        # Also clear from in-memory cache
        if ip in _IP_USAGE_COUNTS:
            _IP_USAGE_COUNTS[ip] = 0
        # Clear debounce cache
        if ip in _DEBOUNCE_CACHE:
            del _DEBOUNCE_CACHE[ip]
        return True
    except Exception as e:
        print(f"❌ Error resetting usage for IP {ip}: {e}")
        return False


def _check_usage_limit(ip):
    """Check if IP can still use the service (hasn't exceeded limit)"""
    current_usage = _get_usage_count_for_ip(ip)
    return current_usage < _USAGE_LIMIT, current_usage


@api_view(['GET'])
def usage_status(request):
    """Return usage status for the requesting IP.

    Response shape:
    {
        "ip_address": "1.2.3.4",
        "usage_count": 2,
        "remaining": 3,
        "limit": 5,
        "can_use": true,
        "percentage_used": 40.0,
        "request_id": "...",
        "server_timestamp": "...",
        "user_agent": "..."
    }
    """
    # Determine client IP (best-effort; may need X-Forwarded-For in prod)
    ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')

    # Debounce: if we've answered recently for this IP, return the cached payload
    now = time.time()
    cache_entry = _DEBOUNCE_CACHE.get(ip)
    if cache_entry:
        ts, cached = cache_entry
        if now - ts < _DEBOUNCE_TTL:
            # Return cached response to collapse near-simultaneous requests
            return Response(cached)

    # Determine usage count (from file-backed store if available)
    usage_count = _get_usage_count_for_ip(ip)

    remaining = max(0, _USAGE_LIMIT - usage_count)
    can_use = usage_count < _USAGE_LIMIT
    percentage_used = (usage_count / _USAGE_LIMIT) * 100.0 if _USAGE_LIMIT else 0.0

    payload = {
        'ip_address': ip,
        'usage_count': usage_count,
        'remaining': remaining,
        'limit': _USAGE_LIMIT,
        'can_use': can_use,
        'percentage_used': round(percentage_used, 2),
        'request_id': str(uuid.uuid4()),
        'server_timestamp': timezone.now().isoformat(),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
    }

    # Store in debounce cache
    _DEBOUNCE_CACHE[ip] = (now, payload)

    return Response(payload)



@api_view(['POST'])
def usage_increment(request):
    """Increment usage for requesting IP and return updated status."""
    ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        new_count = _increment_usage_for_ip(ip)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

    remaining = max(0, _USAGE_LIMIT - new_count)
    can_use = new_count < _USAGE_LIMIT
    payload = {
        'ip_address': ip,
        'usage_count': new_count,
        'remaining': remaining,
        'limit': _USAGE_LIMIT,
        'can_use': can_use,
        'percentage_used': round((new_count / _USAGE_LIMIT) * 100.0, 2) if _USAGE_LIMIT else 0.0,
        'request_id': str(uuid.uuid4()),
        'server_timestamp': timezone.now().isoformat(),
    }
    # update debounce cache so quick subsequent reads see latest value
    _DEBOUNCE_CACHE[ip] = (time.time(), payload)
    return Response(payload)


@api_view(['POST'])
def reset_usage(request):
    """Reset usage count for requesting IP - for testing purposes only"""
    ip = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    
    # Optional: Allow resetting specific IP if provided in request body
    if request.data and 'ip_address' in request.data:
        ip = request.data['ip_address']
    
    success = _reset_usage_for_ip(ip)
    
    if success:
        return Response({
            'message': f'Usage count reset to 0 for IP: {ip}',
            'ip_address': ip,
            'usage_count': 0,
            'remaining': _USAGE_LIMIT,
            'limit': _USAGE_LIMIT,
            'can_use': True,
            'percentage_used': 0.0,
            'request_id': str(uuid.uuid4()),
            'server_timestamp': timezone.now().isoformat(),
        })
    else:
        return Response({
            'error': f'Failed to reset usage for IP: {ip}'
        }, status=500)