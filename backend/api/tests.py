from rest_framework.test import APITestCase
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from PIL import Image
import io


class APITestCase(APITestCase):
    def test_health_check(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')

    def test_conversation_analysis(self):
        data = {
            'conversation_text': 'This is a test conversation about technology and innovation.'
        }
        response = self.client.post('/api/conversation-analysis/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)

    @patch('api.views._check_usage_limit', return_value=(True, 0))
    @patch('api.views._increment_usage_for_ip', return_value=1)
    def test_photo_upload_preserves_learned_rating_and_reports_blank_composition(self, increment, usage):
        buffer = io.BytesIO()
        Image.new('RGB', (100, 100), (255, 0, 0)).save(buffer, format='PNG')
        upload = SimpleUploadedFile('flat.png', buffer.getvalue(), content_type='image/png')
        response = self.client.post('/api/detailed-image-analysis/', {'image': upload}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        analysis = response.json()['analysis']
        self.assertEqual(analysis['aesthetic_score']['mode'], 'learned-nima')
        self.assertEqual(analysis['overall_rating']['score'], analysis['aesthetic_score']['score'])
        self.assertEqual(analysis['composition_analysis']['method'], 'insufficient-evidence')
        self.assertFalse(analysis['composition_analysis']['ml_reliable'])
