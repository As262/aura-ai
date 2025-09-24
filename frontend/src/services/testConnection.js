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

    // Test user registration (will fail if user exists, that's okay)
    const testUser = {
      username: 'testuser123',
      email: 'test@example.com',
      password: 'testpass123'
    };

    const registerResult = await ApiService.registerUser(testUser);
    if (registerResult.success) {
      console.log('✅ User registration test passed');
    } else {
      console.log('ℹ️ User registration test result:', registerResult.error);
    }

    // Test login
    const loginResult = await ApiService.loginUser({
      username: testUser.username,
      password: testUser.password
    });
    if (loginResult.success) {
      console.log('✅ Login test passed');
    } else {
      console.log('ℹ️ Login test result:', loginResult.error);
    }

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