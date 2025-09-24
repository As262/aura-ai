from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import UserProfile, AestheticAnalysis, ConversationAnalysis


class UserProfileTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), "testuser's Profile")


class APITestCase(APITestCase):
    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_user_registration(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_conversation_analysis(self):
        data = {
            'conversation_text': 'This is a test conversation about technology and innovation.'
        }
        response = self.client.post('/api/conversation-analysis/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('analysis_result', response.data)