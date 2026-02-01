import json
import os
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import get_spin, init_db, set_spin
from .spin_log import log_spin
from .security import validate_init_data

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

PRIZES = [
    "Скидка 7%",
    "Скидка 5%",
    "Отрез DUCK до 0.5 м",
    "Отрез РАНФОРСА до 0.5 м",
    "Отрез РАНФОРСА до 1 м",
    "Набор из 3-х мини-отрезов",
    "Отрез сатина до 0.5 м",
]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InitPayload(BaseModel):
    initData: str


def _get_user(init_data: str) -> tuple[int, dict]:
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not set")
    try:
        data = validate_init_data(init_data, BOT_TOKEN)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    user_raw = data.get("user")
    if not user_raw:
        raise HTTPException(status_code=400, detail="user data not found")
    try:
        user = json.loads(user_raw)
        return int(user["id"]), user
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid user data") from exc


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/api/health")
async def health():
    return {"ok": True}

@app.get("/api/prizes")
async def prizes():
    return {"prizes": PRIZES}

@app.post("/api/me")
async def me(payload: InitPayload):
    user_id, _user = _get_user(payload.initData)
    record = get_spin(user_id)
    if not record:
        return {"has_spun": False, "prize": None, "prize_index": None}
    prize = record["prize"]
    prize_index = PRIZES.index(prize) if prize in PRIZES else None
    return {"has_spun": True, "prize": prize, "prize_index": prize_index}


@app.post("/api/spin")
async def spin(payload: InitPayload):
    user_id, user = _get_user(payload.initData)

    record = get_spin(user_id)
    is_admin = user_id == ADMIN_USER_ID
    if record and not is_admin:
        prize = record["prize"]
        prize_index = PRIZES.index(prize) if prize in PRIZES else None
        log_spin(user, prize, already=True)
        return {"ok": True, "already": True, "prize": prize, "prize_index": prize_index, "locked": True}

    prize = random.choice(PRIZES)
    prize_index = PRIZES.index(prize)
    if not is_admin:
        set_spin(user_id, prize, datetime.now(timezone.utc).isoformat())

    log_spin(user, prize, already=False)
    return {"ok": True, "already": False, "prize": prize, "prize_index": prize_index, "locked": not is_admin}
