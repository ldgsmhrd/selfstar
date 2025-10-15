// Imgcreate.jsx
function Imgcreate() {
  return (
    <div>
      <h1>이미지 생성 페이지</h1>
      <p>여기에 이미지 생성 기능을 추가하세요.</p>
    </div>
  );
}

// App.jsx
import { useState, useEffect, useMemo, useRef, useCallback } from "react";
// Vite 기준: /src 아래 경로 import
import guideImg from "../../img/fixed_face.png";
import { API_BASE } from "@/api/client";

/* =============== 세션 사용자 훅 =============== */
function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const focusCooldownRef = useRef(0);

  const refresh = useCallback(async () => {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 8000);

    try {
      setLoading(true);
  const res = await fetch(`${API_BASE}/auth/me`, {
        method: "GET",
        credentials: "include",
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: ctrl.signal,
      });

      if (res.status === 401) {
        setUser(null);
        setError(null);
        return;
      }
      if (!res.ok) {
        setUser(null);
        setError(`서버 오류: HTTP ${res.status}`);
        return;
      }

      const data = await res.json();
      setUser(data.authenticated ? data.user : null);
      setError(null);
    } catch (err) {
      setUser(null);
      setError(err?.name === "AbortError" ? "요청 시간 초과" : (err?.message || "네트워크 오류"));
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
  const res = await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok || res.status === 204) {
        setUser(null);
        setError(null);
      } else {
        setError(`로그아웃 실패: HTTP ${res.status}`);
      }
    } catch (e) {
      setError(e?.message || "로그아웃 중 오류");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const onFocus = () => {
      const now = Date.now();
      if (now - focusCooldownRef.current < 3000) return;
      focusCooldownRef.current = now;
      refresh();
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refresh]);

  return { user, loading, error, refresh, logout, setUser };
}

/* ========================= 공통 Field 컴포넌트 ========================= */
function Field({ label, right, children }) {
  return (
    <div className="mb-4">
      {label && (
        <div className="mb-2 flex items-center justify-between">
          <label className="text-sm font-semibold text-slate-800">{label}</label>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

/* ========================= Home (스샷 스타일) ========================= */
function Home() {
  // 기본 필드
  const [name, setName] = useState("이빛나");
  const [gender, setGender] = useState("여");
  const [feature, setFeature] = useState("");

  // 옵션(악세사리 등) — 현재 UI 미구현이므로 선택 값만 보유
  const [selected] = useState([]);

  // 성격 chips
  const personalityList = useMemo(
    () => ["활발함", "차분함", "상냥함", "도도함", "유머러스", "카리스마", "지적인", "우아한"],
    []
  );
  const [personalities, setPersonalities] = useState([]);
  const togglePersonality = (p) =>
    setPersonalities((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]));

  // 얼굴 디테일 6종 (스샷 구조)
  const [faceShape, setFaceShape] = useState(""); // 얼굴형
  const [skinTone, setSkinTone] = useState("");   // 피부톤
  const [hair, setHair] = useState("");           // 헤어
  const [eyes, setEyes] = useState("");           // 눈
  const [nose, setNose] = useState("");           // 코
  const [lips, setLips] = useState("");           // 입

  const faceShapes = ["계란형", "둥근형", "각진형", "하트형", "긴형"];
  const skinTones  = ["밝은 17~21호", "중간 21~23호", "따뜻한 23~25호", "태닝톤", "쿨톤"];
  const hairs      = ["스트레이트", "웨이브", "단발", "장발", "포니테일", "업스타일"];
  const eyeShapes  = ["크고 또렷함", "고양이상", "강아지상", "아치형", "처진눈매"];
  const noses      = ["오똑함", "버튼", "긴코", "작은코", "직선"];
  const lipTypes   = ["도톰", "얇음", "하트", "자연", "그라데"];

  // 이미지 생성 상태
  const [generated, setGenerated] = useState(null);
  const [generatedUrl, setGeneratedUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("");

  // 공통 Select
  const Select = ({ value, onChange, children }) => (
    <div className="relative">
      <select
        className="w-full appearance-none px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
        value={value}
        onChange={onChange}
      >
        <option value="">선택</option>
        {children}
      </select>
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">▾</span>
    </div>
  );

  const onGenerate = async () => {
    setGenerated(null);
    setError(null);
    setGeneratedUrl("");
    setStatus("");
    setLoading(true);

    // 백엔드/AI가 단순 키로 이해하기 쉽게 플랫한 문장과 옵션으로 변환
    const detailSummary = [
      faceShape && `얼굴형:${faceShape}`,
      skinTone && `피부톤:${skinTone}`,
      hair && `헤어:${hair}`,
      eyes && `눈:${eyes}`,
      nose && `코:${nose}`,
      lips && `입:${lips}`,
    ]
      .filter(Boolean)
      .join(", ");

    const featureCombined = [feature, detailSummary, personalities.length ? `성격:${personalities.join('/')}` : ""]
      .filter(Boolean)
      .join(" | ");

    const payload = {
      name,
      gender,
      // keep original feature for backward compatibility
      feature: featureCombined,
      options: selected,
      // send detailed fields so backend can build richer prompt
      featureCombined,
      faceShape,
      skinTone,
      hair,
      eyes,
      nose,
      lips,
      personalities,
    };

    const MAX_RETRY = 2;
    for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
      try {
        setStatus(attempt === 1 ? "생성중…" : `다시 시도중… (${attempt}/${MAX_RETRY})`);
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 60_000);
  const res = await fetch(`${API_BASE}/api/image/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),
          signal: controller.signal,
        });
        clearTimeout(t);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!data?.ok) throw new Error(data?.message || "generation failed");
        setGenerated(data.image);
        if (data.url) {
          // 백엔드가 반환한 /media 상대 경로를 절대 경로로 보정(API_BASE는 '' 또는 'http://localhost:8000')
          const abs = `${API_BASE || ''}${data.url}`;
          setGeneratedUrl(abs);
        }
        setStatus("");
        break;
      } catch (e) {
        if (attempt === MAX_RETRY) {
          setError(`이미지 생성 실패: ${e?.name === "AbortError" ? "요청 시간 초과" : (e?.message || e)}`);
          setStatus("에러");
        } else {
          setStatus(`에러, 다시 시도중… (${attempt + 1}/${MAX_RETRY})`);
          await new Promise((r) => setTimeout(r, 1200));
        }
      }
    }
    setLoading(false);
  };

  return (
    <>
      <StyleTag />

      <main className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
          {/* 좌측 미리보기 카드 */}
          <section className="card overflow-hidden">
            <div className="bg-black flex items-center justify-center">
              <div className="relative w-[520px] h-[520px]" aria-busy={loading} aria-live="polite">
                {loading ? (
                  <div className="absolute inset-0 flex items-center justify-center text-blue-200">
                    <span className="animate-pulse">{status || "생성중…"}</span>
                  </div>
                ) : (generatedUrl || generated) ? (
                  <img
                    src={generatedUrl || generated}
                    alt="generated"
                    className="absolute inset-0 w-full h-full object-contain"
                    onError={(e) => {
                      // If /media URL fails (404/CORS), fall back to inline data URI
                      if (generated && e.currentTarget.src !== generated) {
                        e.currentTarget.src = generated
                      }
                    }}
                  />
                ) : (
                  <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_10%_0%,rgba(255,255,255,0.12),transparent_60%)] pointer-events-none" />
                )}
              </div>
            </div>
            <div className="p-5 bg-blue-50">
              <h3 className="text-2xl font-semibold mb-1 tracking-tight">
                나만의 인플루언서를 만들어보세요.
              </h3>
              <p className="text-sm text-slate-600">
                얼굴 ID를 고정할 때 일상과 바뀐 다양한 결과를 얻을 수 있습니다.
              </p>
            </div>
          </section>

          {/* 우측 입력 카드 (스샷 레이아웃) */}
          <section className="rounded-2xl border border-blue-200 bg-blue-50/60 p-6 shadow-[0_20px_40px_rgba(30,64,175,0.08)] relative w-[520px] text-left">
            {/* 말풍선 헤더 */}
            <div className="flex items-start gap-3 mb-5">
              <img src={guideImg} alt="guide" className="w-11 h-11 rounded-full object-cover border" />
              <div className="text-sm px-4 py-2 rounded-[14px] border border-blue-300 bg-white/70 shadow-[0_4px_12px_rgba(30,64,175,0.06)]">
                활동하실 인물을 생성해보세요.
              </div>
            </div>

            {/* 이름/성별 2컬럼 */}
            <div className="grid grid-cols-2 gap-6">
              <Field label="이름">
                <input
                  className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="이빛나"
                />
              </Field>

              <Field label="성별">
                <div className="relative">
                  <select
                    className="w-full appearance-none px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                  >
                    <option>여</option>
                    <option>남</option>
                  </select>
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">▾</span>
                </div>
              </Field>
            </div>

            {/* 얼굴 디테일 */}
            <div className="mt-2 mb-1 text-sm font-semibold">얼굴 디테일</div>
            <div className="grid grid-cols-2 gap-6">
              <Field label="얼굴형">
                <Select value={faceShape} onChange={(e) => setFaceShape(e.target.value)}>
                  {faceShapes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="피부톤">
                <Select value={skinTone} onChange={(e) => setSkinTone(e.target.value)}>
                  {skinTones.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="헤어">
                <Select value={hair} onChange={(e) => setHair(e.target.value)}>
                  {hairs.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="눈">
                <Select value={eyes} onChange={(e) => setEyes(e.target.value)}>
                  {eyeShapes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="코">
                <Select value={nose} onChange={(e) => setNose(e.target.value)}>
                  {noses.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="입">
                <Select value={lips} onChange={(e) => setLips(e.target.value)}>
                  {lipTypes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>
            </div>

            {/* 성격 */}
            <div className="mt-2 mb-1 text-sm font-semibold">성격 <span className="text-slate-400">· 중복 선택</span></div>
            <div className="flex flex-wrap gap-3 mb-4">
              {personalityList.map((p) => {
                const on = personalities.includes(p);
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => togglePersonality(p)}
                    className={"chip " + (on ? "border-blue-400 bg-white text-blue-700 shadow-sm" : "")}
                    aria-pressed={on}
                  >
                    {p}
                  </button>
                );
              })}
            </div>

            {/* 특징 한 줄 */}
            <div className="mb-2 text-sm font-semibold">
              특징 <span className="text-slate-400">· 인플루언서의 특징을 작성해주세요.</span>
            </div>
            <Field>
              <input
                className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-white/70 placeholder:text-blue-500/80 focus:outline-none focus:ring-2 focus:ring-blue-300"
                value={feature}
                onChange={(e) => setFeature(e.target.value)}
                placeholder="ex) 귀여운 이미지"
              />
            </Field>

            {/* 버튼 두 개 (우측 정렬) */}
            <div className="flex justify-end gap-3 mt-6">
              <button
                className={`btn-outline ${loading ? "opacity-60 cursor-not-allowed" : ""}`}
                type="button"
                onClick={onGenerate}
                disabled={loading}
              >
                인플루언서 생성
              </button>
              <button
                className={`btn-primary ${loading ? "opacity-60 cursor-not-allowed" : ""}`}
                onClick={onGenerate}
                disabled={loading}
              >
                {loading ? "생성중…" : "인플루언서 확정"}
              </button>
            </div>

            {error && <p className="mt-3 text-sm text-red-600" role="alert">{error}</p>}
          </section>
        </div>
      </main>
    </>
  );
}

/* ========================= 전역 스타일(컴포넌트 안에 주입) ========================= */
function StyleTag() {
  return (
    <style>{`
      /* 카드/버튼/칩 — Tailwind 없이도 보이도록 보조 */
      .card{
        border-radius: 16px;
        border: 1px solid #cfe3fb;
        background: #0b1020;
        box-shadow: 0 20px 40px rgba(30,64,175,.10);
      }
      .btn-primary{
        white-space:nowrap;
        padding: 10px 16px;
        border-radius: 12px;
        border: 1px solid transparent;
        background: linear-gradient(180deg,#5ea3ff,#2d6cdf);
        color: #fff;
        font-weight: 700;
        box-shadow: 0 14px 28px rgba(45,108,223,.22);
      }
      .btn-outline{
        white-space:nowrap;
        padding: 10px 16px;
        border-radius: 12px;
        border: 1px solid #cfe3fb;
        background: #fff;
        color: #0f1d2b;
        font-weight: 700;
      }
      .chip{
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid #cfe3fb;
        background: #f2f8ff;
        color: #0f1d2b;
        font-weight: 600;
        transition: transform .06s ease, box-shadow .12s ease;
      }
      .chip:hover{ transform: translateY(-1px); box-shadow: 0 8px 16px rgba(45,108,223,.12); }
    `}</style>
  );
}

export default function App() {
  // 인증 훅은 여기서 사용할 수 있음
  useAuth(); // 필요 없으면 제거 가능
  return <Home />;
}
