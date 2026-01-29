import json
import os
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import get_spin, init_db, set_spin
from .security import validate_init_data

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

PRIZES = [
    "Скидка 5 процентов",
    "Скидка 3 процентов",
    "Скидка 7 процентов",
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


def _get_user_id(init_data: str) -> int:
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
        return int(user["id"])
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid user data") from exc


@app.on_event("startup")
async def startup() -> None:
    init_db()


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/me")
async def me(payload: InitPayload):
    user_id = _get_user_id(payload.initData)
    record = get_spin(user_id)
    if not record:
        return {"has_spun": False, "prize": None}
    return {"has_spun": True, "prize": record["prize"]}


@app.post("/api/spin")
async def spin(payload: InitPayload):
    user_id = _get_user_id(payload.initData)

    record = get_spin(user_id)
    is_admin = user_id == ADMIN_USER_ID
    if record and not is_admin:
        return {"ok": True, "already": True, "prize": record["prize"], "locked": True}

    prize = random.choice(PRIZES)
    if not is_admin:
        set_spin(user_id, prize, datetime.now(timezone.utc).isoformat())

    return {"ok": True, "already": False, "prize": prize, "locked": not is_admin}
