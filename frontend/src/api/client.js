// 기본값: Vite 개발 서버 프록시를 이용하기 위해 빈 문자열 사용
// 필요 시 .env에서 VITE_API_BASE_URL 로 절대주소 지정 가능
export const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env)
  ? (import.meta.env.VITE_API_BASE ?? '')
  : '';

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health request failed: ${res.status}`);
  }
  return res.json();
}
