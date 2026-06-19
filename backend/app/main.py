from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .database import init_db, seed_db
from .schemas import WalletCreate, WalletSettingsPatch, PoolCreate
from . import services

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(title="FatBot Copytrading MVP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    seed_db()

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/summary")
def summary():
    return services.get_summary()

@app.get("/api/trader-source")
def trader_source():
    return {"source": services.get_trader_source()}

@app.get("/api/traders")
def traders():
    return services.list_traders()

@app.get("/api/traders/{address}")
def trader(address: str):
    data = services.get_trader(address)
    if not data:
        raise HTTPException(status_code=404, detail="Trader not found")
    return data

@app.get("/api/wallets")
def wallets():
    return services.list_wallets()

@app.post("/api/wallets/generate")
def generate_wallet(payload: WalletCreate):
    try:
        return services.generate_wallet(mode=payload.mode, trader_address=payload.trader_address, label=payload.label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/wallets/{wallet_id}")
def wallet(wallet_id: int):
    data = services.get_wallet(wallet_id)
    if not data:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return data

@app.post("/api/wallets/{wallet_id}/activate")
def activate_wallet(wallet_id: int):
    data = services.activate_wallet(wallet_id)
    if not data:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return data

@app.post("/api/wallets/{wallet_id}/pause")
def pause_wallet(wallet_id: int):
    data = services.pause_wallet(wallet_id)
    if not data:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return data

@app.post("/api/wallets/{wallet_id}/close")
def close_wallet(wallet_id: int):
    data = services.close_wallet(wallet_id)
    if not data:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return data

@app.delete("/api/wallets/{wallet_id}")
def delete_wallet(wallet_id: int):
    ok = services.delete_wallet(wallet_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"status": "deleted", "wallet_id": wallet_id}

@app.patch("/api/wallets/{wallet_id}/settings")
def patch_wallet_settings(wallet_id: int, payload: WalletSettingsPatch):
    data = services.patch_settings(wallet_id, payload.model_dump())
    if not data:
        raise HTTPException(status_code=404, detail="Wallet settings not found")
    return data

@app.get("/api/live-positions")
def live_positions():
    return services.live_positions()

@app.get("/api/pools")
def pools():
    return services.list_pools()

@app.post("/api/pools")
def create_pool(payload: PoolCreate):
    return services.create_pool(payload.vault_name or payload.name, payload.trader_addresses, payload.multiplier)
