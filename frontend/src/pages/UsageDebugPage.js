import React from 'react';
import { useUsage } from '../contexts/UsageContext';

function UsageDebugPage() {
  const { usage, refresh } = useUsage() || {};

  const handleIncrement = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/usage-increment/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      const data = await response.json();
      console.log('Manual increment result:', data);
      // Refresh after increment
      refresh();
    } catch (error) {
      console.error('Manual increment failed:', error);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Usage Debug Page</h2>
      <div style={{ background: '#f0f0f0', padding: '10px', margin: '10px 0' }}>
        <h3>Current Usage Data:</h3>
        <pre>{JSON.stringify(usage, null, 2)}</pre>
      </div>
      <div>
        <button onClick={refresh} style={{ margin: '5px' }}>
          Manual Refresh
        </button>
        <button onClick={handleIncrement} style={{ margin: '5px' }}>
          Increment & Refresh
        </button>
      </div>
      <div style={{ marginTop: '20px', fontSize: '12px' }}>
        <p>This page polls every 5 seconds. Watch the console for polling logs.</p>
        <p>Check developer console for detailed logs from PollManager.</p>
      </div>
    </div>
  );
}

export default UsageDebugPage;