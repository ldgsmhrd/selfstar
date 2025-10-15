import React, { useState, useEffect } from "react";

function TypingText({ text = "", speed = 100 }) {
  // Normalize to a string to avoid undefined/null being concatenated
  const safeText = typeof text === "string" ? text : String(text ?? "");
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    setDisplayedText(""); // Reset when text changes

    let index = 0;
    const interval = setInterval(() => {
      if (index < safeText.length) {
        // Build from the source string to avoid concatenating any stray values
        setDisplayedText(safeText.slice(0, index + 1));
        index += 1;
      } else {
        clearInterval(interval);
      }
    }, Math.max(0, speed));

    return () => clearInterval(interval);
  }, [safeText, speed]);

  return <span>{displayedText}</span>;
}

export default TypingText;