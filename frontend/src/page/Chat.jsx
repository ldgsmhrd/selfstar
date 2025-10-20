import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ProfileSelect from "./ProfileSelect.jsx";
import {
  Bot,
  Hash,
  Image as ImageIcon,
  Loader2,
  MessageSquare,
  Settings2,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

/* ---------------- helpers ---------------- */
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
  const base = [
    "#fashion",
    "#runway",
    "#ootd",
    "#model",
    "#lookbook",
    "#style",
    "#instafashion",
    "#catwalk",
    "#trend",
    "#editorial",
  ];
  return [
    ...new Set([
      ...base,
      ...words
        .filter(Boolean)
        .slice(0, 5)
        .map((w) => `#${w.replace(/[^가-힣a-z0-9]/gi, "")}`),
    ]),
  ].slice(0, 12);
};

const avatarFromName = (name) =>
  `https://api.dicebear.com/7.x/thumbs/svg?seed=${encodeURIComponent(
    name || "influencer"
  )}`;

/* ---------------- page ---------------- */
export default function Chat() {
  const navigate = useNavigate();
  // 현재 선택된 프로필(없으면 null) → 없으면 프로필 선택 모달 먼저 표시
  const [current, setCurrent] = useState(null);
  const [askProfile, setAskProfile] = useState(true);

  // 채팅 메시지
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      text:
        "인플루언서를 선택하거나 생성해 주세요. 우측 도우미에서 캡션/해시태그를 복사할 수 있습니다.",
      ts: Date.now() - 5000,
    },
  ]);

  // 간소화된 옵션
  const [lockedFace, setLockedFace] = useState(true);
  const [ratio, setRatio] = useState("3:4");
  const [prompt, setPrompt] = useState(
    "패션쇼 무드의 블랙 드레스, 런웨이 조명, 담백한 포즈"
  );
  const [isGenerating, setIsGenerating] = useState(false);

  // 우측 도우미
  const [vibe, setVibe] = useState("insta");
  // 우측 미리보기/캡션/해시태그는 즉시 복사용으로만 사용

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      alert("클립보드에 복사되었습니다");
    } catch {
      alert("복사 실패. 수동으로 복사해주세요.");
    }
  };

  // 이미지 생성(프리뷰는 만들지 않음)
  const generate = async () => {
    setIsGenerating(true);
    const id = Date.now();
    setMessages((m) => [
      ...m,
      { id, role: "user", text: prompt, ts: Date.now() },
    ]);
    await new Promise((r) => setTimeout(r, 400));
    setMessages((m) => [
      ...m,
      {
        id: id + 1,
        role: "assistant",
        text: `요청이 접수되었습니다.\n(데모에서는 이미지를 표시하지 않아요)\n설정: ${ratio}, ${
          lockedFace ? "얼굴 고정" : "얼굴 자유"
        }`,
        ts: Date.now(),
      },
    ]);
    setIsGenerating(false);
  };

  // Imgcreate에서 저장 완료(postMessage -> App -> window event) 시 다시 프로필 선택 모달을 열어준다
  useEffect(() => {
    const onOpenProfileSelect = () => {
      setAskProfile(true);
      setCurrent(null);
    };
    window.addEventListener("open-profile-select", onOpenProfileSelect);
    return () => window.removeEventListener("open-profile-select", onOpenProfileSelect);
  }, []);

  // 프로필 선택 모달: Chat 진입시 먼저 호출
  if (askProfile || !current) {
    return (
      <div role="dialog" aria-modal="true" style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(15,23,42,0.45)", display: "grid", placeItems: "center", padding: 16 }}>
        <div style={{ position: "relative", width: "min(1200px, 98vw)", maxHeight: "90dvh", overflow: "hidden", borderRadius: 18, boxShadow: "0 30px 70px rgba(2,6,23,.35)", background: "#fff", padding: 16 }}>
          <button
            aria-label="닫기"
            onClick={() => navigate("/")}
            style={{ position: "absolute", top: 10, right: 12, width: 36, height: 36, borderRadius: 999, border: "1px solid #e2e8f0", background: "#fff", boxShadow: "0 4px 10px rgba(2,6,23,.08)", cursor: "pointer", fontSize: 18, fontWeight: 800, color: "#334155" }}
          >
            ×
          </button>
          <ProfileSelect
            maxSlots={4}
            onProfileChosen={(name) => {
              const c = { name, avatar: avatarFromName(name) };
              setCurrent(c);
              setAskProfile(false);
            }}
            onAddProfileClick={() => {
              // 선택 모달 닫고 이미지 생성 모달을 열라는 신호(App에서 iframe으로 처리)
              setAskProfile(false);
              window.dispatchEvent(new CustomEvent("open-imgcreate"));
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-3 grid grid-cols-12 gap-4 h-[calc(100vh-4rem)] min-h-0">
      {/* 가운데: 채팅 (스크롤 전용) */}
      <main className="col-span-12 xl:col-span-8 rounded-xl border bg-white/80 backdrop-blur flex flex-col min-h-0">
        {/* 헤더 */}
        <div className="px-4 py-3 border-b flex items-center gap-3">
          <img src={current.avatar} alt="avatar" className="size-8 rounded-full" />
          <div className="flex-1">
            <div className="text-sm font-semibold leading-none">
              {current.name} · Chat Studio
            </div>
            <div className="text-xs text-neutral-500">
            </div>
          </div>
          <Button variant="ghost" size="icon">
            <Settings2 className="size-5" />
          </Button>
        </div>

        {/* 메시지 영역: 스크롤 */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex ${
                m.role === "assistant" ? "items-start" : "items-end justify-end"
              }`}
            >
              {m.role === "assistant" && (
                <img
                  src={current.avatar}
                  className="size-8 rounded-full mr-2"
                  alt="av"
                />
              )}
              <motion.div
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`max-w-[720px] rounded-2xl p-3 shadow-sm ${
                  m.role === "assistant"
                    ? "bg-white border"
                    : "bg-neutral-900 text-white"
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {m.text}
                </div>
              </motion.div>
              {m.role === "user" && (
                <div className="ml-2 size-8 rounded-full bg-neutral-200/80 flex items-center justify-center">
                  <User className="size-4" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 컴포저: sticky bottom */}
        <div className="px-4 py-3 border-t bg-white/90 sticky bottom-0 z-10">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <div className="flex items-center gap-2">
              <Switch
                id="face"
                checked={lockedFace}
                onCheckedChange={setLockedFace}
              />
              <Label htmlFor="face" className="text-xs">
                얼굴 고정
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Label className="text-xs">비율</Label>
              <Select value={ratio} onValueChange={setRatio}>
                <SelectTrigger className="h-8 w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1:1">1:1</SelectItem>
                  <SelectItem value="3:4">3:4</SelectItem>
                  <SelectItem value="4:5">4:5</SelectItem>
                  <SelectItem value="9:16">9:16</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button className="ml-auto gap-2" onClick={generate} disabled={isGenerating}>
              {isGenerating ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <ImageIcon className="size-4" />
              )}
              {isGenerating ? "생성 중" : "이미지 생성"}
            </Button>
          </div>

          <Label htmlFor="prompt" className="text-xs text-neutral-500">
            프롬프트
          </Label>
          <Textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="예) 패션쇼 무드의 블랙 드레스, 런웨이 조명, 담백한 포즈"
            className="min-h-[80px]"
          />
        </div>
      </main>

      {/* 오른쪽: 게시 도우미 칼럼 (개별 스크롤) */}
      <aside className="col-span-12 xl:col-span-4 rounded-xl border bg-white/70 overflow-y-auto min-h-0">
        <div className="p-3 border-b">
          <div className="flex items-center gap-2 font-semibold">
            <MessageSquare className="size-4" /> 게시 도우미
          </div>
          <CardDescription>이미지 생성은 연결 전 단계입니다.</CardDescription>
        </div>

        <div className="p-3 space-y-3">
          {/* 프리뷰: 기본 웹 고정(이미지 미표시) */}
          <Card className="overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <ImageIcon className="size-4" /> 프리뷰
              </CardTitle>
              <CardDescription>
                구현 중
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="aspect-[4/5] w-full bg-neutral-100 rounded-xl flex items-center justify-center text-xs text-neutral-500">
                <Bot className="size-4 mr-1" /> 아직 이미지가 없습니다
              </div>
            </CardContent>
            <CardFooter className="justify-between">
              <Button variant="outline" size="sm" className="gap-2" disabled>
                링크 복사
              </Button>
              <Button variant="outline" size="sm" className="gap-2" disabled>
                다운로드
              </Button>
            </CardFooter>
          </Card>

          {/* 캡션 */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Hash className="size-4" /> 인스타 캡션
              </CardTitle>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-neutral-500">톤</span>
                <Select value={vibe} onValueChange={setVibe}>
                  <SelectTrigger className="h-8 w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="insta">Instagram(300자)</SelectItem>
                    <SelectItem value="editorial">에디토리얼</SelectItem>
                    <SelectItem value="playful">발랄/이모지</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <Textarea value={mockCaption(prompt, vibe)} readOnly className="min-h-[96px]" />
              <div className="flex gap-2">
                <Button size="sm" variant="secondary" onClick={() => copy(mockCaption(prompt, vibe))}>
                  캡션 복사
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 해시태그 */}
          <Card>
            <CardHeader className="pb-1">
              <CardTitle className="text-base">추천 해시태그</CardTitle>
              <CardDescription>프롬프트 기반 키워드</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {mockHashtags(prompt).map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="cursor-pointer"
                  onClick={() => copy(tag)}
                >
                  {tag}
                </Badge>
              ))}
            </CardContent>
            <CardFooter className="justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={() => copy(mockHashtags(prompt).join(" "))}
              >
                모두 복사
              </Button>
            </CardFooter>
          </Card>
        </div>
      </aside>
    </div>
  );
}
