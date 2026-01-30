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
  "Отрез сатина до 0.5 м"
];

const SEGMENT_COLORS = ["#ffb347", "#f76b52", "#ffd27a", "#ff9f68", "#ffc07a", "#f77b5a", "#ffe0a8"];

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
    body: JSON.stringify(body)
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}

export default function App() {
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("Добро пожаловать в колесо фортуны");
  const [prize, setPrize] = useState(null);
  const wheelRef = useRef(null);
  const initData = useMemo(() => getInitData(), []);

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

      const turns = 6 + Math.floor(Math.random() * 3);
      const segmentAngle = 360 / PRIZES.length;
      const landingIndex = Math.max(0, PRIZES.indexOf(result.prize));
      const landingAngle = landingIndex * segmentAngle + segmentAngle / 2;
      const rotation = turns * 360 + (360 - landingAngle);

      if (wheelRef.current) {
        wheelRef.current.style.transition = `transform ${SPIN_DURATION_MS}ms cubic-bezier(0.12, 0.8, 0.12, 1)`;
        wheelRef.current.style.transform = `rotate(${rotation}deg)`;
      }

      setTimeout(() => {
        setStatus(result.locked ? "locked" : "done");
        setPrize(result.prize);
        setMessage("Спасибо за участие");
      }, SPIN_DURATION_MS);
    } catch (err) {
      setStatus("idle");
      setMessage("Ошибка. Попробуйте снова.");
    }
  };

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
            "--count": PRIZES.length,
            background: `conic-gradient(${PRIZES.map((_, i) => {
              const start = (360 / PRIZES.length) * i;
              const end = (360 / PRIZES.length) * (i + 1);
              const color = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
              return `${color} ${start}deg ${end}deg`;
            }).join(", ")})`
          }}
        >
          <div className="wheel-labels">
            {PRIZES.map((label, index) => {
              const angle = (360 / PRIZES.length) * (index + 0.5);
              const isLong = label.length > 14;
              return (
                <div
                  className={`wheel-label${isLong ? " long" : ""}`}
                  key={label}
                  style={{ transform: `rotate(${angle}deg) translateY(-120px) translateX(-50%)` }}
                >
                  {label}
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
        {status === "locked" ? "Уже участвовали" : "Крутить колесо фортуны"}
      </button>

    </div>
  );
}
