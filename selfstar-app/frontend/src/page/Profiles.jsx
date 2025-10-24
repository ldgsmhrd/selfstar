import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { API_BASE } from "@/api/client";

export default function Profiles() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [personas, setPersonas] = useState([]);
  const [activeNum, setActiveNum] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE}/personas/list`, { credentials: "include" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setPersonas(Array.isArray(data?.items) ? data.items : []);
        setActiveNum(data?.active_num ?? null);
      } catch (e) {
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const choosePersona = async (p) => {
    try {
      const res = await fetch(`${API_BASE}/personas/activate`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ persona_num: p.num }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setActiveNum(p.num);
      nav("/mypage", { replace: true });
    } catch (e) {
      setError(e?.message || String(e));
    }
  };

  if (loading) return <main className="p-6">불러오는 중…</main>;
  if (error) return <main className="p-6 text-red-600">오류: {error}</main>;

  return (
    <main className="mx-auto max-w-6xl px-6 py-7">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">프로필 선택</h1>
        <Link to="/imgcreate" className="btn primary">새 프로필 만들기</Link>
      </div>
      {personas.length ? (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {personas.map((p) => (
            <button
              key={p.num}
              onClick={() => choosePersona(p)}
              className={`group relative rounded-2xl border ${activeNum===p.num?"border-blue-400 bg-blue-50/60":"border-slate-200 bg-white/70"} overflow-hidden text-left shadow-sm hover:shadow-md transition`}
            >
              <div className="aspect-[4/5] w-full bg-gradient-to-b from-slate-100 to-slate-50">
                {p.img ? (
                  <img src={p.img} alt="persona" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-gray-200 grid place-items-center text-gray-500">로딩 중...</div>
                )}
              </div>
              <div className="px-3 py-2 flex items-center justify-between">
                <div className="font-semibold truncate">{p.name || `프로필 ${p.num}`}</div>
                {activeNum === p.num && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full border bg-blue-100 text-blue-700 border-blue-200">선택됨</span>
                )}
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-slate-500">등록된 프로필이 없습니다. 새로 만들어보세요.</div>
      )}
    </main>
  );
}