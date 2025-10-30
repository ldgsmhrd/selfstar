import React from "react";

const CheckIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
    <path d="M20 6L9 17l-5-5" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const IconBubble = () => (
  <div className="w-10 h-10 rounded-md bg-blue-50 grid place-items-center text-blue-600">
    💬
  </div>
);
const IconSparkle = () => (
  <div className="w-10 h-10 rounded-md bg-yellow-50 grid place-items-center text-yellow-500">
    ✨
  </div>
);
const IconTag = () => (
  <div className="w-10 h-10 rounded-md bg-pink-50 grid place-items-center text-pink-600">
    🏷️
  </div>
);

function PlanCard({ Icon, title, subtitle, price, priceUnit, description, features = [], featured, cta }) {
  return (
    <article
      className={
        "rounded-2xl border p-6 shadow-sm transition-transform transform hover:scale-[1.03] " +
        (featured ? "border-blue-100 bg-white" : "bg-white")
      }
    >
      <div className="flex items-start gap-4">
        <Icon />
        <div>
          <div className="flex items-baseline gap-2">
            <h3 className="text-lg font-extrabold">{title}</h3>
            {subtitle && <div className="text-sm text-slate-500">{subtitle}</div>}
          </div>
          <div className="mt-3 flex items-end gap-3">
            <div className="text-3xl font-bold">{price}</div>
            <div className="text-sm text-slate-500">{priceUnit}</div>
          </div>
        </div>
      </div>

      {description && <p className="mt-4 text-sm text-slate-600">{description}</p>}

      <ul className="mt-5 space-y-2">
        {features.map((f, i) => (
          <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
            <span className="mt-1"><CheckIcon /></span>
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6">
        <a
          href={cta?.href || '#'}
          className={
            "inline-block px-4 py-2 rounded-lg font-semibold text-sm " +
            (cta?.primary ? "bg-blue-600 text-white" : "border border-slate-200 text-slate-700 bg-white")
          }
        >
          {cta?.label || "선택"}
        </a>
      </div>
    </article>
  );
}

export default function CreditPlans() {
  const plans = [
    {
      title: "무료",
      subtitle: "체험용",
      price: "0원",
      priceUnit: "영구",
      description: "가입 즉시 사용 가능한 기본 크레딧과 기능",
      Icon: IconBubble,
      features: [
        "기본 크레딧 제공, 일일 생성 한도",
        "커뮤니티 피드 기능 사용 가능",
        "이미지 업로드 및 편집 기능 일부 제공",
      ],
      cta: { label: "시작하기 (무료)", href: "/signup", primary: true },
    },
    {
      title: "프로",
      subtitle: "크리에이터용",
      price: "₩9,900",
      priceUnit: "/월",
      description: "더 많은 크레딧과 고급 기능으로 활동을 확장하세요.",
      Icon: IconSparkle,
      features: [
        "추가 크레딧 월별 제공, 우선 처리",
        "고해상도 이미지 생성 및 빠른 큐",
        "상업적 이용 가능, API 호출 제한 상향",
      ],
      cta: { label: "구독하기", href: "/signup", primary: true },
      featured: true,
    },
    {
      title: "비즈니스",
      subtitle: "팀/기업용",
      price: "문의",
      priceUnit: "",
      description: "대규모 사용을 위한 전용 요금제 및 SLA 제공",
      Icon: IconTag,
      features: [
        "전용 크레딧 패키지, 엔터프라이즈 지원",
        "팀 관리, 사용자/권한 통합",
        "전용 API 및 SLA 계약 가능",
      ],
      cta: { label: "문의하기", href: "/", primary: false },
    },
  ];

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-extrabold">SelfStar.AI 크레딧/요금제</h1>
        <p className="text-sm text-slate-500 mt-2">필요한 플랜을 선택하고 즉시 시작하세요.</p>
      </header>

      <section className="grid md:grid-cols-3 gap-6">
        {plans.map((p) => (
          <PlanCard key={p.title} {...p} />
        ))}
      </section>
    </div>
  );
}
