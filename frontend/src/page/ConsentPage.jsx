import React, { useMemo, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import guideImg from "../../img/fixed_face.png";
import "./ConsentPage.css";

export default function ConsentPage() {
   const navigate = useNavigate();
   // ===== State =====
   const [agreeTerms, setAgreeTerms] = useState(false);
   const [agreePrivacy, setAgreePrivacy] = useState(false);
   const [agreeAge, setAgreeAge] = useState(false);
   const [agreeAI, setAgreeAI] = useState(false);

   const [modal, setModal] = useState(null); // "terms" | "privacy" | "ai" | null

   // Guide bubble typing effect with bold segments and left alignment
   const segments = useMemo(
      () => [
         { text: "안녕하세요, 저는 ", bold: false },
         { text: "SelfStar 가이드", bold: true },
         { text: "입니다. 가입을 완료하려면 ", bold: false },
         { text: "회원가입약관", bold: true },
         { text: ", ", bold: false },
         { text: "개인정보처리방침", bold: true },
         { text: ", ", bold: false },
         { text: "AI 모델 개선 동의", bold: true },
         { text: "에 체크해 주세요.", bold: false },
      ],
      []
   );
   const flatMessage = useMemo(() => segments.map((s) => s.text).join(""), [segments]);
   const totalLen = flatMessage.length;
   const [typedCount, setTypedCount] = useState(0);
   const doneTyping = typedCount >= totalLen;

   useEffect(() => {
      let active = true;
      const typeNext = (i) => {
         if (!active) return;
         if (i > totalLen) return; // done
         setTypedCount(i);
         const ch = flatMessage[i - 1] || "";
         const delay = [".", ",", "!", "?", "·", " "].includes(ch) ? 85 : 36;
         setTimeout(() => typeNext(i + 1), delay);
      };
      // Start typing with a small initial pause
      setTypedCount(0);
      const t = setTimeout(() => typeNext(1), 250);
      return () => {
         active = false;
         clearTimeout(t);
      };
   }, [totalLen, flatMessage]);

   const allRequiredOn = useMemo(
      () => agreeTerms && agreePrivacy && agreeAge && agreeAI,
      [agreeTerms, agreePrivacy, agreeAge, agreeAI]
   );

   // ===== Handlers =====
   const toggleAll = (checked) => {
      setAgreeTerms(checked);
      setAgreePrivacy(checked);
      setAgreeAge(checked);
      setAgreeAI(checked);
   };

   const handleSubmit = () => {
      if (!allRequiredOn) return;
      const payload = {
         version: "tos-2025-10-01",
         consents: {
            terms_required: agreeTerms,
            privacy_required: agreePrivacy,
            age_over_14: agreeAge,
            ai_model_training_required: agreeAI,
         },
      };
      console.debug("[Consent] submit payload", payload);
      // 동의 완료 후 사용자 설정 페이지로 이동
      navigate("/setup");
   };

   // 모두동의 인디터미넌트 계산
   const someChecked = agreeTerms || agreePrivacy || agreeAge || agreeAI;
   const allChecked = allRequiredOn;
   const allBoxProps = {
      checked: allChecked,
      ref: (el) => {
         if (el) el.indeterminate = !allChecked && someChecked;
      },
      onChange: (e) => toggleAll(e.target.checked),
   };

   return (
      <section className="wrap" aria-label="가입 약관 동의">
         <div className="card">
            <div className="card-body">
               {/* 안내 */}
               <div className="guide">
                  <img className="avatar" src={guideImg} alt="SelfStar 가이드" />
                  <div className="bubble" aria-live="polite" aria-label="가이드 메시지">
                     {segments.map((seg, idx) => {
                        const start = segments.slice(0, idx).reduce((a, s) => a + s.text.length, 0);
                        const take = Math.max(0, Math.min(typedCount - start, seg.text.length));
                        if (take <= 0) return null;
                        const slice = seg.text.slice(0, take);
                        return seg.bold ? <b key={idx}>{slice}</b> : <span key={idx}>{slice}</span>;
                     })}
                     {!doneTyping && <span className="caret" aria-hidden="true" />}
                  </div>
               </div>

               {/* 모두 동의 */}
               <div className="section-title">
                  <span className="dot" />
                  모두 동의
               </div>
               <div className="agree-row">
                  <input id="agree-all" className="checkbox" type="checkbox" {...allBoxProps} />
                  <label className="label" htmlFor="agree-all">
                     모든 항목에 동의합니다(선택).
                  </label>
                  <span className="badge">일괄</span>
               </div>

               {/* 필수 동의 */}
               <div className="section-title" style={{ marginTop: 18 }}>
                  <span className="dot" />
                  필수 동의
               </div>

               <div className="agree-row">
                  <input
                     id="agree-terms"
                     className="checkbox"
                     type="checkbox"
                     checked={agreeTerms}
                     onChange={(e) => setAgreeTerms(e.target.checked)}
                  />
                  <label className="label" htmlFor="agree-terms">
                     회원가입약관 동의
                  </label>
                  <span className="badge">필수</span>
                  <button className="chip" type="button" onClick={() => setModal("terms")}>
                     전문 보기
                  </button>
               </div>
               <div className="doc" id="doc-terms">
                  본 약관은 서비스 이용에 관한 기본 사항을 규정합니다. 서비스 제공, 계정 사용,
                  금지 행위, 면책, 분쟁 해결에 관한 조항을 포함합니다. 아래 전문 보기에서 상세
                  내용을 확인하세요.
               </div>

               <div className="agree-row" style={{ marginTop: 12 }}>
                  <input
                     id="agree-privacy"
                     className="checkbox"
                     type="checkbox"
                     checked={agreePrivacy}
                     onChange={(e) => setAgreePrivacy(e.target.checked)}
                  />
                  <label className="label" htmlFor="agree-privacy">
                     개인정보처리방침 동의
                  </label>
                  <span className="badge">필수</span>
                  <button className="chip" type="button" onClick={() => setModal("privacy")}>
                     전문 보기
                  </button>
               </div>
               <div className="doc" id="doc-privacy">
                  수집 항목(로그인 정보, 로그, 기기 정보 등), 이용 목적(서비스 제공·보안·고객지원·분석),
                  보관 기간, 제3자 제공/국외 이전 여부, 파기 절차를 명시합니다. 아래 전문 보기에서
                  상세 내용을 확인하세요.
               </div>

               <div className="agree-row" style={{ marginTop: 12 }}>
                  <input
                     id="agree-age"
                     className="checkbox"
                     type="checkbox"
                     checked={agreeAge}
                     onChange={(e) => setAgreeAge(e.target.checked)}
                  />
                  <label className="label" htmlFor="agree-age">
                     만 14세 이상입니다
                  </label>
                  <span className="badge">필수</span>
               </div>

               {/* AI 동의(필수) */}
               <div className="section-title" style={{ marginTop: 18 }}>
                  <span className="dot" />
                  AI 사용 안내 및 동의(필수)
               </div>
               <div className="agree-row">
                  <input
                     id="agree-ai"
                     className="checkbox"
                     type="checkbox"
                     checked={agreeAI}
                     onChange={(e) => setAgreeAI(e.target.checked)}
                  />
                  <label className="label" htmlFor="agree-ai">
                     AI 모델 개선을 위한 데이터 이용 동의
                  </label>
                  <span className="badge">필수</span>
                  <button className="chip" type="button" onClick={() => setModal("ai")}>
                     AI 안내
                  </button>
               </div>
               <div className="doc" id="doc-ai">
                  SelfStar는 추천 및 품질 개선, 보안 강화에 AI를 사용합니다. 본 동의는 가명처리된
                  이용 데이터를 모델 개선에 활용하는 데 필요하며, 철회 시 모델 재학습 시점부터
                  반영됩니다.
               </div>

               <div className="footer-actions">
                  <button
                     id="btn-next"
                     className={`btn ${allRequiredOn ? "active" : ""}`}
                     disabled={!allRequiredOn}
                     onClick={handleSubmit}
                     type="button"
                  >
                     동의하고 계속
                  </button>
               </div>
            </div>
         </div>

         {/* 모달 공통 */}
         <Modal open={modal === "terms"} onClose={() => setModal(null)} title="회원가입약관">
            <TermsBody />
         </Modal>
         <Modal open={modal === "privacy"} onClose={() => setModal(null)} title="개인정보처리방침">
            <PrivacyBody />
         </Modal>
         <Modal open={modal === "ai"} onClose={() => setModal(null)} title="SelfStar의 AI 사용 안내">
            <AIBody />
         </Modal>
      </section>
   );
}

/* ================= Subcomponents ================= */

function Modal({ open, onClose, title, children }) {
   return (
      <div className={`modal ${open ? "open" : ""}`} aria-hidden={!open} role="dialog">
         <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
               {title}
               <button className="btn-secondary" onClick={onClose} type="button">
                  닫기
               </button>
            </div>
            <div className="modal-body">{children}</div>
            <div className="modal-foot">
               <button className="btn-secondary" onClick={onClose} type="button">
                  확인
               </button>
            </div>
         </div>
         {/* 배경 클릭 닫기 */}
         <div style={{ position: "fixed", inset: 0 }} onClick={onClose} />
      </div>
   );
}

function TermsBody() {
   return (
      <div>
         <p>
            <b>문서버전</b>: tos-2025-10-01 · <b>시행일자</b>: 2025-10-13
         </p>
         <h3>제1조(목적)</h3>
         <p>
            본 약관은 SelfStar(이하 "회사")가 제공하는 서비스의 이용과 관련하여 회사와
            이용자의 권리·의무 및 책임사항을 규정함을 목적으로 합니다.
         </p>
         <h3>제2조(정의)</h3>
         <ol>
            <li>“서비스”란 회사가 제공하는 웹/모바일 기반 기능을 말합니다.</li>
            <li>“회원”이란 계정을 생성하여 서비스를 이용하는 자를 말합니다.</li>
            <li>“게시물”이란 이용자가 서비스에 게시·업로드한 콘텐츠를 말합니다.</li>
         </ol>
         <h3>제3조(약관의 게시 및 개정)</h3>
         <p>회사는 관련 법령을 위반하지 않는 범위에서 약관을 개정할 수 있으며 공지합니다.</p>
         <h3>제4조(계정 및 인증)</h3>
         <p>회원가입은 OAuth 등 인증 절차를 통해 이뤄지며 보안 책임은 회원에게 있습니다.</p>
         <h3>제5조(서비스의 제공 및 변경)</h3>
         <p>운영상·기술상의 필요로 서비스의 전부 또는 일부를 변경·중단할 수 있습니다.</p>
         <h3>제6조(이용자의 의무)</h3>
         <ul>
            <li>법령·약관·가이드라인 준수</li>
            <li>권리침해·불법·스팸·시스템 남용 금지</li>
         </ul>
         <h3>제7조(게시물의 권리와 책임)</h3>
         <p>게시물 저작권은 원저작자에게 귀속되며 회사는 운영 목적의 이용권을 가집니다.</p>
         <h3>제8조(개인정보보호)</h3>
         <p>개인정보 처리에 관한 사항은 개인정보처리방침에 따릅니다.</p>
         <h3>제9조(면책)</h3>
         <p>천재지변, 불가항력, 회원 귀책에 대해서 회사는 책임을 지지 않습니다.</p>
         <h3>제10조(관할 및 준거법)</h3>
         <p>대한민국 법령을 준거법으로 하며 관할은 민사소송법에 따릅니다.</p>
         <p>※ 본 전문은 템플릿이며 실제 적용 전 법무 검토가 필요합니다.</p>
      </div>
   );
}

function PrivacyBody() {
   return (
      <div>
         <p>
            <b>문서버전</b>: privacy-2025-10-01 · <b>시행일자</b>: 2025-10-13
         </p>
         <h3>1. 수집 항목 및 방법</h3>
         <ul>
            <li>
               <b>필수</b>: 이메일/소셜ID, 닉네임, 인증토큰, 접속기록(IP/UA/쿠키), 이용기록
            </li>
            <li>
               <b>선택</b>: 프로필 이미지, 관심사, 피드백/설문
            </li>
            <li>
               <b>방법</b>: 회원가입(OAuth), 이용 중 자동 수집, 고객문의
            </li>
         </ul>
         <h3>2. 처리 목적</h3>
         <p>회원 식별·인증, 서비스 제공·개선, 고객지원, 보안 및 부정이용 방지, 법규 준수</p>
         <h3>3. 보유·이용기간</h3>
         <p>목적 달성 시 지체 없이 파기. 법령 보존 기간은 관련 규정에 따름.</p>
         <h3>4. 제3자 제공/국외 이전</h3>
         <p>해당 시 제공받는 자·국가·항목·목적·보유기간·보호조치를 고지하고 동의를 받습니다.</p>
         <h3>5. 처리위탁</h3>
         <p>수탁업체, 위탁업무, 연락처를 공개합니다.</p>
         <h3>6. 정보주체 권리</h3>
         <p>열람·정정·삭제·처리정지·동의 철회는 마이페이지 또는 고객센터로 요청 가능합니다.</p>
         <h3>7. 쿠키 및 유사기술</h3>
         <p>브라우저 설정으로 저장 거부 가능. 광고쿠키 사용 시 별도 동의.</p>
         <h3>8. 안전성 확보조치</h3>
         <p>암호화, 접근통제, 접근기록, 모니터링 등</p>
         <h3>9. 아동의 개인정보</h3>
         <p>만 14세 미만은 보호자 동의가 필요합니다.</p>
         <h3>10. 개인정보 보호책임자</h3>
         <p>성명/직책/연락처/이메일 기재</p>
         <h3>11. 고지 의무</h3>
         <p>변경 시 최소 7일 전 공지(중대한 변경은 30일 전).</p>
         <p>※ 본 전문은 템플릿이며 실제 적용 전 법무 검토가 필요합니다.</p>
      </div>
   );
}

function AIBody() {
   return (
      <div>
         <p>
            <b>문서버전</b>: ai-2025-10-01 · <b>시행일자</b>: 2025-10-13
         </p>
         <h3>목적</h3>
         <p>
            SelfStar는 추천 품질 개선, 검색/랭킹 최적화, 부정행위 탐지 및 보안 강화를 위해
            AI/ML 모델을 운영합니다.
         </p>
         <h3>수집·이용되는 데이터 범위</h3>
         <ul>
            <li>이용 로그, 클릭/체류/전환 정보, 오류 이벤트</li>
            <li>사용자 입력·업로드 콘텐츠, 피드백(신고·평가)</li>
            <li>기기·브라우저 정보 및 대략적 지역(정밀 위치 제외)</li>
         </ul>
         <p>
            개인식별 정보는 분리 또는 가명처리 후 학습·평가에 활용하며, 민감정보는 제외됩니다.
         </p>
         <h3>처리 방식 및 보호조치</h3>
         <p>내부 폐쇄 환경에서만 접근 가능하며, 암호화·접근통제·기록 모니터링 등 안전조치를 적용합니다.</p>
         <h3>보관 기간</h3>
         <p>
            학습 원본 데이터는 목적 달성 시 지체 없이 파기(최대 ○○개월), 학습 산출물은 서비스
            운영 기간 동안 보관될 수 있습니다.
         </p>
         <h3>동의 철회</h3>
         <p>
            본 동의는 서비스 품질 유지에 필수입니다. 탈퇴 또는 법정 요건에 따른 예외를 제외하고
            철회 시 서비스 품질에 영향이 있을 수 있습니다. 철회 이전 학습된 모델에는 소급 반영되기
            어려울 수 있습니다.
         </p>
         <h3>국외 이전/외부 모델 사용</h3>
         <p>해당 시 업체·국가·항목·목적·보유기간·보호조치를 고지합니다.</p>
         <h3>문의</h3>
         <p>AI/개인정보 관련 문의는 개인정보 보호책임자 또는 고객센터로 연락 바랍니다.</p>
         <p>※ 본 전문은 템플릿이며 실제 적용 전 법무 검토가 필요합니다.</p>
      </div>
   );
}
