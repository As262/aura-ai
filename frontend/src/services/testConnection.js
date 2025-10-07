// Test script to verify backend connection
import ApiService from '../services/ApiService.js';

const testBackendConnection = async () => {
  console.log('🧪 Testing backend connection...');
  
  try {
    // Test health endpoint
    const health = await ApiService.healthCheck();
    if (health.success) {
      console.log('✅ Health check passed:', health.data);
    } else {
      console.log('❌ Health check failed:', health.error);
      return;
    }

    // Test connection status
    const connected = await ApiService.testConnection();
    console.log(`🔗 Connection status: ${connected ? 'Connected' : 'Disconnected'}`);

    console.log('🎉 Backend connection tests completed!');
    
  } catch (error) {
    console.error('💥 Test failed:', error);
  }
};

// Run tests if this script is executed directly
if (typeof window === 'undefined') {
  testBackendConnection();
}

export default testBackendConnection;