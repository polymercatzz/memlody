from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from faster_whisper import WhisperModel
from database import Base, engine
from datetime import datetime
from sqlalchemy.orm import Session
from models import OrderQuestion, TodoQuestion, SeeQuestion, SpeakingQuestion, PairingQuestion, User, GameStageHistory
import ast
import random
import os
import shutil

router = APIRouter(prefix="/home")

templates = Jinja2Templates(directory="templates")

model = WhisperModel("base", compute_type="int8", device="cpu")

Base.metadata.create_all(bind=engine)

def get_db():
    db = Session(bind=engine)
    try:
        print("connect")
        yield db
    finally:
        print("close")
        db.close()

@router.get("/")
async def home(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    return templates.TemplateResponse("index2.html", {"request": request})

@router.get("/my_info")
async def my_info(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user = db.query(User).filter(User.user_id==user_id).first()
    user_age = calculate_age(user.date)
    return templates.TemplateResponse("information.html", {"request": request, "user":user, "user_age":user_age})

def calculate_age(birthdate):
    from datetime import datetime
    today = datetime.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

@router.get("/game_sound/pairing_mode")
async def pairing_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(PairingQuestion.stage).group_by(PairingQuestion.stage).order_by(PairingQuestion.stage).all()
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.game_type=="pairing_mode").order_by(GameStageHistory.stage.desc()).first()
    if not all_stage_raw:
        all_stage_raw = []
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    return templates.TemplateResponse("main_sound1.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage})

@router.get("/game_sound/pairing_mode/{stage}")
async def play_pairing(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    questions_data_raw = db.query(PairingQuestion).filter(PairingQuestion.stage==stage).all()
    if not questions_data_raw:
        return RedirectResponse(url="/home/game_sound/pairing_mode/")
    questions_data = [
    {
        "stage": question.stage,
        "path_img": ast.literal_eval(question.all_path_img),
        "path_sound": question.path_sound,
        "answer": question.answer,
        "category_id": question.category_id
    } for question in questions_data_raw
]
    return templates.TemplateResponse("voicepic.html", {"request": request, "questions": questions_data, "stage":stage})

@router.get("/game_sound/speaking_mode")
async def speaking_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(SpeakingQuestion.stage).group_by(SpeakingQuestion.stage).order_by(SpeakingQuestion.stage).all()
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.game_type=="speaking_mode").order_by(GameStageHistory.stage.desc()).first()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    return templates.TemplateResponse("main_sound2.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage})

@router.get("/game_sound/speaking_mode/{stage}")
async def play_speaking(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_sounds_raw = db.query(SpeakingQuestion).filter(SpeakingQuestion.stage==stage).order_by(SpeakingQuestion.speaking_id).all()
    if not all_sounds_raw:
        return RedirectResponse(url="/home/game_sound/speaking_mode/")
    all_sounds = [
    {
        "stage": question.stage,
        "path_sound": question.path_sound,
        "answer": question.answer
    }
    for question in all_sounds_raw
]
    # random.shuffle(all_sounds)
    return templates.TemplateResponse("game_sound2.html", {"request": request, "all_sounds": all_sounds, "stage":stage})

def is_similar(a, b, threshold=0.7):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() >= threshold

@router.post("/check_voice")
async def check_voice(request: Request, label: str = Form(...), file: UploadFile = File(...), answer: str = Form(...)):
    from pythainlp.tokenize import word_tokenize
    from pythainlp.util import normalize
    from pythainlp.corpus.common import thai_stopwords
    temp_path = f"uploads/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    segments, _ = model.transcribe(temp_path, language="th")
    full_text = "".join([segment.text for segment in segments])
    print("ถอดได้:", full_text)
    os.remove(temp_path)
    EXCLUDED_WORDS = {"เสียง", "รูป"}
    # 1. Normalize คำ (ลบวรรณยุกต์/สะกดให้เป็นมาตรฐาน)
    full_text_norm = normalize(full_text.strip())
    answer_norm = normalize(answer.strip())

    # 2. ตัดคำ
    words_in_text = word_tokenize(full_text_norm, engine="newmm")
    words_in_answer = word_tokenize(answer_norm, engine="newmm")

    # 3. ตัด stopwords (เอาคำฟุ่มเฟือยออก เช่น "ของ", "คือ")
    stopwords = thai_stopwords()
    filtered_text = [w for w in words_in_text if w not in stopwords and w not in EXCLUDED_WORDS]
    filtered_answer = [w for w in words_in_answer if w not in stopwords and w not in EXCLUDED_WORDS]

    print("คำที่พูด:", filtered_text)
    print("คำเฉลย:", filtered_answer)

    # 4. ตรวจสอบว่าคำเฉลยอย่างน้อย 1 คำ อยู่ในคำพูด หรือคล้ายกัน
    for ans_word in filtered_answer:
        for spoken_word in filtered_text:
            if ans_word in spoken_word or is_similar(ans_word, spoken_word):
                return "ถูกต้อง"

    return "ไม่ถูกต้อง"

@router.get("/game_sound/my_voice_mode")
async def my_voice_mode(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    return templates.TemplateResponse("main_sound3.html", {"request": request})

@router.get("/game_sound/my_voice_mode/{stage}")
async def play_my_voice(request: Request, stage: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
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
    return templates.TemplateResponse("game_sound3.html", {"request": request, "questions_cosins": questions_cosins, "stage":stage})

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
async def todo_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(TodoQuestion.stage).group_by(TodoQuestion.stage).order_by(TodoQuestion.stage).all()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.game_type=="todo_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    return templates.TemplateResponse("main_guess1.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage})

@router.get("/game_pic/todo_mode/{stage}")
async def play_todo(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    todo_list_raw = db.query(TodoQuestion).filter(TodoQuestion.stage==stage).order_by(TodoQuestion.todo_id).all()
    if not todo_list_raw:
        return RedirectResponse(url="/home/game_pic/todo_mode/")
    todo_list = [
        {
        "stage": question.stage,
        "path_img": question.path_img,
        "choice_4": ast.literal_eval(question.choice_4),
        "answer": question.answer,
        "category":question.category_id
        }
        for question in todo_list_raw
]
    return templates.TemplateResponse("choosepic.html", {"request": request, "todo_list": todo_list, "stage":stage})

@router.get("/game_pic/what_you_see_mode")
async def what_you_see_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(SeeQuestion.stage).group_by(SeeQuestion.stage).order_by(SeeQuestion.stage).all()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.game_type=="what_you_see_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    return templates.TemplateResponse("main_guess2.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage})

@router.get("/game_pic/what_you_see_mode/{stage}")
async def play_what_you_see(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    what_you_see_raw = db.query(SeeQuestion).filter(SeeQuestion.stage==stage).order_by(SeeQuestion.see_id).all()
    if not what_you_see_raw:
        return RedirectResponse(url="/home/game_pic/what_you_see_mode/")
    what_you_see = [
    {
        "stage": question.stage,
        "path_img": question.path_img,
        "answer": question.answer,
        "category":question.category_id
    }
    for question in what_you_see_raw
]
    return templates.TemplateResponse("game_guess2.html", {"request": request, "what_you_see": what_you_see, "stage":stage})

@router.get("/game_pic/order_mode")
async def order_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(OrderQuestion.stage).group_by(OrderQuestion.stage).order_by(OrderQuestion.stage).all()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.game_type=="what_you_see_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    return templates.TemplateResponse("main_guess3.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage})

@router.get("/game_pic/order_mode/{stage}")
async def play_order(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    order_questions_raw = db.query(OrderQuestion).filter(OrderQuestion.stage==stage).order_by(OrderQuestion.order_id).all()
    if not order_questions_raw:
        return RedirectResponse(url="/home/game_pic/order_mode/")
    order_questions = [
        {
        "order_id": question.order_id,
        "stage": question.stage,
        "map_choice_4": ast.literal_eval(question.map_choice_4),
        "category":question.category_id
        }
        for question in order_questions_raw
    ]
    all_map_choices = []
    for q in order_questions:
        choices = list(q['map_choice_4'])
        random.shuffle(choices)
        all_map_choices.append(choices)
    return templates.TemplateResponse("event_order.html", {"request": request, "order_questions": order_questions, "all_map_choices": all_map_choices, "stage":stage})

@router.post("/submit/{game}/{mode}/{stage}")
async def post_submit(request: Request, game: str, mode: str, stage: int, finished: str = Form(...), corrected: int = Form(...), time: int = Form(...)):
    if finished == "true":
        # ตั้งค่า session ว่าเล่นเกมจบแล้ว
        request.session[f"{game}_{mode}_{stage}_finished"] = True

    return RedirectResponse(url=f"/home/submit/{game}/{mode}/{stage}?corrected={corrected}&time={time}", status_code=303)  # 303 = redirect หลัง POST

# GET: แสดงผลเฉพาะถ้าเกมจบ
@router.get("/submit/{game}/{mode}/{stage}")
async def get_submit(request: Request, game: str, mode: str, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    key = f"{game}_{mode}_{stage}_finished"
    if request.session.get(key):
        del request.session[key]
        corrected = int(request.query_params.get('corrected', 0))
        time = float(request.query_params.get('time', 0))
        history = GameStageHistory(
            user_id=user_id,
            game_type=mode,
            stage=stage,
            total_questions=5,
            correct_count=corrected,
            incorrect_count=5-corrected,
            play_time=datetime.now(),
            duration=time
        )
        db.add(history)
        db.commit()
        return templates.TemplateResponse("sum.html", {"request": request, "game": game, "mode": mode, "stage":stage, "corrected":corrected, "time":time})
    return RedirectResponse(url=f"/home/{game}/{mode}", status_code=302)
