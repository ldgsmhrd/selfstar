import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "@/api/client";

export default function PersonaQuickPicker({ buttonLabel = "프로필 선택", to = "/mypage" }){
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const navigate = useNavigate();

  const openPicker = async () => {
    setOpen(true); setLoading(true); setError(null);
    try{
  const r = await fetch(`${API_BASE}/api/personas/me`, { credentials:'include', cache:'no-store' });
      if(!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      const arr = Array.isArray(j?.items) ? j.items : [];
      arr.sort((a,b)=> (a.num||0)-(b.num||0));
      setItems(arr);
    }catch(e){ setError(e?.message || '로드 실패'); }
    finally{ setLoading(false); }
  };

  const pick = (p) => {
    try{ if(p?.num) localStorage.setItem('activePersonaNum', String(p.num)); }catch{}
    try{ window.dispatchEvent(new CustomEvent('persona-chosen', { detail: p })); }catch{}
    setOpen(false);
    navigate(to);
  };

  return (
    <>
      <button className="btn light" onClick={openPicker}>{buttonLabel}</button>
      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-[rgba(2,6,23,0.45)] p-4" onClick={()=>setOpen(false)}>
          <div className="w-[min(420px,92vw)] rounded-2xl border bg-white shadow-xl" onClick={(e)=>e.stopPropagation()}>
            <div className="p-4 border-b flex items-center justify-between">
              <div className="font-semibold">프로필 선택</div>
              <button className="text-slate-500 hover:text-slate-700" onClick={()=>setOpen(false)}>×</button>
            </div>
            <div className="p-3">
              {loading ? (
                <div className="h-24 rounded-xl bg-slate-100 animate-pulse" />
              ) : error ? (
                <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-3 py-2 text-sm">{String(error)}</div>
              ) : (
                <ul className="divide-y">
                  {items.map(p=> (
                    <li key={p.num}>
                      <button className="w-full flex items-center gap-3 px-2 py-2 hover:bg-slate-50" onClick={()=>pick(p)}>
                        {p.img ? <img src={p.img} alt="" className="w-9 h-9 rounded-full object-cover border" /> : <div className="w-9 h-9 rounded-full bg-slate-200" />}
                        <div className="flex-1 text-left text-sm font-semibold">{p.name || `프로필`}</div>
                      </button>
                    </li>
                  ))}
                  {!items.length && (
                    <li className="text-sm text-slate-500 px-2 py-2">프로필이 없습니다.</li>
                  )}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
