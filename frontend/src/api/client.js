const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health request failed: ${res.status}`);
  }
  return res.json();
}
