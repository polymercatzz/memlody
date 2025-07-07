from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.templating import Jinja2Templates
from faster_whisper import WhisperModel
from database import Base, engine
from sqlalchemy.orm import Session
from models import OrderQuestion, TodoQuestion, SeeQuestion, SpeakingQuestion
import json
import random
import os
import shutil

router = APIRouter(prefix="/home")

templates = Jinja2Templates(directory="templates")

model = WhisperModel("medium", compute_type="int8", device="cpu")

Base.metadata.create_all(bind=engine)

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

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
async def play_speaking(request: Request, id: int, db: Session = Depends(get_db)):
    all_sounds_raw = db.query(SpeakingQuestion).filter(SpeakingQuestion.stage==id).all()
    all_sounds = [
    {
        "stage": question.stage,
        "path_sound": question.path_sound,
        "answer": question.answer
    }
    for question in all_sounds_raw
]
    # random.shuffle(all_sounds)
    return templates.TemplateResponse("game_sound2.html", {"request": request, "all_sounds": all_sounds})

@router.get("/game_sound/speaking_mode_json")
async def get_speaking_questions_json(db: Session = Depends(get_db)):
    all_sounds_raw = db.query(SpeakingQuestion).filter(SpeakingQuestion.stage==1).all()
    print(all_sounds_raw)
    return all_sounds_raw


@router.post("/check_voice")
async def check_voice(request: Request, label: str = Form(...), file: UploadFile = File(...), answer: str = Form(...)):
    temp_path = f"uploads/{file.filename}"
    with open (temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    segments, _ = model.transcribe(temp_path, language="th")
    full_text = "".join([segment.text for segment in segments])
    print(full_text)
    os.remove(temp_path)
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
    cousins = [
    {
        "cousin_id": 1,
        "user_id": 101,
        "nickname": "พี่บอย",
        "relation": "พี่ชาย",
        "path_sound": "/static/sounds/cousin1.mp3",
        "path_img": "/static/img/cousin1.jpg"
    },
    {
        "cousin_id": 2,
        "user_id": 101,
        "nickname": "น้องแพร",
        "relation": "น้องสาว",
        "path_sound": "/static/sounds/cousin2.mp3",
        "path_img": "/static/img/cousin2.jpg"
    },
    {
        "cousin_id": 3,
        "user_id": 101,
        "nickname": "อาแดง",
        "relation": "อา",
        "path_sound": "/static/sounds/cousin3.mp3",
        "path_img": "/static/img/cousin3.jpg"
    },
    {
        "cousin_id": 4,
        "user_id": 101,
        "nickname": "น้าเอ๋",
        "relation": "น้า",
        "path_sound": "/static/sounds/cousin4.mp3",
        "path_img": "/static/img/cousin4.jpg"
    },
    {
        "cousin_id": 5,
        "user_id": 101,
        "nickname": "ลุงหมู",
        "relation": "ลุง",
        "path_sound": "/static/sounds/cousin5.mp3",
        "path_img": "/static/img/cousin5.jpg"
    }
]
    random.shuffle(cousins)
    questions_cosins = create_questions(cousins)
    return templates.TemplateResponse("game_sound3.html", {"request": request, "questions_cosins": questions_cosins})

def create_questions(cousins, num_questions=5, num_choices=4):
    questions = []

    for _ in range(num_questions):
        answer = random.choice(cousins)
        others = [c for c in cousins if c["cousin_id"] != answer["cousin_id"]]
        random.shuffle(others)

        choices = others[:num_choices - 1] + [answer]
        random.shuffle(choices)

        question = {
            "question_sound": answer["path_sound"],
            "choices": [
                {
                    "nickname": f'{c["nickname"]} ({c["relation"]})',
                    "path_img": c["path_img"]
                }
                for c in choices
            ],
            "correct_id": f'{answer["nickname"]} ({answer["relation"]})'
        }

        questions.append(question)

    return questions

@router.get("/game_pic/todo_mode")
async def todo_mode(request: Request):
    return templates.TemplateResponse("main_guess1.html", {"request": request})

@router.get("/game_pic/todo_mode/{id}")
async def play_todo(request: Request, id: int, db: Session = Depends(get_db)):
    todo_list_raw = db.query(TodoQuestion).filter(TodoQuestion.stage==id).all()
    todo_list = [
        {
        "stage": question.stage,
        "path_img": question.path_img,
        "choice_4": json.loads(question.choice_4),
        "answer": question.answer,
        "category":question.category_id
        }
        for question in todo_list_raw
]
    return templates.TemplateResponse("choosepic.html", {"request": request, "todo_list": todo_list})

@router.get("/game_pic/what_you_see_mode")
async def what_you_see_mode(request: Request):
    return templates.TemplateResponse("main_guess2.html", {"request": request})

@router.get("/game_pic/what_you_see_mode/{id}")
async def play_what_you_see(request: Request, id: int, db: Session = Depends(get_db)):
    what_you_see_raw = db.query(SeeQuestion).filter(SeeQuestion.stage==id).all()

    what_you_see = [
    {
        "stage": question.stage,
        "path_img": question.path_img,
        "answer": question.answer,
        "category":question.category_id
    }
    for question in what_you_see_raw
]
    return templates.TemplateResponse("game_guess2.html", {"request": request, "what_you_see": what_you_see})

@router.get("/game_pic/order_mode")
async def order_mode(request: Request):
    return templates.TemplateResponse("main_guess3.html", {"request": request})

@router.get("/game_pic/order_mode/{id}")
async def play_order(request: Request, id: int, db: Session = Depends(get_db)):
    order_questions_raw = db.query(OrderQuestion).filter(OrderQuestion.stage==id).all()
    order_questions = [
        {
        "order_id": question.order_id,
        "stage": question.stage,
        "map_choice_4": json.loads(question.map_choice_4),
        "category":question.category_id
         }
        for question in order_questions_raw
    ]
    print(order_questions)
    all_map_choices = []
    for q in order_questions:
        choices = list(q['map_choice_4'])
        random.shuffle(choices)

        all_map_choices.append(choices)
    return templates.TemplateResponse("event_order.html", {"request": request, "order_questions": order_questions, "all_map_choices": all_map_choices})

@router.get("/submit/{game}/{mode}")
async def submit(request: Request):
    return templates.TemplateResponse("sum.html", {"request": request})

