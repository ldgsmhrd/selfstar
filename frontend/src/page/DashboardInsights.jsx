import { useEffect, useState } from "react";
// import { Link } from "react-router-dom";
import { API_BASE } from "@/api/client";
import PersonaQuickPicker from "@/components/PersonaQuickPicker.jsx";

export default function DashboardInsights() {
  const [personas, setPersonas] = useState([]);
  const [persona, setPersona] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [daily, setDaily] = useState(null); // { followers_delta:[], likes_delta:[] }
  const [mediaItems, setMediaItems] = useState([]);
  const [mediaError, setMediaError] = useState(null);
  const [mediaLoading, setMediaLoading] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/personas/me`, { credentials: 'include' });
        if (!res.ok) return;
        const j = await res.json();
        const items = Array.isArray(j?.items) ? j.items : [];
        items.sort((a,b)=> (a.num||0)-(b.num||0));
        if (!alive) return;
        setPersonas(items);
        const saved = Number(localStorage.getItem('activePersonaNum') || 0);
        const pick = items.find(p=>p.num===saved) || items[0] || null;
        setPersona(pick);
      } catch {}
    })();
    return ()=>{ alive=false; };
  }, []);

  useEffect(() => {
    const load = async () => {
      if (!persona?.num) { setData(null); return; }
      setLoading(true); setError(null);
      try {
  const res = await fetch(`${API_BASE}/instagram/insights/overview?persona_num=${persona.num}&days=30`, { credentials: 'include' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const j = await res.json();
        setData(j);
        // 일별 증가
        const d = await fetch(`${API_BASE}/instagram/insights/daily?persona_num=${persona.num}&days=30`, { credentials: 'include' });
        if (d.ok) setDaily(await d.json()); else setDaily(null);
        // 게시글별 인사이트
        setMediaLoading(true); setMediaError(null);
        const m = await fetch(`${API_BASE}/instagram/insights/media_overview?persona_num=${persona.num}&limit=12&days=30`, { credentials: 'include' });
        if (m.ok) {
          const mj = await m.json();
          setMediaItems(Array.isArray(mj?.items)? mj.items : []);
        } else {
          setMediaItems([]);
          setMediaError(`HTTP ${m.status}`);
        }
      } catch (e) {
        setError(e?.message || '로드 실패');
        setData(null);
        setDaily(null);
        setMediaItems([]);
        setMediaError(e?.message || '로드 실패');
      } finally { setLoading(false); }
    };
    load();
  }, [persona?.num]);

  return (
    <div className="w-full space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black">인사이트</h1>
            <select
              value={persona?.num || ''}
              onChange={(e)=>{
                const p = personas.find(x=>String(x.num)===e.target.value);
                setPersona(p||null);
                if (p?.num) localStorage.setItem('activePersonaNum', String(p.num));
              }}
              className="h-9 px-3 rounded-xl border bg-white"
            >
              {personas.map(p=> <option key={p.num} value={p.num}>{p.name || `프로필 ${p.num}`}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <PersonaQuickPicker buttonLabel="프로필 선택" to="/dashboard" />
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{String(error)}</div>
        )}

        {loading ? (
          <>
            <div className="grid md:grid-cols-3 gap-6">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="h-4 w-24 bg-slate-200 rounded animate-pulse mb-4" />
              <div className="grid md:grid-cols-3 gap-4">
                {Array.from({length:6}).map((_,i)=>(
                  <div key={i} className="rounded-xl border bg-white/70 p-3 flex items-center gap-3">
                    <div className="w-14 h-14 rounded-md bg-slate-200 animate-pulse" />
                    <div className="flex-1">
                      <div className="h-3 w-24 bg-slate-200 rounded animate-pulse mb-2" />
                      <div className="h-3 w-36 bg-slate-200 rounded animate-pulse mb-1" />
                      <div className="h-3 w-20 bg-slate-200 rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="grid md:grid-cols-3 gap-6">
              <InsightStat label="팔로워" value={fmtNum(data?.followers_count)} sub={todayTrendText(data) || trendText(data?.series?.follows, data?.series?.unfollows)} />
              <InsightStat label="도달" value={sumSeries(data?.series?.reach)} spark={data?.series?.reach} />
              <InsightStat label="노출" value={sumSeries(data?.series?.impressions)} spark={data?.series?.impressions} />
            </div>

            {/* 30일 일별 시각화 */}
            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="text-sm text-slate-500 mb-2">30일 · 팔로워 수 / 프로필 방문수</div>
              <MultiLineChart
                width={760}
                height={240}
                series={[
                  { name: '팔로워 수', color: '#2563eb', data: data?.series?.follower_count || [] },
                  { name: '프로필 방문수', color: '#16a34a', data: data?.series?.profile_views || [] },
                ]}
              />
            </div>

            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm text-slate-500">30일 · 게시일 기준 좋아요 합계(approx)</div>
                <div className="text-[10px] text-slate-400">API 한계로 일별 증가분은 스냅샷 저장이 필요</div>
              </div>
              <BarChart width={760} height={180} data={data?.series?.approx_likes_by_post_day || []} color="#f59e0b" />
            </div>

            {/* 스냅샷 기반 일별 증가 */}
            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="text-sm text-slate-500 mb-2">스냅샷 · 팔로워 일별 증가</div>
              <LineChart width={760} height={180} data={daily?.followers_delta || []} color="#2563eb" />
              {!daily?.followers_delta?.length && (
                <div className="text-xs text-slate-400 mt-2">스냅샷이 아직 부족합니다. 자정 자동 스냅샷 이후에 증가분이 표시됩니다.</div>
              )}
            </div>

            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="text-sm text-slate-500 mb-2">스냅샷 · 좋아요 일별 증가</div>
              <BarChart width={760} height={180} data={daily?.likes_delta || []} color="#fb7185" />
              {!daily?.likes_delta?.length && (
                <div className="text-xs text-slate-400 mt-2">스냅샷이 부족합니다. 최소 2일 이상 자동 기록이 있어야 증가분이 계산됩니다.</div>
              )}
            </div>

            <div className="rounded-3xl border bg-white/80 p-6">
              <div className="text-sm text-slate-500 mb-3">최근 게시글</div>
              {mediaLoading ? (
                <div className="h-24 bg-slate-100/60 rounded-xl animate-pulse" />
              ) : mediaError ? (
                <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-3 py-2 text-xs">게시글 인사이트 로드 실패: {String(mediaError)}</div>
              ) : (
                <div className="grid md:grid-cols-3 gap-4">
                  {(mediaItems || []).slice(0,9).map(m => (
                    <a key={m.id} href={m.permalink} target="_blank" rel="noreferrer" className="rounded-xl border bg-white/70 p-3 flex items-center gap-3 hover:shadow-sm">
                      <img src={m.preview_url} alt="" className="w-14 h-14 rounded-md object-cover border" />
                      <div className="min-w-0">
                        <div className="text-xs text-slate-500">{fmtDate(m.timestamp)} · {(m.media_product_type || m.media_type) || ''}</div>
                        <div className="text-sm font-semibold truncate">
                          {('plays' in (m.insights||{})) ? (
                            <>
                              재생 {fmtNum(m.insights?.plays)} · 도달 {fmtNum(m.insights?.reach)} · 저장 {fmtNum(m.insights?.saves)}
                            </>
                          ) : (
                            <>
                              노출 {fmtNum(m.insights?.impressions)} · 도달 {fmtNum(m.insights?.reach)} · 저장 {fmtNum(m.insights?.saved)}
                            </>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">❤️ {fmtNum(m.like_count)} · 💬 {fmtNum(m.comments_count)}</div>
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
    </div>
  );
}

function fmtNum(v){ if(v===null||v===undefined) return '-'; const n=Number(v); if(Number.isNaN(n)) return String(v); if(n>=1e6) return (n/1e6).toFixed(1)+'M'; if(n>=1e3) return (n/1e3).toFixed(1)+'K'; return String(n); }
function sumSeries(a){ if(!Array.isArray(a)) return '-'; const s=a.reduce((t,x)=>t+(Number(x?.value)||0),0); return fmtNum(s); }
function trendText(f,u){ if(!Array.isArray(f)||!Array.isArray(u)) return '-'; const sf=f.reduce((t,x)=>t+(Number(x?.value)||0),0); const su=u.reduce((t,x)=>t+(Number(x?.value)||0),0); const net=sf-su; const sign=net>0?'+':net<0?'':''; return `순증가 ${sign}${fmtNum(net)}`; }
function todayTrendText(d){ const v = (d?.today_followers_delta); if(v===null||v===undefined) return ''; const n=Number(v); if(Number.isNaN(n)) return ''; const sign=n>0?'+':n<0?'':''; return `오늘 순증가 ${sign}${fmtNum(n)}`; }

function InsightStat({ label, value, sub, spark }){
  return (
    <div className="rounded-3xl border bg-white/80 p-6">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-2xl font-bold mt-1">{value ?? '-'}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
      {Array.isArray(spark) && spark.length>1 && (
        <div className="mt-3 h-10"><Sparkline data={spark.map(p=>Number(p.value)||0)} /></div>
      )}
    </div>
  );
}

function SkeletonCard(){
  return (
    <div className="rounded-3xl border bg-white/80 p-6 animate-pulse">
      <div className="h-3 w-14 bg-slate-200 rounded" />
      <div className="h-7 w-24 bg-slate-200 rounded mt-2" />
      <div className="h-10 w-full bg-slate-200 rounded mt-3" />
    </div>
  );
}

function Sparkline({ data=[] }){ const w=140,h=36; const max=Math.max(...data,1); const min=Math.min(...data,0); const span=Math.max(max-min,1); const step=data.length>1?(w/(data.length-1)):w; const pts=data.map((v,i)=>{ const x=i*step; const y=h-((v-min)/span)*h; return `${x},${y}`; }).join(' '); return (<svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}><polyline points={pts} fill="none" stroke="#2563eb" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" /></svg>); }
function fmtDate(s){ try{ return new Date(s).toLocaleDateString(); }catch{ return s||''; } }

// 간단한 SVG 멀티라인 차트
function MultiLineChart({ width=640, height=220, series=[] }){
  const pad=24; const innerW=width-pad*2; const innerH=height-pad*2;
  const dates=(series[0]?.data||[]).map(d=>d.date);
  const lines=series.map(s=>({ name:s.name, color:s.color, values:(s.data||[]).map(d=>Number(d.value)||0) }));
  const all=lines.flatMap(l=>l.values);
  const max=Math.max(1,...all);
  const step=dates.length>1?innerW/(dates.length-1):innerW;
  const toX=i=>pad+i*step; const toY=v=>pad+innerH-(v/max)*innerH;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#e5e7eb" />
      {lines.map((l,idx)=>{
        const pts=l.values.map((v,i)=>`${toX(i)},${toY(v)}`).join(' ');
        return <polyline key={idx} points={pts} fill="none" stroke={l.color||'#2563eb'} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"/>;
      })}
    </svg>
  );
}

function BarChart({ width=640, height=160, data=[], color="#2563eb" }){
  const pad=24; const innerW=width-pad*2; const innerH=height-pad*2;
  const vals=(data||[]).map(d=>Number(d.value)||0);
  const max=Math.max(1,...vals);
  const bw=data.length?innerW/data.length-2:innerW;
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#e5e7eb" />
      {(data||[]).map((d,i)=>{
        const h=(vals[i]/max)*innerH; const x=pad+i*(bw+2); const y=height-pad-h;
        return <rect key={d.date||i} x={x} y={y} width={bw} height={h} rx={3} fill={color} opacity={0.85}/>;
      })}
    </svg>
  );
}

function LineChart({ width=640, height=160, data=[], color="#2563eb" }){
  const pad=24; const innerW=width-pad*2; const innerH=height-pad*2;
  const vals=(data||[]).map(d=>Number(d.value)||0);
  const max=Math.max(1,...vals);
  const step=(data||[]).length>1?innerW/((data||[]).length-1):innerW;
  const toX=i=>pad+i*step; const toY=v=>pad+innerH-(v/max)*innerH;
  const pts=(data||[]).map((d,i)=>`${toX(i)},${toY(vals[i])}`).join(' ');
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} stroke="#e5e7eb" />
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
