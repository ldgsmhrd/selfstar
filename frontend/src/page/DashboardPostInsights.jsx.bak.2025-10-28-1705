import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { API_BASE } from "@/api/client";
import PersonaQuickPicker from "@/components/PersonaQuickPicker.jsx";

export default function DashboardPostInsights(){
  const [items,setItems]=useState([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState(null);
  const navigate = useNavigate();
  useEffect(()=>{
    let alive=true;
    (async()=>{
      setLoading(true); setError(null);
      try{
        const personaNum = Number(localStorage.getItem('activePersonaNum')||'0');
  const r = await fetch(`${API_BASE}/api/instagram/insights/media_overview?persona_num=${personaNum}&limit=18&days=30`, { credentials:'include' });
        if(!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = await r.json();
        if(alive) setItems(Array.isArray(j?.items)? j.items:[]);
      }catch(e){ if(alive) setError(e?.message||'로드 실패'); }
      finally{ if(alive) setLoading(false); }
    })();
    return ()=>{ alive=false; };
  },[]);

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black">게시글 인사이트</h2>
        <div className="flex items-center gap-2">
          <PersonaQuickPicker buttonLabel="프로필 선택" to="/dashboard" />
        </div>
      </div>
      {loading? (
        <div>
          <div className="h-24 rounded-xl bg-slate-100 animate-pulse" />
          <div className="text-xs text-slate-500 mt-2">게시글 인사이트를 불러오는 중…</div>
        </div>
      ) : error? (
        <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{String(error)}</div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map(m=> (
            <button key={m.id} onClick={()=> navigate(`/dashboard/post-insights/${m.id}`)} className="text-left rounded-xl border bg-white/80 p-3 hover:shadow-sm">
              <div className="flex gap-3">
                <img src={m.preview_url} alt="" className="w-16 h-16 rounded-lg object-cover border" />
                <div className="min-w-0 flex-1">
                  <div className="text-xs text-slate-500">{fmtDate(m.timestamp)} · {(m.media_product_type||m.media_type)||''}</div>
                  <div className="text-sm font-semibold truncate">{truncate(m.caption, 40) || '제목 없음'}</div>
                  <div className="text-xs text-slate-600 mt-1">
                    {('plays' in (m.insights||{}))? (
                      <>재생 {fmtNum(m.insights?.plays)} · 도달 {fmtNum(m.insights?.reach)} · 저장 {fmtNum(m.insights?.saves)}</>
                    ):(
                      <>노출 {fmtNum(m.insights?.impressions)} · 도달 {fmtNum(m.insights?.reach)} · 저장 {fmtNum(m.insights?.saved)}</>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function fmtDate(s){ try{ return new Date(s).toLocaleDateString(); }catch{ return s||''; } }
function fmtNum(v){ const n=Number(v||0); if(n>=1e6) return (n/1e6).toFixed(1)+'M'; if(n>=1e3) return (n/1e3).toFixed(1)+'K'; return String(n); }
function truncate(s,max){ if(!s) return s; return s.length>max? s.slice(0,max-1)+'…' : s; }
