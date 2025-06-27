from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from compare import is_similar
import random
import os
import shutil

router = APIRouter(prefix="/home")

templates = Jinja2Templates(directory="templates")

@router.get("")
async def home(request: Request):
    return templates.TemplateResponse("index2.html", {"request": request})

@router.get("/game_sound/pairing_mode")
async def pairing_mode(request: Request):
    return templates.TemplateResponse("main_sound1.html", {"request": request})

@router.get("/game_sound/pairing_mode/{stage_id}")
async def play_pairing(request: Request, stage_id: int):
    sound = [
        "/static/sounds/sound1.mp3",
        "/static/sounds/sound2.mp3",
        "/static/sounds/sound3.mp3",
        "/static/sounds/sound4.mp3",
        ]
    images = [
        "/static/img/weather.jpg",
        "/static/img/bug.jpg",
        "/static/img/sea.jpg",
        "/static/img/pirot.jpg"
    ]
    answer = {
        "/static/sounds/sound1.mp3": "/static/img/weather.jpg",
        "/static/sounds/sound2.mp3": "/static/img/bug.jpg",
        "/static/sounds/sound3.mp3": "/static/img/sea.jpg",
        "/static/sounds/sound4.mp3": "/static/img/pirot.jpg",
    }
    random.shuffle(sound)
    random.shuffle(images)
    return templates.TemplateResponse("voicepic.html", {"request": request, "sound": sound, "images": images, "answer": answer})

@router.get("/game_sound/speaking_mode")
async def speaking_mode(request: Request):
    return templates.TemplateResponse("main_sound2.html", {"request": request})

@router.get("/game_sound/speaking_mode/{id}")
async def play_speaking(request: Request, id: int):
    return templates.TemplateResponse("game_sound2.html", {"request": request})

@router.post("/game_sound/speaking_mode/compare")
async def compare(request: Request, label: str = Form(...), file: UploadFile = File(...)):
    UPLOAD_FOLDER = "uploads"
    upload_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    target_path = f"static/sounds/{label}.wav"
    if not os.path.exists(target_path):
        return "Find the target file in not found"

    result, score = is_similar(target_path, upload_path)
    score_percent = round(float(score) * 100, 2)
    return {
        "score": score_percent,
        "result": "✅ เสียงคล้ายกัน" if result else "❌ ยังไม่ค่อยเหมือน ลองใหม่อีกครั้ง"
    }

@router.get("/game_sound/my_voice_mode")
async def my_voice_mode(request: Request):
    return templates.TemplateResponse("main_sound3.html", {"request": request})

@router.get("/game_sound/my_voice_mode/{id}")
async def play_my_voice(request: Request, id: int):
    return templates.TemplateResponse("game_sound3.html", {"request": request})



@router.get("/game_pic/todo_mode")
async def todo_mode(request: Request):
    return templates.TemplateResponse("main_guess1.html", {"request": request})

@router.get("/game_pic/todo_mode/{id}")
async def play_todo(request: Request, id: int):
    return templates.TemplateResponse("choosepic.html", {"request": request})

@router.get("/game_pic/what_you_see_mode")
async def what_you_see_mode(request: Request):
    return templates.TemplateResponse("main_guess2.html", {"request": request})

@router.get("/game_pic/what_you_see_mode/{id}")
async def play_what_you_see(request: Request, id: int):
    return templates.TemplateResponse("game_guess2.html", {"request": request})

@router.get("/game_pic/order_mode")
async def order_mode(request: Request):
    return templates.TemplateResponse("main_guess3.html", {"request": request})

@router.get("/game_pic/order_mode/{id}")
async def play_order(request: Request, id: int):
    return templates.TemplateResponse("event_order.html", {"request": request})