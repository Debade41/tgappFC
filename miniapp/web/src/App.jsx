import React, { useEffect, useMemo, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "";
const SPIN_DURATION_MS = 5000;

const PRIZES = [
  "Скидка 7%",
  "Скидка 5%",
  "Отрез DUCK до 0.5 м",
  "Отрез РАНФОРСА до 0.5 м",
  "Отрез РАНФОРСА до 1 м",
  "Набор из 3-х мини-отрезов",
  "Отрез сатина до 0.5 м",
];

const SEGMENT_COLORS = [
  "#ffb347",
  "#f76b52",
  "#ffd27a",
  "#ff9f68",
  "#ffc07a",
  "#f77b5a",
  "#ffe0a8",
];

function getInitData() {
  const tg = window.Telegram?.WebApp;
  if (tg && tg.initData) return tg.initData;
  const params = new URLSearchParams(window.location.search);
  return params.get("initData") || "";
}

async function apiPost(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}

function wrapLabel(text, maxLen = 14, maxLines = 3) {
  const words = text.split(" ");
  const lines = [];
  let line = "";

  for (const w of words) {
    const next = line ? `${line} ${w}` : w;
    if (next.length <= maxLen || !line) {
      line = next;
    } else {
      lines.push(line);
      line = w;
      if (lines.length === maxLines - 1) break;
    }
  }

  const usedWords = lines.join(" ").split(" ").filter(Boolean).length + (line ? line.split(" ").length : 0);
  const allWords = words.length;

  if (line) lines.push(line);

  if (usedWords < allWords && lines.length) {
    lines[lines.length - 1] = lines[lines.length - 1].replace(/\.*$/, "") + "…";
  }

  return lines;
}

export default function App() {
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Добро пожаловать в колесо фортуны");
  const [prize, setPrize] = useState(null);

  const wheelRef = useRef(null);
  const initData = useMemo(() => getInitData(), []);

  const rotationRef = useRef(0);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, []);

  useEffect(() => {
    if (!initData) return;

    apiPost("/api/me", { initData })
      .then((data) => {
        if (data.has_spun) {
          setPrize(data.prize);
          setStatus("locked");
          setMessage("Вы уже крутили колесо");
        }
      })
      .catch(() => {
        setMessage("Ошибка проверки. Попробуйте позже.");
      });
  }, [initData]);

  const spin = async () => {
    if (status === "spinning" || status === "locked") return;

    if (!initData) {
      setMessage("Откройте приложение через Telegram");
      return;
    }

    setStatus("spinning");
    setMessage("Колесо вращается...");
    setPrize(null);

    try {
      const result = await apiPost("/api/spin", { initData });

      if (result.already) {
        setStatus("locked");
        setPrize(result.prize);
        setMessage("Вы уже крутили колесо");
        return;
      }

      const count = PRIZES.length;
      const segmentAngle = 360 / count;

      const landingIndex = Math.max(0, PRIZES.indexOf(result.prize));

      const desiredMod = (360 - (landingIndex + 0.5) * segmentAngle) % 360;

      const current = ((rotationRef.current % 360) + 360) % 360;

      const extra = (desiredMod - current + 360) % 360;

      const turns = 6 + Math.floor(Math.random() * 3);

      const nextRotation = rotationRef.current + turns * 360 + extra;
      rotationRef.current = nextRotation;

      if (wheelRef.current) {
        wheelRef.current.style.transition = `transform ${SPIN_DURATION_MS}ms cubic-bezier(0.12, 0.8, 0.12, 1)`;
        wheelRef.current.style.transform = `rotate(${nextRotation}deg)`;
      }

      setTimeout(() => {
        setStatus(result.locked ? "locked" : "done");
        setPrize(result.prize);
        setMessage("Спасибо за участие");

        try {
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred?.("success");
        } catch {}
      }, SPIN_DURATION_MS);
    } catch (err) {
      setStatus("idle");
      setMessage("Ошибка. Попробуйте снова.");
    }
  };

  const count = PRIZES.length;
  const segmentAngle = 360 / count;

  return (
    <div className="app">
      <div className="glow" />

      <header className="header">
        <h1>Колесо фортуны</h1>
        <p className="subtitle">Поймай удачу на тёплой волне</p>
      </header>

      <div className="wheel-wrap">
        <div className="pointer" />

        <div
          className="wheel"
          ref={wheelRef}
          style={{
            "--count": count,
            background: `conic-gradient(${PRIZES.map((_, i) => {
              const start = segmentAngle * i;
              const end = segmentAngle * (i + 1);
              const color = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
              return `${color} ${start}deg ${end}deg`;
            }).join(", ")})`,
          }}
        >
          <div className="wheel-labels">
          {PRIZES.map((label, index) => {
            const segmentAngle = 360 / PRIZES.length;

            const angle = (index + 0.5) * segmentAngle;

            const radius = 118; 

            const lines = wrapLabel(label, 14, 3);
            const isLong = lines.length >= 3 || label.length > 18;

            return (
              <div
                key={`${label}-${index}`}
                className={`wheel-label${isLong ? " long" : ""}`}
                style={{
                  transform: `
                    rotate(${angle}deg)
                    translate(${radius}px)
                    rotate(90deg)
                    translate(-50%, -50%)
                  `,
                }}
              >
                {lines.map((t, i) => (
                  <div key={i}>{t}</div>
                ))}
              </div>
            );
          })}
        </div>

          <div className="wheel-center" />
        </div>
      </div>

      <div className="status">
        <div className="message">{message}</div>
        {prize && <div className="prize">{prize}</div>}
      </div>

      <button className="spin-btn" onClick={spin} disabled={status === "spinning" || status === "locked"}>
        {status === "locked" ? "Уже участвовали" : status === "spinning" ? "Крутим..." : "Крутить колесо фортуны"}
      </button>
    </div>
  );
}