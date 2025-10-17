import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE } from "@/api/client";

export default function MyPage() {
  const [tab, setTab] = useState("posts");
  const [todos, setTodos] = useState([
    { id: 1, text: "프로필 소개 업데이트", done: false },
    { id: 2, text: "인스타 연동 확인", done: false },
    { id: 3, text: "샘플 사진 5장 업로드", done: false },
  ]);
  const credit = 0;
  const creditMax = 100;

  // Personas state
  const [personas, setPersonas] = useState([]); // [{ num, img, name }]
  const [activePersona, setActivePersona] = useState(null);
  const [selectorOpen, setSelectorOpen] = useState(false);
  const [integrationsOpen, setIntegrationsOpen] = useState(false);
  const [loadingPersona, setLoadingPersona] = useState(false);

  useEffect(() => {
    let alive = true;
    const saved = Number(localStorage.getItem("activePersonaNum") || "0");
    (async () => {
      try {
        setLoadingPersona(true);
        const res = await fetch(`${API_BASE}/personas/me`, { credentials: "include" });
        if (!res.ok) return;
        const data = await res.json();
        if (!alive) return;
        const items = Array.isArray(data?.items) ? data.items : [];
        items.sort((a, b) => (a.num || 0) - (b.num || 0));
        setPersonas(items);
        const picked = items.find((p) => p.num === saved) || items[0] || null;
        setActivePersona(picked);
        if (picked?.num) localStorage.setItem("activePersonaNum", String(picked.num));
      } catch {
        // noop
      } finally {
        setLoadingPersona(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  const choosePersona = (p) => {
    setActivePersona(p);
    if (p?.num) localStorage.setItem("activePersonaNum", String(p.num));
    setSelectorOpen(false);
  };

  const posts = useMemo(
    () => [
      { id: "post1", title: "게시물을 올려주세요.", date: "게시물 올린 날짜", channel: "플랫폼", status: "작성" },
    ],
    []
  );

  return (
    <main className="w-full min-h-screen bg-[#eaf5ff]">
      <div className="mx-auto max-w-6xl px-6 py-7">
        <HeaderSummary
          credit={credit}
          creditMax={creditMax}
          personaName={activePersona?.name}
          personaImg={activePersona?.img}
          onOpenSelector={() => setSelectorOpen(true)}
          onOpenIntegrations={() => setIntegrationsOpen(true)}
          loadingPersona={loadingPersona}
        />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-6">
          <aside className="lg:col-span-4 space-y-6">
            <Card>
              <div className="text-sm text-slate-500">SNS 연동</div>
              <div className="mt-4 space-y-4">
                <ConnectRow logo="IG" name="Instagram" status="미연동" hint="연동해주세요!" />
                <ConnectRow logo="Th" name="Threads" status="미연동" hint="연동해주세요!" />
              </div>
              <button className="btn primary mt-4 w-full" onClick={() => setIntegrationsOpen(true)}>
                인스타 연동 하기
              </button>
            </Card>

            <Card>
              <div className="text-sm text-slate-500">오늘의 할 일</div>
              <ul className="mt-3 space-y-2">
                {todos.map((t) => (
                  <li key={t.id} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={t.done}
                      onChange={() => setTodos(todos.map((x) => (x.id === t.id ? { ...x, done: !x.done } : x)))}
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-400"
                    />
                    <span className={t.done ? "line-through text-slate-400" : ""}>{t.text}</span>
                  </li>
                ))}
              </ul>
              <button
                className="btn light mt-3 w-full"
                onClick={() => setTodos((prev) => prev.concat({ id: Date.now(), text: "새 할 일", done: false }))}
              >
                할 일 추가
              </button>
            </Card>
          </aside>

          <section className="lg:col-span-8 space-y-6">
            <div className="flex items-center justify-between">
              <div className="rounded-full bg-white/80 border border-slate-200 p-1 inline-flex shadow-sm">
                <TabButton active={tab === "photos"} onClick={() => setTab("photos")} label="사진" />
                <TabButton active={tab === "posts"} onClick={() => setTab("posts")} label="게시글" />
                <TabButton active={tab === "drafts"} onClick={() => setTab("drafts")} label="임시저장" />
                <TabButton active={tab === "scheduled"} onClick={() => setTab("scheduled")} label="예약" />
              </div>
              <div className="text-slate-600 font-semibold">대시보드</div>
            </div>

            {(tab === "photos" || tab === "drafts" || tab === "scheduled") && (
              <Card>
                <Empty title="아직 콘텐츠가 없어요" action="새로 만들기" />
              </Card>
            )}

            {tab === "posts" && (
              <Card>
                <div className="flex items-center justify-between">
                  <div className="text-sm text-slate-500">총 {posts.length}개</div>
                  <select className="h-9 px-3 rounded-xl border border-slate-300 bg-white/80 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300">
                    <option>전체</option>
                    <option>발행</option>
                    <option>예약</option>
                    <option>초안</option>
                    <option>작성</option>
                  </select>
                </div>
                <div className="mt-3 divide-y">
                  {posts.map((x) => (
                    <div key={x.id} className="py-4 flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{x.title}</div>
                        <div className="text-xs text-slate-500">{x.date} · {x.channel}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${badgeTone(x.status)}`}>{x.status}</span>
                        <button className="btn light">미리보기</button>
                        <button className="btn primary">편집</button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </section>
        </div>
      </div>

      {/* Profile switcher modal */}
      {selectorOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-4xl rounded-2xl border border-slate-200 bg-white/90 backdrop-blur shadow-[0_30px_70px_rgba(2,6,23,0.28)] overflow-hidden">
            <div className="px-5 py-4 flex items-center justify-between border-b">
              <div className="font-semibold">프로필 교체하기</div>
              <button className="btn" onClick={() => setSelectorOpen(false)}>닫기</button>
            </div>
            <div className="p-5">
              {personas?.length ? (
                <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                  {personas.map((p) => (
                    <button
                      key={p.num}
                      onClick={() => choosePersona(p)}
                      className={`group relative rounded-2xl border ${activePersona?.num===p.num?"border-blue-400 bg-blue-50/60":"border-slate-200 bg-white/70"} overflow-hidden text-left shadow-sm hover:shadow-md transition`}
                    >
                      <div className="aspect-[4/5] w-full bg-gradient-to-b from-slate-100 to-slate-50">
                        {p.img ? (
                          <img src={p.img} alt="persona" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full grid place-items-center text-slate-400">이미지 없음</div>
                        )}
                      </div>
                      <div className="px-3 py-2 flex items-center justify-between">
                        <div className="font-semibold truncate">{p.name || `프로필 ${p.num}`}</div>
                        {activePersona?.num === p.num && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full border bg-blue-100 text-blue-700 border-blue-200">선택됨</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-center py-10 text-slate-500">등록된 프로필이 없습니다. 새로 만들어보세요.</div>
              )}
              <div className="mt-5 flex items-center justify-between">
                <button className="btn" onClick={() => setSelectorOpen(false)}>취소</button>
                <Link to="/imgcreate" className="btn primary">새 프로필 만들기</Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integrations modal */}
      {integrationsOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white/90 backdrop-blur shadow-[0_30px_70px_rgba(2,6,23,0.28)] overflow-hidden">
            <div className="px-5 py-4 flex items-center justify-between border-b">
              <div className="font-semibold">연동 관리</div>
              <button className="btn" onClick={() => setIntegrationsOpen(false)}>닫기</button>
            </div>
            <div className="p-5 space-y-4">
              <div className="rounded-xl border border-slate-200 bg-white/70 p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-black text-white text-[10px] grid place-items-center">IG</div>
                  <div>
                    <div className="font-semibold">Instagram</div>
                    <div className="text-xs text-slate-500">게시/댓글 자동 운영을 위해 계정을 연동하세요.</div>
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() => {
                    const url = `${API_BASE}/oauth/instagram/start`;
                    try {
                      window.location.href = url;
                    } catch {
                      alert("연동 준비 중입니다.");
                    }
                  }}
                >
                  인스타 연동 하기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function HeaderSummary({ credit, creditMax, personaName, personaImg, onOpenSelector, onOpenIntegrations, loadingPersona }) {
  const guideImg = "./img/fixed_face.png";
  const pct = Math.min(100, Math.round((credit / creditMax) * 100));
  return (
    <div className="rounded-3xl border border-slate-200 bg-white/80 backdrop-blur p-6 shadow-[0_10px_30px_rgba(30,64,175,0.08)]">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="relative w-50 h-50 rounded-full overflow-hidden border border-slate-200 bg-white">
            <img src={personaImg || guideImg} alt="" className="w-full h-full object-cover" />
            <span className="absolute -bottom-1 -right-1 inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200 text-[10px]">온라인</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <div className="text-xl font-bold">{personaName || (loadingPersona ? "로딩 중…" : "프로필 없음")}</div>
              <span className="inline-flex items-center px-2 py-0.5 text-[10px] rounded-full bg-blue-100 text-blue-700 border border-blue-200">검증됨</span>
            </div>
            <div className="text-sm text-slate-500">마이페이지에서 활동 프로필을 관리하세요.</div>
            <div className="mt-2 flex gap-6 text-sm">
              <Stat label="팔로워" value="0" />
              <Stat label="참여율" value="0%" />
              <Stat label="주간도달" value="0" />
            </div>
          </div>
        </div>

        <div className="w-full md:w-80">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>크레딧</span>
            <span>{credit} / {creditMax}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-blue-400 to-indigo-500" style={{ width: `${pct}%` }} />
          </div>
          <div className="mt-3 flex gap-2">
            <button className="btn primary grow" onClick={onOpenSelector}>프로필 교체하기</button>
            <button className="btn light" onClick={onOpenIntegrations}>연동관리</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="flex flex-col">
      <span className="text-slate-400 text-xs">{label}</span>
      <span className="font-semibold">{value}</span>
    </div>
  );
}

function ConnectRow({ logo, name, status, hint }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-full bg-black text-white text-[10px] flex items-center justify-center">{logo}</div>
        <div className="flex flex-col">
          <div className="text-slate-800 text-sm">{name}</div>
          <div className="text-[11px] text-slate-400">{hint}</div>
        </div>
      </div>
      <span className="text-[10px] px-2 py-0.5 rounded-full border bg-slate-100 text-slate-600 border-slate-200">{status}</span>
    </div>
  );
}

function Notice({ text, tone = "info" }) {
  const toneCls =
    tone === "warn"
      ? "bg-amber-50 text-amber-800 border-amber-200"
      : "bg-slate-50 text-slate-700 border-slate-200";
  return <div className={`text-sm rounded-xl px-3 py-2 border ${toneCls}`}>{text}</div>;
}

function TabButton({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 h-10 rounded-full text-sm ${active ? "bg-blue-600 text-white shadow" : "text-slate-600 hover:bg-slate-100"}`}
    >
      {label}
    </button>
  );
}

function Card({ children, className = "" }) {
  return (
    <div className={`rounded-3xl border border-slate-200 bg-white/80 backdrop-blur p-6 shadow-[0_10px_30px_rgba(30,64,175,0.08)] ${className}`}>
      {children}
    </div>
  );
}

function Empty({ title, action }) {
  return (
    <div className="py-16 text-center">
      <div className="mx-auto w-20 h-18.5 rounded-2xl bg-slate-100" />
      <div className="mt-4 text-slate-700 font-semibold">{title}</div>
      <button className="btn primary mt-4">{action}</button>
    </div>
  );
}

function badgeTone(s) {
  if (s === "발행") return "bg-emerald-100 text-emerald-700 border-emerald-200";
  if (s === "예약") return "bg-blue-100 text-blue-700 border-blue-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}
