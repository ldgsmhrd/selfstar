import React from "react";

function Field({ label, right, children, compact = false, className = "" }) {
  const containerCls = `${compact ? "mb-2" : "mb-4"} ${className}`.trim();
  const labelBarCls = `${compact ? "mb-1" : "mb-2"} flex items-center justify-between`;
  return (
    <div className={containerCls}>
      {label && (
        <div className={labelBarCls}>
          <label className="text-sm font-semibold text-slate-800">{label}</label>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

export default Field;