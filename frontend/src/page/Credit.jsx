import React from "react";

// Page-specific CSS + simple entrance animation
const pageCss = `
  .credit-hero { text-align:center; }
  .credit-hero .title { font-weight:900; line-height:1; }
  .credit-hero .subtitle { color: #64748b; margin-top:8px; }

  @keyframes fadeSlideUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:none; } }
  .fade-slide-up { opacity:0; transform:translateY(12px); animation: fadeSlideUp 480ms cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--delay, 0ms); }
`;

/* ------------------ Icons ------------------ */
function IconBubble({ className = 'w-6 h-6' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path d="M3 8c0-3 3-5 7-5s7 2 7 5-3 5-7 5c-.7 0-1.4-.07-2-.21L3 18l1-4.5C3.4 12.2 3 10.2 3 8z" fill="currentColor" opacity="0.12" />
      <path d="M7.5 10.5c-1.2 0-2.2-.9-2.2-2s1-2 2.2-2 2.2.9 2.2 2-1 2-2.2 2z" fill="currentColor" />
    </svg>
  );
}

function IconSparkle({ className = 'w-6 h-6' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2l1.8 3.6L17 7l-3.2 1.4L12 12l-1.8-3.6L7 7l3.2-1.4L12 2z" fill="currentColor" opacity="0.95" />
      <path d="M5 14l1 2 2 .6-2 .6-1 2-1-2-2-.6 2-.6 1-2z" fill="currentColor" opacity="0.2" />
    </svg>
  );
}

function IconTag({ className = 'w-6 h-6' }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path d="M2 12l10 10 10-10-9-9L2 12z" fill="currentColor" opacity="0.08" />
      <circle cx="7.5" cy="9.5" r="1.5" fill="currentColor" />
    </svg>
  );
}

function CheckIcon({ className = 'w-3 h-3' }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <path d="M4.5 10.5l3 3 8-8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ------------------ PlanCard ------------------ */
function PlanCard({
  Icon,
  title,
  subtitle,
  price,
  desc,
  features = [],
  featured,
  buttonText,
  buttonPrimary,
  footerNote,
  delay = 0,
}) {
  const isPro = Boolean(featured);
  const isBusiness = title && title.includes("비즈니스");

  const outerClass =
    isBusiness
      ? "bg-white border border-slate-200 text-slate-900 shadow-md rounded-3xl"
      : "bg-white border border-slate-100 text-slate-900 shadow-md rounded-3xl";

  const hoverFree =
    "hover:bg-linear-to-r hover:from-emerald-400 hover:to-emerald-600 hover:shadow-2xl hover:text-white hover:scale-105 hover:-translate-y-1";
  const hoverPro =
    "hover:bg-linear-to-r hover:from-sky-500 hover:to-violet-600 hover:shadow-2xl hover:text-white hover:scale-105 hover:-translate-y-1";
  const hoverBiz =
    "hover:bg-linear-to-r hover:from-indigo-400 hover:to-indigo-600 hover:shadow-2xl hover:text-white hover:scale-105 hover:-translate-y-1";

  const finalOuter = isPro ? `${outerClass} ${hoverPro}` : isBusiness ? `${outerClass} ${hoverBiz}` : `${outerClass} ${hoverFree}`;

  const btnClass = buttonPrimary
    ? "bg-sky-600 text-white font-semibold shadow hover:brightness-95"
    : "border border-slate-200 text-slate-900 hover:bg-slate-50";

  const featureTextClass = "text-slate-700 group-hover:text-white/95";

  return (
    <article
      className={`relative rounded-2xl overflow-hidden group ${finalOuter} transition-all duration-300 ease-out h-full flex flex-col fade-slide-up`}
      style={{ ['--delay']: `${delay}ms` }}
    >
      <div className="relative p-8 flex-1 flex flex-col">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg grid place-items-center bg-slate-100 text-sky-600 group-hover:bg-white/10 group-hover:text-white">
            {Icon ? <Icon className="w-6 h-6" /> : <span className="text-xl">{title?.[0]}</span>}
          </div>
          <div>
            <h3 className="font-bold text-lg text-slate-900 group-hover:text-white">{title}</h3>
            <p className="text-sm text-slate-500 group-hover:text-white/90">{subtitle}</p>
          </div>
        </div>

        <div className="mt-4 rounded-xl px-4 py-4 flex items-baseline justify-between bg-white/10">
          <div>
            <div className="text-3xl font-extrabold text-sky-600 group-hover:text-white">{price}</div>
            {String(price) && !/상담|문의/i.test(String(price)) ? (
              <div className="text-xs text-slate-500 group-hover:text-white/90">/월 · 부가세 별도</div>
            ) : null}
          </div>
          <div className="text-right max-w-[40%]">
            <div className="text-sm text-slate-500 group-hover:text-white/90 wrap-break-word">{desc}</div>
          </div>
        </div>

        <div className="mt-5 flex-1 overflow-hidden">
          <ul className="grid grid-cols-1 sm:grid-cols-1 gap-3 h-full overflow-auto pr-2">
            {features.map((f, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className={`${isBusiness ? "bg-indigo-50 text-indigo-700" : "bg-emerald-100 text-emerald-700"} mt-1 w-7 h-7 rounded-full flex items-center justify-center group-hover:bg-white/20 group-hover:text-white`}>
                  <CheckIcon className="w-3 h-3" />
                </span>
                <div className={`${featureTextClass} text-sm wrap-break-word`}>{f}</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-6">
          <button className={`w-full ${btnClass} py-3 rounded-full focus:outline-none focus:ring-4 focus:ring-sky-300`}>
            {buttonText}
          </button>
          {footerNote && <p className="mt-3 text-center text-xs text-slate-400">{footerNote}</p>}
        </div>
      </div>
    </article>
  );
}

/* ------------------ Main Page ------------------ */
export default function CreditPlans() {
  return (
    <div className="w-full min-h-screen text-slate-900 flex flex-col bg-[#eaf6ff] relative">
      <style>{pageCss}</style>
      <main className="w-full py-8">
        {/* Decorative background blobs */}
  <div className="pointer-events-none absolute -left-20 -top-20 w-72 h-72 bg-linear-to-r from-blue-200/40 to-indigo-200/30 rounded-full blur-3xl opacity-70" />
  <div className="pointer-events-none absolute right-6 top-24 w-64 h-64 bg-linear-to-r from-rose-100/30 to-indigo-100/20 rounded-full blur-3xl opacity-60" />

        <div className="relative mx-auto max-w-6xl px-6 py-12">
          <header className="credit-hero text-center mb-6">
            <h1 className="title text-4xl md:text-5xl lg:text-6xl tracking-tight bg-linear-to-r from-sky-600 to-indigo-600 bg-clip-text text-transparent">
              SelfStar.AI 크레딧/요금제
            </h1>
            <p className="subtitle mt-3 text-sm max-w-2xl mx-auto">
              AI 이미지 생성과 운영 자동화를 손쉽게 시작하세요.
            </p>
          </header>

          <section aria-label="요금제 목록" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 items-start">
            <PlanCard
              Icon={IconBubble}
              title="무료"
              subtitle="개인 테스트용"
              price="₩0"
              desc="가볍게 시작해 보세요"
              features={[
                "하루 5장 이미지 생성 (AI 이미지 API)",
                "생성 이미지에 워터마크 포함",
                "페르소나 최대 2개",
                "간단 템플릿, 예약 게시 5건/월",
                "Instagram 수동 업로드 지원",
              ]}
                buttonText="이용 중"
              delay={80}
              footerNote="카드 정보 불필요"
            />

            <PlanCard
              Icon={IconSparkle}
              title="프로"
              subtitle="크리에이터 · 소상공인 추천"
              price="₩15,900"
              desc="가장 많은 사용자에게 추천되는 요금제"
              featured
              features={[
                "높은 생성량, 빠른 처리 우선순위",
                "워터마크 제거, 상업적 사용 가능",
                "페르소나 최대 4개, 브랜드 키트",
                "예약 게시 무제한, Instagram 자동 업로드",
                "API 액세스",
              ]}
              buttonText="프로로 업그레이드"
              delay={160}
              buttonPrimary
            />

            <PlanCard
              Icon={IconTag}
              title="비즈니스"
              subtitle="팀 · 브랜드 운영"
              desc="대량 운영과 협업에 최적화된 옵션"
              features={[
                "팀 시트 3석 포함, 권한 관리",
                "무제한 생성량, 전용 처리 큐",
                "댓글 알림/응답 자동화, 운영 대시보드",
                "전용 API/웹훅 우선도, SLA 옵션",
                "전담 온보딩, 캠페인 컨설팅",
              ]}
              price="상담 요청"
              buttonText="상담 요청"
              delay={240}
              footerNote="필요 시 맞춤 견적 제공"
            />
          </section>
        </div>
      </main>
    </div>
  );
}
