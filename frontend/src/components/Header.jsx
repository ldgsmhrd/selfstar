import React from "react";
import { Link, useLocation } from "react-router-dom";

export default function Header() {
  const { pathname } = useLocation();
  const isSignup = pathname.startsWith("/signup");

  const handleLogout = async () => {
    try {
      await fetch("/auth/logout", { method: "POST" });
    } catch {
      // ignore
    } finally {
      window.location.href = "/signup";
    }
  };

  return (
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/" className="font-bold tracking-tight text-slate-900">
            <span className="text-blue-600">SelfStar</span>.AI
          </Link>
          {/* debug: show current path */}
          <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
            {pathname || "/"}
          </span>
        </div>

        <nav className="flex items-center gap-3 text-sm">
          <Link
            to="/setup"
            className="inline-flex h-9 items-center rounded-xl border border-slate-300 bg-white/90 px-3 font-medium text-slate-700 hover:bg-slate-50"
          >
            사용자 설정
          </Link>
          {!isSignup ? (
            <Link
              to="/signup"
              className="inline-flex h-9 items-center rounded-xl border border-slate-300 bg-white/90 px-3 font-medium text-slate-700 hover:bg-slate-50"
            >
              회원가입 / 로그인
            </Link>
          ) : (
            <Link
              to="/"
              className="inline-flex h-9 items-center rounded-xl border border-slate-300 bg-white/90 px-3 font-medium text-slate-700 hover:bg-slate-50"
            >
              홈으로
            </Link>
          )}
          <button
            onClick={handleLogout}
            className="inline-flex h-9 items-center rounded-xl border border-slate-300 bg-white/90 px-3 font-medium text-slate-700 hover:bg-slate-50"
            type="button"
          >
            로그아웃
          </button>
        </nav>
      </div>
    </header>
  );
}
