// Imgcreate.jsx
import { useState, useMemo } from "react";
import guideImg from "../../img/fixed_face.png";
import { API_BASE } from "@/api/client";
import TypingText from "../components/TypingText";
import Field from "../components/Field";
import StyleTag from "../components/StyleTag";

/* ========================= Home ========================= */
function Home() {
  // 기본 필드
  const [name, setName] = useState("이빛나");
  const [gender, setGender] = useState("여");
  const [age, setAge] = useState(23);

  // 옵션(악세사리 등) — 현재 UI 미구현이므로 선택 값만 보유
  const [selected] = useState([]);

  // 성격 chips
  const personalityList = useMemo(
    () => ["활발함", "차분함", "상냥함", "도도함", "유머러스", "카리스마", "지적인", "우아한"],
    []
  );
  const [personalities, setPersonalities] = useState([]);

  // 얼굴 디테일 6종
  const [faceShape, setFaceShape] = useState(""); // 얼굴형
  const [skinTone, setSkinTone] = useState("");   // 피부톤
  const [hair, setHair] = useState("");           // 헤어
  const [eyes, setEyes] = useState("");           // 눈
  const [nose, setNose] = useState("");           // 코
  const [lips, setLips] = useState("");           // 입

  const [bodyType, setBodyType] = useState("");   // 체형
  const [glasses, setGlasses] = useState("");     // 안경 유무

  const faceShapes = ["계란형", "둥근형", "각진형", "하트형", "긴형"];
  const skinTones  = ["밝은 17~21호", "중간 21~23호", "따뜻한 23~25호", "태닝톤", "쿨톤"];
  const hairs      = ["스트레이트", "웨이브", "단발", "장발", "포니테일", "업스타일"];
  const eyeShapes  = ["크고 또렷함", "고양이상", "강아지상", "아치형", "처진눈매"];
  const noses      = ["오똑함", "버튼", "긴코", "작은코", "직선"];
  const lipTypes   = ["도톰", "얇음", "하트", "자연", "그라데"];
  const bodyTypes  = ["마름", "슬림", "보통", "통통", "근육질"];

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
    if (loading) return;              // ✅ CHANGED: 더블클릭 방지
    setGenerated(null);
    setError(null);
    setGeneratedUrl("");
    setStatus("");
    setLoading(true);

    // ✅ CHANGED: 문장 합치기(feature/featureCombined) 제거.
    // 사용자가 고른 값을 "그대로" 보낸다.
    const payload = {
      name,
      gender,
      age,                 // 숫자 그대로
      options: selected,   // 옵션 그대로
      faceShape,
      skinTone,
      hair,
      eyes,
      nose,
      lips,
      bodyType,
      glasses,
      personalities,       // 배열 그대로 (지금은 단일 선택이지만 구조 유지)
    };

    const MAX_RETRY = 2;
    for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
      try {
        setStatus(attempt === 1 ? "생성중…" : `다시 시도중… (${attempt}/${MAX_RETRY})`);
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 60_000);

        const res = await fetch(`${API_BASE}/api/images`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),  // ✅ CHANGED: 합친 문자열 대신 필드 그대로
          signal: controller.signal,
        });

        clearTimeout(t);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!data?.ok) throw new Error(data?.message || "generation failed");

        setGenerated(data.image);
        if (data.url) {
          const abs = `${API_BASE || ""}${data.url}`;
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

      <main className="mx-auto max-w-6xl px-4 py-6 md:py-8 min-h-screen">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 items-stretch">
          {/* 좌측 미리보기 카드 */}
          <section className="card overflow-hidden h-full">
            <div className="bg-black flex items-center justify-center">
              <div className="relative w-full max-w-[520px] aspect-square" aria-busy={loading} aria-live="polite">
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
                      if (generated && e.currentTarget.src !== generated) {
                        e.currentTarget.src = generated;
                      }
                    }}
                  />
                ) : (
                  <div className="absolute inset-0 bg-[radial-gradient(120%_80%_at_10%_0%,rgba(255,255,255,0.12),transparent_60%)] pointer-events-none" />
                )}
              </div>
            </div>
            <div className="p-4 bg-blue-50">
              <h3 className="text-xl md:text-2xl font-semibold mb-1 tracking-tight">나만의 인플루언서를 만들어보세요.</h3>
              <p className="text-xs md:text-sm text-slate-600">얼굴 ID를 고정할 때 일상과 바뀐 다양한 결과를 얻을 수 있습니다.</p>
            </div>
          </section>

          {/* 우측 입력 카드 */}
          <section className="rounded-2xl border border-blue-200 bg-blue-50/60 p-5 md:p-6 shadow-[0_20px_40px_rgba(30,64,175,0.08)] relative text-left h-full">
            {/* 말풍선 헤더 */}
            <div className="flex items-start gap-3 mb-4">
              <img src={guideImg} alt="guide" className="w-10 h-10 md:w-11 md:h-11 rounded-full object-cover border" />
              <div className="text-sm px-4 py-2 rounded-[14px] border border-blue-300 bg-white/70 shadow-[0_4px_12px_rgba(30,64,175,0.06)]">
                <TypingText text={"활동하실 인물을 생성해보세요."} />
              </div>
            </div>

            {/* 인플루언서 정보 */}
            <div className="mt-1 mb-1 text-base font-semibold">인플루언서 정보</div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="이름" compact>
                <input
                  className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="이빛나"
                />
              </Field>

              <Field label="성별" compact>
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

            {/* 나이 */}
            <div className="grid grid-cols-2 gap-4 mt-1">
              <Field label="나이" compact>
                <input
                  type="number"
                  min={20}
                  max={80}
                  className="w-full px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={age}
                  onChange={(e) => {
                    const v = Number(String(e.target.value).replace(/[^\d]/g, ""));
                    if (Number.isNaN(v)) return setAge("");
                    const clamped = Math.max(20, Math.min(80, v));
                    setAge(clamped);
                  }}
                  placeholder="예: 23"
                />
              </Field>

              <Field label="안경" compact>
                <div className="relative">
                  <select
                    className="w-full appearance-none px-4 py-2 rounded-lg border border-blue-200 bg-white/70 focus:outline-none focus:ring-2 focus:ring-blue-300"
                    value={glasses}
                    onChange={(e) => setGlasses(e.target.value)}
                  >
                    <option value="">선택</option>
                    <option value="없음">없음</option>
                    <option value="있음">있음</option>
                  </select>
                  <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-500">▾</span>
                </div>
              </Field>
            </div>

            {/* 얼굴 디테일 */}
            <div className="mt-1 mb-1 text-base font-semibold">얼굴 디테일</div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="얼굴형" compact>
                <Select value={faceShape} onChange={(e) => setFaceShape(e.target.value)}>
                  {faceShapes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="피부톤" compact>
                <Select value={skinTone} onChange={(e) => setSkinTone(e.target.value)}>
                  {skinTones.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="헤어" compact>
                <Select value={hair} onChange={(e) => setHair(e.target.value)}>
                  {hairs.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="눈" compact>
                <Select value={eyes} onChange={(e) => setEyes(e.target.value)}>
                  {eyeShapes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="코" compact>
                <Select value={nose} onChange={(e) => setNose(e.target.value)}>
                  {noses.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>

              <Field label="입" compact>
                <Select value={lips} onChange={(e) => setLips(e.target.value)}>
                  {lipTypes.map((v) => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              </Field>
            </div>

            {/* 체형 */}
            <div className="mt-3 mb-1 text-sm font-semibold">체형</div>
            <div className="grid grid-cols-5 gap-2 mb-3">
              {bodyTypes.map((p) => {
                const on = bodyType === p;
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setBodyType(on ? "" : p)}
                    className={"chip " + (on ? "chip-on" : "")}
                    aria-pressed={on}
                  >
                    {p}
                  </button>
                );
              })}
            </div>

            {/* 성격 */}
            <div className="mt-2 mb-1 text-sm font-semibold">
              성격 <span className="text-slate-400"></span>
            </div>
            <div className="grid grid-cols-4 gap-2 mb-3">
              {personalityList.map((p) => {
                const on = personalities.includes(p);
                return (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPersonalities(on ? [] : [p])} // single-select 유지
                    className={"chip " + (on ? "chip-on" : "")}
                    aria-pressed={on}
                  >
                    {p}
                  </button>
                );
              })}
            </div>

            {/* 버튼 */}
            <div className="flex justify-end gap-2 mt-4">
              <button
                className={`btn-outline ${loading ? "opacity-60 cursor-not-allowed" : ""}`}
                type="button"
                onClick={onGenerate}
                disabled={loading}
              >
                미리보기
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

export default Home;
