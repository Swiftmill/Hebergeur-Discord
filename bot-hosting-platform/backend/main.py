import asyncio
import os
import shutil
import zipfile
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .auth import router as auth_router, get_current_user
from .bot_manager import bot_manager
from .config import BOTS_DIR, LOGS_DIR, BASE_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Discord Bot Hosting Platform")
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/api/bots", response_model=List[schemas.BotOut])
async def list_bots(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bots = db.query(models.Bot).filter(models.Bot.owner_id == current_user.id).all()
    return bots


@app.post("/api/bots", response_model=schemas.BotDetail)
async def create_bot(
    name: str = Form(...),
    language: str = Form("python"),
    entrypoint: str = Form("bot.py"),
    token: str = Form(...),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user_bot_dir = BOTS_DIR / str(current_user.id)
    user_bot_dir.mkdir(parents=True, exist_ok=True)

    new_bot = models.Bot(
        name=name,
        language=language,
        entrypoint=entrypoint,
        token=token,
        status="stopped",
        bot_path="",
        owner_id=current_user.id,
    )
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    bot_dir = user_bot_dir / str(new_bot.id)
    bot_dir.mkdir(parents=True, exist_ok=True)

    if file:
        upload_path = bot_dir / file.filename
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)
        if zipfile.is_zipfile(upload_path):
            with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                zip_ref.extractall(bot_dir)
            upload_path.unlink()
    else:
        # create minimal bot file if none provided
        if language.lower() == "python":
            with open(bot_dir / entrypoint, "w") as f:
                f.write("import os\nimport asyncio\n\nasync def main():\n    token=os.getenv('DISCORD_TOKEN','')\n    while True:\n        print('Bot running with token', token)\n        await asyncio.sleep(5)\n\nasyncio.run(main())\n")
        else:
            with open(bot_dir / entrypoint, "w") as f:
                f.write("const token = process.env.DISCORD_TOKEN;\nsetInterval(()=>{console.log('Bot running with token', token);},5000);\n")

    env_path = bot_dir / ".env"
    with open(env_path, "w") as env_file:
        env_file.write(f"DISCORD_TOKEN={token}\n")

    new_bot.bot_path = str(bot_dir)
    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)
    return new_bot


@app.get("/api/bots/{bot_id}", response_model=schemas.BotDetail)
async def get_bot(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@app.put("/api/bots/{bot_id}", response_model=schemas.BotDetail)
async def update_bot(
    bot_id: int,
    payload: schemas.BotUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(bot, field, value)
    db.commit()
    db.refresh(bot)
    return bot


@app.delete("/api/bots/{bot_id}")
async def delete_bot(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    await bot_manager.stop_bot(bot.id)
    bot_dir = Path(bot.bot_path)
    if bot_dir.exists():
        shutil.rmtree(bot_dir)
    log_path = LOGS_DIR / f"{bot.id}.log"
    if log_path.exists():
        log_path.unlink()
    db.delete(bot)
    db.commit()
    return {"detail": "Bot deleted"}


@app.post("/api/bots/{bot_id}/start")
async def start_bot(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    pid = await bot_manager.start_bot(bot.id, Path(bot.bot_path), bot.language, bot.entrypoint, bot.token)
    bot.status = "running"
    process = models.BotProcess(bot_id=bot.id, pid=pid, status="running")
    db.add(process)
    db.commit()
    db.refresh(bot)
    return {"pid": pid, "status": "running"}


@app.post("/api/bots/{bot_id}/stop")
async def stop_bot(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    stopped = await bot_manager.stop_bot(bot.id)
    bot.status = "stopped"
    db.commit()
    return {"stopped": stopped}


@app.post("/api/bots/{bot_id}/restart")
async def restart_bot(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    pid = await bot_manager.restart_bot(bot.id, Path(bot.bot_path), bot.language, bot.entrypoint, bot.token)
    bot.status = "running"
    db.commit()
    return {"pid": pid, "status": "running"}


@app.get("/api/bots/{bot_id}/status")
async def bot_status(bot_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    status_str = bot_manager.get_status(bot.id)
    bot.status = status_str
    db.commit()
    return {"status": status_str}


@app.get("/api/bots/{bot_id}/logs")
async def bot_logs(bot_id: int, lines: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    bot = db.query(models.Bot).filter(models.Bot.id == bot_id, models.Bot.owner_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    log_path = LOGS_DIR / f"{bot.id}.log"
    if not log_path.exists():
        return {"logs": []}
    with open(log_path, "r") as f:
        all_lines = f.readlines()
    tail = all_lines[-lines:]
    return {"logs": tail}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
