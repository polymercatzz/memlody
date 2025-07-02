from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from faster_whisper import WhisperModel
import random
import os
import shutil

router = APIRouter(prefix="/home")

templates = Jinja2Templates(directory="templates")

model = WhisperModel("medium", compute_type="int8", device="cpu")

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
    all_sounds = [
    {
        "id": 1,
        "stage": 1,
        "path_sound": "/static/sounds/sound1.mp3",
        "answer": "เสียงนกร้อง"
    },
    {
        "id": 2,
        "stage": 1,
        "path_sound": "/static/sounds/sound2.mp3",
        "answer": "เสียงหมาเห่า"
    },
    {
        "id": 3,
        "stage": 1,
        "path_sound": "/static/sounds/sound3.mp3",
        "answer": "เสียงแมวร้อง"
    },
    {
        "id": 4,
        "stage": 1,
        "path_sound": "/static/sounds/sound4.mp3",
        "answer": "เสียงฝนตก"
    },
    {
        "id": 5,
        "stage": 1,
        "path_sound": "/static/sounds/sound5.mp3",
        "answer": "เสียงรถวิ่ง"
    }
]
    # random.shuffle(all_sounds)
    return templates.TemplateResponse("game_sound2.html", {"request": request, "all_sounds": all_sounds})

@router.post("/check_voice")
async def check_voice(request: Request, label: str = Form(...), file: UploadFile = File(...), answer: str = Form(...)):
    temp_path = f"uploads/{file.filename}"
    with open (temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    segments, _ = model.transcribe(temp_path, language="th")
    full_text = "".join([segment.text for segment in segments])
    print(full_text)
    ##  เช็คคำตอบตรงๆก่อนเดี๋ยวจะหาวิธีที่ดีกว่านี้
    if full_text == answer:
        return "ถูกต้อง"
    else:
        return "ไม่ถูกต้อง"

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
    todo_list = [
    {
        "todo_id": 1,
        "stage": 1,
        "path_img": "/static/img/cat.png",
        "choice_4": ["แมว", "สุนัข", "นก", "ปลา"],
        "answer": "แมว"
    },
    {
        "todo_id": 2,
        "stage": 1,
        "path_img": "/static/img/banana.png",
        "choice_4": ["ส้ม", "กล้วย", "แอปเปิ้ล", "มะม่วง"],
        "answer": "กล้วย"
    },
    {
        "todo_id": 3,
        "stage": 1,
        "path_img": "/static/img/television.png",
        "choice_4": ["โทรศัพท์", "วิทยุ", "ทีวี", "ไมโครเวฟ"],
        "answer": "ทีวี"
    },
    {
        "todo_id": 4,
        "stage": 1,
        "path_img": "/static/img/spoon.png",
        "choice_4": ["มีด", "ตะเกียบ", "ช้อน", "ส้อม"],
        "answer": "ช้อน"
    },
    {
        "todo_id": 5,
        "stage": 1,
        "path_img": "/static/img/car.png",
        "choice_4": ["รถจักรยาน", "รถไฟ", "รถยนต์", "เครื่องบิน"],
        "answer": "รถยนต์"
    }
]
    return templates.TemplateResponse("choosepic.html", {"request": request, "todo_list": todo_list})

@router.get("/game_pic/what_you_see_mode")
async def what_you_see_mode(request: Request):
    return templates.TemplateResponse("main_guess2.html", {"request": request})

@router.get("/game_pic/what_you_see_mode/{id}")
async def play_what_you_see(request: Request, id: int):
    what_you_see = [
    {
        "id": 1,
        "stage": 1,
        "path_img": "/static/img/elephant.png",
        "answer": "ช้าง"
    },
    {
        "id": 2,
        "stage": 1,
        "path_img": "/static/img/dog.png",
        "answer": "สุนัข"
    },
    {
        "id": 3,
        "stage": 1,
        "path_img": "/static/img/apple.png",
        "answer": "แอปเปิ้ล"
    },
    {
        "id": 4,
        "stage": 1,
        "path_img": "/static/img/phone.png",
        "answer": "โทรศัพท์"
    },
    {
        "id": 5,
        "stage": 1,
        "path_img": "/static/img/fork.png",
        "answer": "ส้อม"
    }
    ]
    return templates.TemplateResponse("game_guess2.html", {"request": request, "what_you_see": what_you_see})

@router.get("/game_pic/order_mode")
async def order_mode(request: Request):
    return templates.TemplateResponse("main_guess3.html", {"request": request})

@router.get("/game_pic/order_mode/{id}")
async def play_order(request: Request, id: int):
    order_questions = [
    {
        "order_id": 1,
        "stage": 1,
        "map_choice_4": ["ตื่นนอน", "แปรงฟัน", "ล้างหน้า", "แต่งตัว"]
    },
    {
        "order_id": 2,
        "stage": 1,
        "map_choice_4": ["กินข้าวเช้า", "ไปโรงเรียน", "เรียนหนังสือ", "กลับบ้าน"]
    },
    {
        "order_id": 3,
        "stage": 2,
        "map_choice_4": ["อาบน้ำ", "ใส่ชุดนอน", "แปรงฟันก่อนนอน", "เข้านอน"]
    },
    {
        "order_id": 4,
        "stage": 2,
        "map_choice_4": ["เดินเข้าห้องน้ำ", "กดชักโครก", "ล้างมือ", "ออกจากห้องน้ำ"]
    },
    {
        "order_id": 5,
        "stage": 3,
        "map_choice_4": ["หยิบจาน", "ตักข้าว", "นั่งโต๊ะอาหาร", "กินข้าว"]
    }
]
    all_map_choices = []
    for q in order_questions:
        choices = list(q["map_choice_4"])
        random.shuffle(choices)

        all_map_choices.append(choices)
    print(all_map_choices)
    return templates.TemplateResponse("event_order.html", {"request": request, "order_questions": order_questions, "all_map_choices": all_map_choices})

@router.get("/submit/{game}/{mode}")
async def submit(request: Request):
    return templates.TemplateResponse("sum.html", {"request": request})

