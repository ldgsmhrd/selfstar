// Imgcreate.jsx
import { useState, useMemo } from "react";
import guideImg from "../../img/fixed_face.png";
import { API_BASE } from "@/api/client";
import TypingText from "../components/TypingText";
import Field from "../components/Field";
import StyleTag from "../components/StyleTag";

/* ========================= Home ========================= */
function Home({ compact = false }) {
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
  const [lastPayload, setLastPayload] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  // 확정 버튼 활성화 여부: 인플루언서 정보(이름/성별/나이/안경) + 얼굴 디테일(6종) 모두 선택 시에만 활성화
  const isInfoReady = Boolean(String(name || "").trim()) && Boolean(gender) && Boolean(age) && Boolean(glasses);
  const isFaceReady = Boolean(faceShape) && Boolean(skinTone) && Boolean(hair) && Boolean(eyes) && Boolean(nose) && Boolean(lips);
  const isBodyReady = Boolean(bodyType) && (Array.isArray(personalities) && personalities.length > 0);
  const isConfirmReady = isInfoReady && isFaceReady && isBodyReady;

  // 현재 입력 상태로부터 payload 스냅샷
  const currentPayload = useMemo(
    () => ({
      name,
      gender,
      age,
      options: selected,
      faceShape,
      skinTone,
      hair,
      eyes,
      nose,
      lips,
      bodyType,
      glasses,
      personalities,
    }),
    [
      name,
      gender,
      age,
      selected,
      faceShape,
      skinTone,
      hair,
      eyes,
      nose,
      lips,
      bodyType,
      glasses,
      personalities,
    ],
  );

  // 마지막 생성 이후로 입력이 변경되었는지
  const isDirty = useMemo(() => {
    if (!lastPayload) return true;
    try {
      return JSON.stringify(currentPayload) !== JSON.stringify(lastPayload);
    } catch {
      return true;
    }
  }, [currentPayload, lastPayload]);

  // 버튼 가능 조건
  const canGenerate = isConfirmReady && (!generated || isDirty);
  const canConfirm = isConfirmReady && Boolean(generated) && !isDirty;

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
    const payload = currentPayload;

    const MAX_RETRY = 2;
    for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
      try {
        setStatus(attempt === 1 ? "생성중…" : `다시 시도중… (${attempt}/${MAX_RETRY})`);
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 60_000);

        const res = await fetch(`${API_BASE}/api/images/preview`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),  // 필드 그대로
          signal: controller.signal,
        });

        clearTimeout(t);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!data?.ok) throw new Error(data?.message || "generation failed");

        // 미리보기: 저장하지 않고 data URI만 세팅
        setGenerated(data.image);
        setGeneratedUrl("");
        setLastPayload(payload);
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

  // 성별 변환 및 생년월일 계산 (나이 기준 단순 변환: 해당 연도의 1월 1일)
  const mapGender = (g) => (g === "남" ? "남성" : "여성");
  const birthdayFromAge = (a) => {
    const n = Number(a);
    if (!Number.isFinite(n) || n <= 0 || n > 120) return null;
    const today = new Date();
    const year = today.getFullYear() - n;
    return `${year}-01-01`;
  };

  const doSaveProfile = async () => {
    if (saving) return;
    // 나이 -> 생년월일, 성별 매핑
    const bday = birthdayFromAge(age);
    const mappedGender = mapGender(gender);
    if (!bday) {
      setError("유효한 나이를 입력해주세요.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/users/me/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ birthday: bday, gender: mappedGender }),
      });
      if (res.status === 401) throw new Error("로그인이 필요합니다.");
      if (!res.ok) throw new Error(`프로필 저장 실패: ${res.status}`);
      const data = await res.json();
      if (!data?.ok) throw new Error(data?.message || "프로필 저장 실패");
      setStatus("프로필 저장 완료");
      // 저장 완료 후, 상위(App)에게 프로필 선택 모달 열도록 신호
      try {
        window.dispatchEvent(new CustomEvent("open-profile-select"));
      } catch {
        // no-op: dispatch might fail in non-browser environments
      }
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <StyleTag />

  <main className={compact ? "mx-auto max-w-6xl p-4" : "mx-auto max-w-6xl px-4 py-6 md:py-8 min-h-screen"}>
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

            {/* 인스타 핸들 입력 제거 (기본 null 저장) */}

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
                className={`${canGenerate ? "btn-primary" : "btn-outline"} ${(loading || !canGenerate) ? "opacity-60 cursor-not-allowed" : ""}`}
                type="button"
                onClick={onGenerate}
                disabled={loading || !canGenerate}
              >
                이미지 생성
              </button>
              <button
                className={`${canConfirm ? "btn-primary" : "btn-outline"} ${((loading || saving) || !canConfirm) ? "opacity-60 cursor-not-allowed" : ""}`}
                onClick={() => {
                  if (!canConfirm || loading || saving) return;
                  if (!generated || !lastPayload) {
                    setError("먼저 이미지를 생성하세요.");
                    return;
                  }
                  setConfirmOpen(true);
                }}
                disabled={(loading || saving) || !canConfirm}
              >
                {saving ? "저장중…" : "프로필 저장"}
              </button>
            </div>

            {error && <p className="mt-3 text-sm text-red-600" role="alert">{error}</p>}
          </section>
        </div>
      </main>

      {/* 확인 모달: 프로필 저장 전에 한번 더 묻기 */}
      {confirmOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 grid place-items-center bg-[rgba(15,23,42,0.45)] p-4"
          onClick={() => setConfirmOpen(false)}
        >
          <div
            className="relative w-[min(420px,94vw)] rounded-2xl border border-blue-200 bg-white p-5 shadow-[0_30px_70px_rgba(2,6,23,.35)]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              aria-label="닫기"
              onClick={() => setConfirmOpen(false)}
              className="absolute top-2.5 right-3 w-8 h-8 rounded-full border bg-white shadow"
            >
              ×
            </button>
            <h3 className="text-lg font-bold mb-1">저장 하시겠습니까?</h3>
            <p className="text-sm text-slate-600">입력하신 성별/생년월일 정보가 프로필에 저장됩니다.</p>
            <div className="flex justify-end gap-2 mt-4">
              <button className="btn-outline" onClick={() => setConfirmOpen(false)}>아니요</button>
              <button
                className="btn-primary disabled:opacity-60"
                disabled={saving}
                onClick={async () => {
                  await doSaveProfile();
                  setConfirmOpen(false);
                }}
              >
                {saving ? "저장중…" : "저장"}
              </button>
            </div>
          </div>
        </div>
      )}

    </>
  );
}

export default Home;
