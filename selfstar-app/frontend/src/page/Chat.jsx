import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ProfileSelect from "./ProfileSelect.jsx";
import { Image as ImageIcon, Loader2, MessageSquare, User, ChevronsRight, ChevronLeft, ChevronRight, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
// removed hashtags UI; badge no longer needed

// Helpers
const mockCaption = (prompt, vibe) => {
  const base = (prompt || "").trim() || "밤하늘 같은 런웨이, 조명 아래에서 빛나는 순간";
  const styles = {
    insta: `오늘의 런웨이 룩 ✨ ${base}. #OOTD #Runway #FashionWeek`,
    editorial: `${base} — 시선을 사로잡는 라인과 결. 디테일이 만든 자신감.`,
    playful: `${base}! 🖤🖤 오늘도 캣워크 기분으로 워킹중 #스웩 #데일리룩`,
  };
  return styles[vibe] || styles.insta;
};

const mockHashtags = (prompt) => {
  const words = (prompt || "패션쇼 블랙 드레스 런웨이 감도").split(/\s+/);
  const base = ["#fashion", "#runway", "#ootd", "#model", "#lookbook", "#style", "#instafashion", "#catwalk", "#trend", "#editorial"];
  return [
    ...new Set([
      ...base,
      ...words.filter(Boolean).slice(0, 5).map((w) => `#${w.replace(/[^가-힣a-z0-9]/gi, "")}`),
    ]),
  ].slice(0, 12);
};

const avatarFromName = (name) => `https://api.dicebear.com/7.x/thumbs/svg?seed=${encodeURIComponent(name || "influencer")}`;

export default function Chat() {
  const navigate = useNavigate();
  // Scroll handling for chat messages
  const messagesEndRef = useRef(null);
  const [current, setCurrent] = useState(null);
  const [askProfile, setAskProfile] = useState(true);
  // Force-refresh ProfileSelect list when a saved profile arrives
  const [profileRefresh, setProfileRefresh] = useState(0);
  // If a persona was just created, remember its num for auto-pick
  const [autoPickNum, setAutoPickNum] = useState(null);

  // chat messages; if image present, render image bubble
  const [messages, setMessages] = useState([
    { id: 1, role: "assistant", text: "인플루언서를 선택하거나 생성해 주세요. 우측 도우미에서 캡션/해시태그를 복사할 수 있습니다.", ts: Date.now() - 5000 },
  ]);

  // options/inputs
  const [lockedFace, setLockedFace] = useState(true);
  const [prompt, setPrompt] = useState("패션쇼 무드의 블랙 드레스, 런웨이 조명, 담백한 포즈");
  const [isGenerating, setIsGenerating] = useState(false);
  // Multi-image preview state with carousel controls
  const [previewImages, setPreviewImages] = useState([]); // array of data URIs/URLs
  const [previewIndex, setPreviewIndex] = useState(0);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showPreviewHint, setShowPreviewHint] = useState(false);
  // Refs and state for fly-to-preview animation
  const imgRefs = useRef(new Map()); // messageId -> HTMLImageElement
  const previewDropRef = useRef(null);
  const pendingFlightRef = useRef(null); // { messageId, img }
  const [flight, setFlight] = useState(null); // { img, from:{x,y,w,h}, to:{x,y,w,h}, started:boolean }
  const [vibe, setVibe] = useState("insta");
  const [lsSessionId, setLsSessionId] = useState(null);
  // Explicit UI toggle for using the previous image as a style reference (outfit transfer)
  const [usePrevAsStyle, setUsePrevAsStyle] = useState(false);

  const currentPreview = previewImages.length ? previewImages[Math.min(previewIndex, previewImages.length - 1)] : null;

  const addToPreview = (uri) => {
    if (!uri || typeof uri !== "string") return;
    setPreviewImages((arr) => {
      const next = [...arr, uri];
      setPreviewIndex(next.length - 1);
      return next;
    });
  };
  const removeCurrentPreview = () => {
    setPreviewImages((arr) => {
      const idx = Math.min(previewIndex, arr.length - 1);
      const next = arr.filter((_, i) => i !== idx);
      const newIdx = Math.max(0, Math.min(idx, next.length - 1));
      setPreviewIndex(newIdx);
      return next;
    });
  };

  const isHttpUrl = (s) => typeof s === "string" && /^https?:\/\//i.test(s);

  // 엔드포인트: POST /files/ensure_public
  // payload: { image: dataURI|/files/상대경로|http(s)URL, persona_num? }
  // 반환: { ok, url(절대), path? }
  const ensurePublicUrl = async (img) => {
    try {
      const res = await fetch(`/files/ensure_public`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ image: img, persona_num: current?.num }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.ok || !data?.url) throw new Error(typeof data?.detail === "string" ? data.detail : JSON.stringify(data));
      return data.url;
    } catch (e) {
      throw e;
    }
  };

  // 엔드포인트: POST /instagram/publish
  // payload: { persona_num, image_url(절대 URL), caption }
  const uploadToInstagram = async () => {
    if (!current?.num) {
      alert("먼저 페르소나를 선택해 주세요.");
      return;
    }
    if (!currentPreview) {
      alert("프리뷰에 이미지가 없습니다.");
      return;
    }
    let uploadUrl = currentPreview;
    if (!isHttpUrl(uploadUrl)) {
      try {
        uploadUrl = await ensurePublicUrl(uploadUrl);
      } catch (e) {
        alert(`공개 URL 변환 실패: ${e}`);
        return;
      }
    }
    const caption = `${mockCaption(prompt, vibe)}\n\n${mockHashtags(prompt).join(" ")}`.slice(0, 2200);
    try {
      const res = await fetch(`/instagram/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ persona_num: current.num, image_url: uploadUrl, caption }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 401 && (data?.detail === "persona_oauth_required")) {
        if (confirm("인스타그램 계정 연동이 필요합니다. 지금 연결할까요?")) {
          const url = `/oauth/instagram/start?persona_num=${encodeURIComponent(current.num)}&picker=1&fresh=1`;
          window.location.href = url;
        }
        return;
      }
      if (!res.ok || !data?.ok) {
        alert(`업로드 실패: ${typeof data?.detail === "string" ? data.detail : JSON.stringify(data)}`);
        return;
      }
      alert("인스타그램 업로드를 요청했습니다. 잠시 후 계정에서 게시물을 확인해 주세요.");
    } catch (e) {
      alert(`업로드 중 오류: ${e}`);
    }
  };
  const handleDropOnPreview = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    setShowPreviewHint(false);
    try {
      const uri = e.dataTransfer.getData("text/uri-list") || e.dataTransfer.getData("text/plain");
      if (uri && /^(data:|https?:)/i.test(uri)) {
        addToPreview(uri.trim());
      }
    } catch {}
  };

  // Trigger a flying animation from the new chat image to the preview dropzone
  const triggerFlight = (messageId, img) => {
    pendingFlightRef.current = { messageId, img };
    // Ensure the message image is in the DOM before measuring
    requestAnimationFrame(() => {
      const srcEl = imgRefs.current.get(messageId);
      const dstEl = previewDropRef.current;
      if (!srcEl || !dstEl) return;
      const s = srcEl.getBoundingClientRect();
      const d = dstEl.getBoundingClientRect();
      const from = { x: s.left, y: s.top, w: s.width, h: s.height };
      const to = { x: d.left, y: d.top, w: d.width, h: d.height };
      setFlight({ img, from, to, started: false });
      requestAnimationFrame(() => setFlight((f) => (f ? { ...f, started: true } : f)));
    });
  };

  // Auto-scroll to bottom whenever messages update
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      try {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
        }
      } catch {}
    });
    return () => cancelAnimationFrame(id);
  }, [messages]);

  // Initial scroll to bottom on mount
  useEffect(() => {
    try {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "auto", block: "end" });
      }
    } catch {}
  }, []);

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert("클립보드에 복사되었습니다");
    } catch {
      alert("복사 실패. 수동으로 복사해주세요.");
    }
  };

  // 엔드포인트: POST /chat/image
  // payload: { persona_num, user_text, ls_session_id?, style_img? }
  const generate = async () => {
    if (!current?.num) {
      alert("먼저 페르소나를 선택해 주세요.");
      return;
    }
    setIsGenerating(true);
    const id = Date.now();
    const waitId = id + 0.5;
    setMessages((m) => [
      ...m,
      { id, role: "user", text: prompt, ts: Date.now() },
      { id: waitId, role: "assistant", text: "이미지를 생성 중입니다…", ts: Date.now() },
    ]);
    try {
      // Strengthen instruction when outfit toggle is on
      const styleLockNote = "Keep the exact same outfit from the style reference image. Do not change garment category, color, material, pattern, length, silhouette, or layers.";
      const instaAspectNote = "Output a single vertical image strictly in 4:5 aspect ratio (portrait for Instagram feed). Aim for approximately 1080x1350 resolution. Fill the frame; no borders or letterboxing.";
      const payload = {
        persona_num: current.num,
        user_text: `${prompt}\n[ASPECT] ${instaAspectNote}` + (usePrevAsStyle ? `\n[STYLE_ENFORCE] ${styleLockNote}` : ""),
        ls_session_id: lsSessionId,
      };
      // If toggle is on and we have a current preview, attach it as a style reference to preserve outfit
      if (usePrevAsStyle && currentPreview) {
        payload.style_img = currentPreview;
      }
      console.log("[Chat] POST /chat/image ->", payload);
      const res = await fetch(`/chat/image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      console.log("[Chat] /chat/image response:", res.status, data);
      if (res.ok && data?.ok && data?.image) {
        setMessages((m) => {
          // replace the waiting message
          const others = m.filter((mm) => mm.id !== waitId);
          return [
            ...others,
            { id: id + 1, role: "assistant", text: "이미지를 생성했어요.", image: data.image, ts: Date.now() },
          ];
        });
        // 첫 생성이고 프리뷰가 비어있다면 드래그-앤-드롭 힌트 표시
        setTimeout(() => {
          if (previewImages.length === 0) setShowPreviewHint(true);
        }, 150);
      } else {
        const detail = data?.detail || data?.error || data;
        setMessages((m) => {
          const others = m.filter((mm) => mm.id !== waitId);
          return [
            ...others,
            { id: id + 1, role: "assistant", text: `오류: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`, ts: Date.now() },
          ];
        });
      }
    } catch (e) {
      setMessages((m) => {
        const others = m.filter((mm) => mm.id !== waitId);
        return [...others, { id: id + 1, role: "assistant", text: `요청 실패: ${e}`, ts: Date.now() }];
      });
    } finally {
      setIsGenerating(false);
    }
  };

  // 힌트 자동 숨김: 프리뷰가 채워지면, 또는 일정 시간 경과 시
  useEffect(() => {
    if (previewImages.length > 0 && showPreviewHint) setShowPreviewHint(false);
  }, [previewImages.length]);
  useEffect(() => {
    if (!showPreviewHint) return;
    const t = setTimeout(() => setShowPreviewHint(false), 8000);
    return () => clearTimeout(t);
  }, [showPreviewHint]);

  // After flight animation ends, just clear the overlay (do NOT auto-add to preview)
  useEffect(() => {
    if (!flight || !flight.started) return;
    const t = setTimeout(() => {
      setFlight(null);
      // Keep or show the hint so user drags the image themselves
      if (previewImages.length === 0) setShowPreviewHint(true);
    }, 480);
    return () => clearTimeout(t);
  }, [flight?.started, previewImages.length]);

  // Start a LangSmith session when entering chat; end when leaving
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await fetch(`/chat/session/start`, { method: "POST", credentials: "include" });
        const data = await res.json().catch(() => ({}));
        if (active && data?.ok && data?.ls_session_id) setLsSessionId(data.ls_session_id);
      } catch {
        /* noop */
      }
    })();
    return () => {
      active = false;
      if (lsSessionId) {
        try {
          fetch(`/chat/session/end`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ ls_session_id: lsSessionId }),
          }).catch(() => {});
        } catch {
          /* noop */
        }
      }
    };
  }, []);

  // Listen for external open-profile-select event (from Imgcreate flow)
  useEffect(() => {
    const onOpenProfileSelect = () => {
      setAskProfile(true);
      setCurrent(null);
      setProfileRefresh((v) => v + 1);
    };
    window.addEventListener("open-profile-select", onOpenProfileSelect);
    // When a new persona is created, open selector and auto-pick it
    const onPersonaCreated = (e) => {
      const num = e?.detail?.persona_num;
      if (num == null) return;
      // App에서 이미 forward 한 이벤트만 소비 (from: 'app-forward')
      const from = e?.detail?.from;
      if (from && from !== "app-forward") return;
      setAutoPickNum(Number(num));
      setAskProfile(true);
      setCurrent(null);
      setProfileRefresh((v) => v + 1);
    };
    // App에서 사용자가 선택한 프로필을 직접 주입하는 경우
    const onPersonaChosen = (e) => {
      const p = e?.detail;
      if (!p || !p.num) return;
      const c = { name: p.name, num: p.num, img: p.img, avatar: p.img || avatarFromName(p.name) };
      setCurrent(c);
      setAskProfile(false);
      setAutoPickNum(null);
    };
    window.addEventListener("persona-created", onPersonaCreated);
    window.addEventListener("persona-chosen", onPersonaChosen);
    return () => {
      window.removeEventListener("open-profile-select", onOpenProfileSelect);
      window.removeEventListener("persona-created", onPersonaCreated);
      window.removeEventListener("persona-chosen", onPersonaChosen);
    };
  }, []);

  // Profile selection modal
  if (askProfile || !current) {
    return (
      <div role="dialog" aria-modal="true" style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(15,23,42,0.45)", display: "grid", placeItems: "center", padding: 16 }}>
        <div style={{ position: "relative", width: "min(1200px, 98vw)", maxHeight: "90dvh", overflow: "hidden", borderRadius: 18, boxShadow: "0 30px 70px rgba(2,6,23,.35)", background: "#fff", padding: 16 }}>
          <button aria-label="닫기" onClick={() => navigate("/")} style={{ position: "absolute", top: 10, right: 12, width: 36, height: 36, borderRadius: 999, border: "1px solid #e2e8f0", background: "#fff", boxShadow: "0 4px 10px rgba(2,6,23,.08)", cursor: "pointer", fontSize: 18, fontWeight: 800, color: "#334155" }}>×</button>
          <ProfileSelect
            key={profileRefresh}
            maxSlots={4}
            onProfileChosen={(sel) => {
              const c = { name: sel.name, num: sel.num, img: sel.img, avatar: sel.img || avatarFromName(sel.name) };
              setCurrent(c);
              setAskProfile(false);
              // reset auto-pick after success
              setAutoPickNum(null);
            }}
            onAddProfileClick={() => {
              setAskProfile(false);
              window.dispatchEvent(new CustomEvent("open-imgcreate"));
            }}
            autoPickNum={autoPickNum}
            refreshKey={profileRefresh}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-3 grid grid-cols-12 gap-4 h-[calc(100vh-4rem)] min-h-0">
      {/* Center: chat */}
      <main className="col-span-12 xl:col-span-8 rounded-xl border bg-white/80 backdrop-blur flex flex-col min-h-0">
        {/* Header */}
  <div className="px-4 h-12 border-b flex items-center gap-3">
          <img src={current.avatar} alt="avatar" className="size-8 rounded-full" />
          <div className="flex-1">
            <div className="text-sm font-semibold leading-none">{current.name} · Chat Studio</div>
            <div className="text-xs text-neutral-500"></div>
          </div>
          <Button variant="outline" size="sm" onClick={() => { setAskProfile(true); setProfileRefresh((v) => v + 1); }}>
            프로필 선택
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === "assistant" ? "items-start" : "items-end justify-end"}`}>
              {m.role === "assistant" && (
                <img src={current.avatar} className="size-8 rounded-full mr-2" alt="av" />
              )}
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-[720px] rounded-2xl p-3 shadow-sm ${m.role === "assistant" ? "bg-white border" : "bg-neutral-900 text-white"}`}
              >
                {m.image ? (
                  <div>
                    <img
                      src={m.image}
                      alt="message"
                      className="rounded-xl w-full object-cover cursor-grab active:cursor-grabbing"
                      style={{ maxHeight: 360 }}
                      draggable
                      ref={(el) => {
                        if (el) imgRefs.current.set(m.id, el); else imgRefs.current.delete(m.id);
                      }}
                      onDragStart={(e) => {
                        try {
                          e.dataTransfer.setData("text/uri-list", m.image);
                          e.dataTransfer.setData("text/plain", m.image);
                        } catch {}
                      }}
                      onDoubleClick={() => addToPreview(m.image)}
                    />
                    <div className="mt-2 text-[11px] text-neutral-500">
                      프리뷰에 넣어주세요 — 이 이미지를 프리뷰 박스로 드래그하거나 더블클릭하세요
                    </div>
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.text}</div>
                )}
              </motion.div>
              {m.role === "user" && (
                <div className="ml-2 size-8 rounded-full bg-neutral-200/80 flex items-center justify-center">
                  <User className="size-4" />
                </div>
              )}
            </div>
          ))}
          {/* Anchor element to ensure scrollIntoView targets the end reliably */}
          <div ref={messagesEndRef} />
        </div>

        {/* Composer */}
        <div className="px-4 py-3 border-t bg-white/90 sticky bottom-0 z-10">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <div className="flex items-center gap-2">
              <Switch id="face" checked={lockedFace} onCheckedChange={setLockedFace} />
              <Label htmlFor="face" className="text-xs">얼굴 고정</Label>
            </div>
            <div className="flex items-center gap-2">
              <Switch id="keep-style" checked={usePrevAsStyle} onCheckedChange={setUsePrevAsStyle} disabled={!currentPreview} />
              <Label htmlFor="keep-style" className="text-xs">이전 옷 적용</Label>
            </div>
            {/* 비율 선택 제거 요청에 따라 UI 숨김 */}
            <Button className="ml-auto gap-2" onClick={generate} disabled={isGenerating}>
              {isGenerating ? <Loader2 className="size-4 animate-spin" /> : <ImageIcon className="size-4" />}
              {isGenerating ? "생성 중" : "이미지 생성"}
            </Button>
          </div>

          <Label htmlFor="prompt" className="text-xs text-neutral-500">프롬프트</Label>
          <Textarea id="prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="예) 패션쇼 무드의 블랙 드레스, 런웨이 조명, 담백한 포즈" className="min-h-[80px]" />
        </div>
      </main>

      {/* Right column */}
      <aside className="col-span-12 xl:col-span-4 rounded-xl border bg-white/70 overflow-y-auto min-h-0 flex flex-col">
        <div className="px-4 h-12 border-b flex items-center">
          <div className="flex items-center gap-2 font-semibold"><MessageSquare className="size-4" /> 게시 도우미</div>
        </div>

        <div className="px-4 py-3 flex-1 min-h-0">
          {/* Preview card */}
          <Card className="overflow-hidden h-full flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2"><ImageIcon className="size-4" /> 프리뷰</CardTitle>
              <CardDescription>{currentPreview ? "선택된 프리뷰를 확인하세요" : "채팅의 이미지를 이 영역으로 드래그하여 보관하세요"}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 min-h-0 flex flex-col">
              <div
                className={`relative w-full rounded-2xl border-2 ${isDragOver ? "border-sky-500 ring-2 ring-sky-300" : "border-dashed border-neutral-200"}`}
                style={{ aspectRatio: "4/5", overflow: "hidden", height: "min(66vh, calc(100% - 120px))" }}
                ref={previewDropRef}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragOver(true);
                }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDropOnPreview}
              >
                {currentPreview ? (
                  <motion.img
                    key={currentPreview}
                    src={currentPreview}
                    alt="preview"
                    className="absolute inset-0 w-full h-full rounded-xl object-cover"
                    initial={{ opacity: 0.0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.25 }}
                  />
                ) : (
                  <div className="absolute inset-0 rounded-2xl flex items-center justify-center text-xs text-neutral-600">
                    {/* 배경 그라디언트 & 장식 블롭 */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white via-slate-50 to-violet-50" />
                    <div className="pointer-events-none absolute -top-10 -left-10 h-48 w-48 rounded-full bg-rose-200/30 blur-3xl" />
                    <div className="pointer-events-none absolute -bottom-12 -right-10 h-56 w-56 rounded-full bg-sky-200/30 blur-3xl" />

                    {/* 안내 텍스트 + 애니메이션 */}
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="relative z-10 flex flex-col items-center gap-2"
                    >
                      <div className="text-[13px] font-medium text-neutral-700">이미지를 드래그하여 프리뷰에 담아두세요</div>
                      <div className="text-[11px] text-neutral-500">아래 점 • 으로 여러 장을 넘겨볼 수 있어요</div>
                      {showPreviewHint && (
                        <motion.div
                          initial={{ opacity: 0, x: 16 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ repeat: Infinity, repeatType: "reverse", duration: 0.9 }}
                          className="mt-1 inline-flex items-center gap-1 rounded-full bg-white/70 px-3 py-1 shadow border"
                        >
                          <ChevronsRight className="size-4 text-emerald-600" />
                          <span className="text-[11px] text-emerald-700">첫 이미지가 생성되었어요! 여기로 드래그 ▶</span>
                        </motion.div>
                      )}
                    </motion.div>
                  </div>
                )}

                {/* Controls overlay - prettier glass buttons */}
                {previewImages.length > 0 && (
                  <>
                    <button
                      aria-label="이전"
                      className="absolute left-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-white/80 backdrop-blur-sm text-neutral-700 shadow border hover:bg-white disabled:opacity-30"
                      disabled={previewImages.length <= 1}
                      onClick={(e) => {
                        e.preventDefault();
                        setPreviewIndex((i) => (i - 1 + previewImages.length) % previewImages.length);
                      }}
                    >
                      <ChevronLeft className="size-5" />
                    </button>
                    <button
                      aria-label="다음"
                      className="absolute right-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full bg-white/80 backdrop-blur-sm text-neutral-700 shadow border hover:bg-white disabled:opacity-30"
                      disabled={previewImages.length <= 1}
                      onClick={(e) => {
                        e.preventDefault();
                        setPreviewIndex((i) => (i + 1) % previewImages.length);
                      }}
                    >
                      <ChevronRight className="size-5" />
                    </button>
                    <button
                      aria-label="제거"
                      className="absolute top-2 right-2 h-8 w-8 rounded-full bg-white/90 text-neutral-700 shadow border hover:bg-white"
                      onClick={(e) => {
                        e.preventDefault();
                        removeCurrentPreview();
                      }}
                    >
                      <X className="size-4" />
                    </button>
                  </>
                )}
                {previewImages.length > 1 && (
                  <div className="absolute inset-x-0 bottom-2 flex items-center justify-center">
                    <div className="flex items-center gap-1 bg-white/70 px-2 py-1 rounded-full shadow">
                      {previewImages.map((_, idx) => (
                        <button
                          key={idx}
                          className={`h-2 w-2 rounded-full ${idx === Math.min(previewIndex, previewImages.length - 1) ? "bg-neutral-800" : "bg-neutral-400"}`}
                          onClick={(e) => {
                            e.preventDefault();
                            setPreviewIndex(idx);
                          }}
                          aria-label={`미리보기 ${idx + 1}`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
              {/* Instagram caption inside preview card */}
              <div className="mt-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <Label className="text-xs text-neutral-600">인스타 캡션</Label>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span className="text-neutral-500">톤</span>
                    <Select value={vibe} onValueChange={setVibe}>
                      <SelectTrigger className="h-7 w-36"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="insta">Instagram</SelectItem>
                        <SelectItem value="editorial">에디토리얼</SelectItem>
                        <SelectItem value="playful">발랄/이모지</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button size="sm" variant="secondary" onClick={() => copy(mockCaption(prompt, vibe))}>복사</Button>
                  </div>
                </div>
                <Textarea value={mockCaption(prompt, vibe)} readOnly className="min-h-[72px]" />
              </div>
            </CardContent>
            <CardFooter className="justify-center">
              <Button
                size="sm"
                className="gap-2"
                disabled={!currentPreview}
                onClick={uploadToInstagram}
                title={!currentPreview ? "프리뷰 없음" : "데이터 URI도 자동으로 공개 URL로 변환하여 업로드합니다"}
              >
                인스타 업로드
              </Button>
            </CardFooter>
          </Card>
        </div>
      </aside>
    {/* 안내는 이미지 하단 캡션과 프리뷰 드롭존 하이라이트로 제공 (오버레이 비활성화) */}
    </div>
  );
}
