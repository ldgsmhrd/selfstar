import { Routes, Route } from "react-router-dom";
import ChatEntry from "@/page/ChatEntry";
import Profiles from "@/page/Profiles";

export default function App() {
  return (
    <>
      {/* ...existing layout... */}
      <Routes>
        {/* ...existing routes... */}
        <Route path="/profiles" element={<Profiles />} />
        <Route path="/chat" element={<ChatEntry />} />
        <Route path="/chat/room" element={<div className="p-6">채팅 화면(구현 연결)</div>} />
      </Routes>
    </>
  );
}