from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

router = APIRouter(prefix="/home")

templates = Jinja2Templates(directory="templates")

@router.get("")
async def home(request: Request):
    return templates.TemplateResponse("index2.html", {"request": request})

@router.get("/game_sound/pairing_mode")
async def pairing_mode(request: Request):
    return templates.TemplateResponse("main_sound1.html", {"request": request})

@router.get("/game_sound/pairing_mode/{id}")
async def play_pairing(request: Request, id: int):
    return templates.TemplateResponse("voicepic.html", {"request": request})

@router.get("/game_sound/speaking_mode")
async def speaking_mode(request: Request):
    return templates.TemplateResponse("main_sound2.html", {"request": request})

@router.get("/game_sound/speaking_mode/{id}")
async def play_speaking(request: Request, id: int):
    return templates.TemplateResponse("game_sound2.html", {"request": request})

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