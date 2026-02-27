import json
import os
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import add_spin_attempt, count_spins_for_month, get_last_spin, init_db
from .spin_log import log_spin
from .security import validate_init_data

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
MONTHLY_SPIN_LIMIT = 2

PRIZES = [
    "Скидка 7%",
    "Скидка 5%",
    "Отрез DUCK до 0.5 м",
    "Отрез DUCK до 1 м",
    "Отрез РАНФОРСА до 0.5 м",
    "Отрез РАНФОРСА до 1 м",
    "Набор из 3-х мини-отрезов Duck",
    "Отрез сатина до 0.5 м",
    "Отрез сатина до 1 м",
    "Отрез фланели до 0.5 м",
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


def _month_id_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


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
    month_id = _month_id_now()
    spins_used_month = count_spins_for_month(user_id, month_id)
    spins_left_month = max(0, MONTHLY_SPIN_LIMIT - spins_used_month)
    record = get_last_spin(user_id)
    if not record:
        return {
            "has_spun": False,
            "prize": None,
            "prize_index": None,
            "spins_used_month": spins_used_month,
            "spins_left_month": spins_left_month,
            "monthly_limit": MONTHLY_SPIN_LIMIT,
        }
    prize = record["prize"]
    prize_index = PRIZES.index(prize) if prize in PRIZES else None
    return {
        "has_spun": True,
        "prize": prize,
        "prize_index": prize_index,
        "spins_used_month": spins_used_month,
        "spins_left_month": spins_left_month,
        "monthly_limit": MONTHLY_SPIN_LIMIT,
    }


@app.post("/api/spin")
async def spin(payload: InitPayload):
    user_id, user = _get_user(payload.initData)

    is_admin = user_id == ADMIN_USER_ID
    month_id = _month_id_now()
    spins_used_month = count_spins_for_month(user_id, month_id)
    spins_left_month = max(0, MONTHLY_SPIN_LIMIT - spins_used_month)
    if not is_admin and spins_left_month <= 0:
        return {
            "ok": False,
            "already": True,
            "error": "monthly_limit_reached",
            "message": "Лимит 2 круток в месяц достигнут",
            "spins_used_month": spins_used_month,
            "spins_left_month": 0,
            "monthly_limit": MONTHLY_SPIN_LIMIT,
            "locked": True,
        }

    prize = random.choice(PRIZES)
    prize_index = PRIZES.index(prize)
    if not is_admin:
        created_at = datetime.now(timezone.utc).isoformat()
        add_spin_attempt(user_id, prize, created_at, month_id)
        spins_used_month += 1
        spins_left_month = max(0, MONTHLY_SPIN_LIMIT - spins_used_month)

    log_spin(user, prize, already=False)
    return {
        "ok": True,
        "already": False,
        "prize": prize,
        "prize_index": prize_index,
        "spins_used_month": spins_used_month,
        "spins_left_month": spins_left_month if not is_admin else MONTHLY_SPIN_LIMIT,
        "monthly_limit": MONTHLY_SPIN_LIMIT,
        "locked": (not is_admin) and spins_left_month <= 0,
    }
