import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

export default function MyPage() {
  const [tab, setTab] = useState("posts");
  const [todos, setTodos] = useState([
    { id: 1, text: "프로필 소개 업데이트", done: false },
    { id: 2, text: "인스타 연동 확인", done: false },
    { id: 3, text: "샘플 사진 5장 업로드", done: false },
  ]);
  const credit = 0;
  const creditMax = 100;

  const posts = useMemo(
    () => [
      { id: "post1", title: "게시물을 올려주세요.", date: "게시물 올린 날짜", channel: "플랫폼", status: "작성" },
    ],
    []
  );

  return (
    <main className="w-full min-h-screen bg-[#eaf5ff]">
      <div className="mx-auto max-w-6xl px-6 py-7">
        <HeaderSummary credit={credit} creditMax={creditMax} />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-6">
          <aside className="lg:col-span-4 space-y-6">
            <Card>
              <div className="text-sm text-slate-500">SNS 연동</div>
              <div className="mt-4 space-y-4">
                <ConnectRow logo="IG" name="Instagram" status="미연동" hint="연동해주세요!" />
                <ConnectRow logo="Th" name="Threads" status="미연동" hint="연동해주세요!" />
              </div>
            </Card>

            <Card>
              <div className="text-sm text-slate-500">오늘의 할 일</div>
              <ul className="mt-3 space-y-2">
                {todos.map((t) => (
                  <li key={t.id} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={t.done}
                      onChange={() =>
                        setTodos(todos.map((x) => (x.id === t.id ? { ...x, done: !x.done } : x)))
                      }
                      className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-400"
                    />
                    <span className={t.done ? "line-through text-slate-400" : ""}>{t.text}</span>
                  </li>
                ))}
              </ul>
              <button
                className="btn light mt-3 w-full"
                onClick={() =>
                  setTodos((prev) => prev.concat({ id: Date.now(), text: "새 할 일", done: false }))
                }
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
    </main>
  );
}

function HeaderSummary({ credit, creditMax }) {
  const guideImg = "./img/fixed_face.png";
  const pct = Math.min(100, Math.round((credit / creditMax) * 100));
  return (
    <div className="rounded-3xl border border-slate-200 bg-white/80 backdrop-blur p-6 shadow-[0_10px_30px_rgba(30,64,175,0.08)]">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="relative w-50 h-50 rounded-full overflow-hidden border border-slate-200 bg-white">
            <img src={guideImg} alt="" className="w-full h-full object-cover" />
            <span className="absolute -bottom-1 -right-1 inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200 text-[10px]">온라인</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <div className="text-xl font-bold">이빛나</div>
              <span className="inline-flex items-center px-2 py-0.5 text-[10px] rounded-full bg-blue-100 text-blue-700 border border-blue-200">검증됨</span>
            </div>
            <div className="text-sm text-slate-500">연동해주세요!</div>
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
            <button className="btn primary grow">크레딧 충전</button>
            <Link to="/setup" className="btn light">연동관리</Link>
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
