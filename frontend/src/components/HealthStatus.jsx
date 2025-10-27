import React from 'react';
import { useHealth } from '../hooks/useHealth.js';

export default function HealthStatus() {
  const { data, loading, error, refresh } = useHealth(true);

  return (
    <div style={box}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>Health</h2>
        <button onClick={refresh} disabled={loading} style={btn}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      {error && <p style={{ color: 'crimson' }}>Error: {error.message}</p>}
      {data && (
        <ul style={ul}>
          <li><strong>Status:</strong> {data.status}</li>
          <li><strong>Timestamp:</strong> {data.timestamp}</li>
        </ul>
      )}
      {!error && !data && !loading && <p>Press Refresh to load.</p>}
    </div>
  );
}

const box = {
  border: '1px solid #ddd',
  borderRadius: 8,
  padding: '1rem',
  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
  background: '#fff'
};

const btn = {
  padding: '0.4rem 0.8rem',
  borderRadius: 4,
  border: '1px solid #ccc',
  cursor: 'pointer',
  background: '#f5f5f5'
};

const ul = {
  listStyle: 'none',
  padding: 0,
  margin: '0.5rem 0 0'
};
