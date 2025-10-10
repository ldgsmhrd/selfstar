import React from 'react';
import HealthStatus from './components/HealthStatus.jsx';

export default function App() {
  return (
    <div style={styles.container}>
      <h1>SelfStar Frontend</h1>
      <p style={styles.subtitle}>FastAPI 백엔드 헬스 상태 확인 예제</p>
      <HealthStatus />
    </div>
  );
}

const styles = {
  container: {
    fontFamily: 'system-ui, sans-serif',
    maxWidth: 640,
    margin: '2rem auto',
    padding: '0 1rem'
  },
  subtitle: {
    color: '#555'
  }
};
