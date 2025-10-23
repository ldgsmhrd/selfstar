import { useEffect, useState, useMemo } from "react";

// API base: prefer Vite proxy; fallback to empty string
const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env)
  ? (import.meta.env.VITE_API_BASE ?? '')
  : '';

function formatTime(ts) {
  try {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts || '';
    return d.toLocaleString();
  } catch {
    return ts || '';
  }
}

export default function Alerts() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({ ok: true, personas: [] });
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/instagram/comments/overview?media_limit=5&comments_limit=8`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' },
      });
      if (res.status === 401) {
        throw new Error('로그인이 필요합니다.');
      }
      if (!res.ok) {
        throw new Error(`요청 실패: HTTP ${res.status}`);
      }
      const json = await res.json();
      setData(json || { ok: false, personas: [] });
      setLastUpdated(new Date());
    } catch (e) {
      setError(e?.message || '네트워크 오류');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-black">알림</h2>
        <div className="flex items-center gap-3 text-sm text-slate-500">
          {lastUpdated && (
            <span>업데이트: {lastUpdated.toLocaleTimeString()}</span>
          )}
          <button
            onClick={fetchOverview}
            className="px-3 py-1.5 rounded-full border bg-white hover:bg-slate-50 text-slate-700 disabled:opacity-60"
            disabled={loading}
          >
            {loading ? '불러오는 중…' : '새로고침'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-slate-500">불러오는 중…</div>
      )}
      {error && (
        <div className="text-red-600">{error}</div>
      )}

      {!loading && !error && (!data?.personas || data.personas.length === 0) && (
        <div className="text-slate-500">연동된 프로필이 없거나 댓글이 없습니다.</div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {data?.personas?.map((p) => (
          <PersonaCard key={p.persona_num} persona={p} />
        ))}
      </div>
    </div>
  );
}

function PersonaCard({ persona }) {
  const { persona_name, persona_img, ig_username, items = [] } = persona;

  return (
    <div className="rounded-2xl border bg-white shadow-sm overflow-hidden">
      <div className="flex items-center gap-3 p-4 border-b bg-slate-50/60">
        {persona_img ? (
          <img src={persona_img} alt="persona" className="w-9 h-9 rounded-full object-cover border" />
        ) : (
          <div className="w-9 h-9 rounded-full bg-slate-200" />
        )}
        <div className="flex-1 min-w-0">
          <div className="font-semibold truncate">{persona_name || '프로필'}</div>
          <div className="text-xs text-slate-500 truncate">@{ig_username || '연동안됨'}</div>
        </div>
      </div>

      <div className="p-4">
        {(!items || items.length === 0) ? (
          <div className="text-sm text-slate-500">표시할 댓글이 없습니다.</div>
        ) : (
          <div className="space-y-5">
            {items.map((m) => (
              <MediaBlock key={m.media_id} media={m} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MediaBlock({ media }) {
  const thumb = media.thumbnail_url || media.media_url;
  const comments = media.comments || [];
  return (
    <div className="rounded-xl border bg-white/60">
      {/* 미디어 헤더: 캡션과 썸네일, 링크 */}
      <div className="grid grid-cols-12 gap-3 p-3 border-b items-center">
        <div className="col-span-9 min-w-0">
          <div className="text-sm font-semibold text-slate-800 truncate" title={media.caption || ''}>
            {media.caption || '(캡션 없음)'}
          </div>
          <div className="text-xs text-slate-500 mt-0.5">{formatTime(media.timestamp)}</div>
          {media.permalink && (
            <a href={media.permalink} target="_blank" rel="noreferrer" className="inline-block mt-1 text-xs text-blue-600 hover:underline">
              원본 게시글 열기
            </a>
          )}
        </div>
        <div className="col-span-3">
          {thumb ? (
            <img
              src={thumb}
              alt="post"
              className="ml-auto w-16 h-16 rounded-md object-cover border shadow-sm"
            />
          ) : (
            <div className="ml-auto w-16 h-16 rounded-md bg-slate-200" />)
          }
        </div>
      </div>
      {/* 댓글 목록 */}
      <div className="divide-y">
        {comments.length === 0 ? (
          <div className="text-sm text-slate-500 p-3">이 게시글에 표시할 댓글이 없습니다.</div>
        ) : (
          comments.map((c) => (
            <div key={c.id} className="p-3 grid grid-cols-12 gap-2 items-start">
              <div className="col-span-2 text-sm font-semibold truncate">{c.username || '사용자'}</div>
              <div className="col-span-8 text-sm text-slate-700 break-words" title={c.text}>{c.text}</div>
              <div className="col-span-2 text-xs text-slate-500 text-right">{formatTime(c.timestamp)}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
