import React from "react";

function StyleTag() {
  return (
    <style>{`
      /* 카드/버튼/칩 — Tailwind 없이도 보이도록 보조 */
      .card{
        border-radius: 16px;
        border: 1px solid #cfe3fb;
        background: linear-gradient(135deg, #D4E7FC, #EAF5FE);
        box-shadow: 0 20px 40px rgba(30,64,175,.12);
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
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding: 10px 16px; /* 여백 확대 */
        min-height: 40px;   /* 높이 확대 */
        min-width: 92px;    /* 통일된 최소 너비 소폭 확대 */
        border-radius: 999px;
        border: 1px solid #cfe3fb;
        background: #f2f8ff;
        color: #0f1d2b;
        font-weight: 600;
        transition: transform .06s ease, box-shadow .12s ease;
      }
      .chip:hover{ transform: translateY(-1px); box-shadow: 0 8px 16px rgba(45,108,223,.12); }
      /* 활성화된 칩은 기본 칩 스타일을 덮어써서 기본 버튼(인플루언서 확정)과 동일 톤 */
      .chip.chip-on{
        border-color: transparent;
        background: linear-gradient(180deg,#5ea3ff,#2d6cdf);
        color: #fff;
        box-shadow: 0 14px 28px rgba(45,108,223,.22);
      }
      .chip.chip-on:hover{ box-shadow: 0 18px 34px rgba(45,108,223,.28); transform: translateY(-1px); }

      /* 칩 행을 항상 왼쪽 정렬로 강제 (마지막 줄도 좌측 정렬) */
      .chip-row-left{ display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-start !important; align-items:flex-start; }

      /* grid 기반 왼쪽 정렬: 줄바꿈 시에도 항상 좌측부터 채움 */
      .chip-grid-left{
        display:grid;
        grid-template-columns: repeat(auto-fill, minmax(92px, max-content));
        gap:12px; /* 간격 확대 */
        justify-content:start; /* 컨테이너 너비 대비 항상 좌측 정렬 */
        align-content:start;
      }

      /* prevent overlapping native select arrow with text */
      select{ background-position: right .75rem center; background-repeat:no-repeat; }
      /* ensure modals and panels stack correctly */
      .isolate{ isolation:isolate; }
    `}</style>
  );
}

export default StyleTag;