// components/WelcomeIntro.jsx
import React from "react";

export default function WelcomeIntro({ onStart, startHref = "/signup" }) {
  // 스타일을 컴포넌트 내부에만 적용 (body는 건드리지 않음)
  const css = `
    :root{ --brand:#4DA3FF; --text:#111827; --muted:#9CA3AF; }
    .intro-wrap{
      min-height:100vh; width:100%;
      background:#ffffff;  /* 요청한 화이트 배경 */
      display:flex; flex-direction:column; align-items:center; justify-content:center;
      gap:28px; padding:72px 16px 120px; text-align:center;
    }
    .intro-title{
      margin:0; font-size:clamp(28px,6.8vw,72px); line-height:1.08;
      font-weight:900; color:#b3b7be; letter-spacing:.3px;
    }
    .intro-title .brand{ color:var(--brand); }
    .intro-sub{ margin-top:8px; font-size:clamp(16px,3.2vw,32px); font-weight:900; color:#aab0b7; }
    .intro-start{ margin-top:26px; font-size:clamp(18px,2.8vw,32px); font-weight:900; color:#aab0b7; text-decoration:none; user-select:none; cursor:pointer; }
    .scroll{ position:fixed; left:50%; bottom:22px; transform:translateX(-50%); text-align:center; color:#9FA6B2; font-size:12px; letter-spacing:.2px; }
    .mouse{ width:26px; height:42px; margin:8px auto 0; border:2px solid #c9ced6; border-radius:18px; display:flex; justify-content:center; }
    .wheel{ width:4px; height:8px; margin-top:6px; border-radius:2px; background:#c9ced6; animation:wheel 1.8s ease-in-out infinite; }
    @keyframes wheel{ 0%{transform:translateY(0)} 50%{transform:translateY(12px)} 100%{transform:translateY(0)} }
  `;

  const handleClick = (e) => {
    if (onStart) {
      e.preventDefault();
      onStart(); // 상위(App)에서 팝오버 열기 등 처리
    }
  };

  return (
    <>
      <style>{css}</style>
      <main className="intro-wrap" aria-label="인트로">
        <h1 className="intro-title">
          <span className="brand">SelfStar</span>에 오신 것을 환영합니다.
        </h1>
        <div className="intro-sub">인물을 생성하여 활동을 시작해보세요.</div>

        <a className="intro-start" href={startHref} onClick={handleClick}>
          시작하기
        </a>
      </main>

      <div className="scroll" aria-hidden="true">
        스크롤을 내려보세요.
        <div className="mouse"><div className="wheel" /></div>
      </div>
    </>
  );
}
