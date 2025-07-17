from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from faster_whisper import WhisperModel
from database import Base, engine
from datetime import datetime
from sqlalchemy.orm import Session
from models import OrderQuestion, TodoQuestion, SeeQuestion, SpeakingQuestion, PairingQuestion, User, GameStageHistory, Category, Cousin
from datetime import datetime
from difflib import SequenceMatcher
from pythainlp.tokenize import word_tokenize
from pythainlp.util import normalize
from pythainlp.corpus.common import thai_stopwords
from collections import defaultdict
from statistics import mean, stdev
from sqlalchemy import func
from prophet import Prophet
import pandas as pd
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
    cousins = db.query(Cousin).filter(Cousin.user_id==user_id).all()
    return templates.TemplateResponse("information.html", {"request": request, "user":user, "user_age":user_age, "cousins":cousins})

@router.post("/create/cousin")
async def create_cousin(request: Request, db: Session = Depends(get_db), nickname: str= Form(...), relation: str = Form(...), path_img: UploadFile = File(...), path_sound: UploadFile = File(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    print(nickname, relation, path_img.filename, path_sound.filename)
    upload_at_s = "./static/cousin/sounds"
    upload_at_i = "./static/cousin/img"
    file_location = os.path.join(upload_at_s, f"{user_id}_{nickname}_{relation}_cousin_{path_sound.filename}")
    os.makedirs(upload_at_s, exist_ok=True)
    os.makedirs(upload_at_i, exist_ok=True)
    with open(file_location, "wb") as f:
        content = await path_sound.read()
        f.write(content)
    file_url_s = file_location.replace("\\", "/")[1:]
    file_location = os.path.join(upload_at_i, f"{user_id}_{nickname}_{relation}_cousin_{path_img.filename}")
    with open(file_location, "wb") as f:
        content = await path_img.read()
        f.write(content)
    file_url_i = file_location.replace("\\", "/")[1:]
    cousin = Cousin(
        user_id=user_id,
        nickname=nickname,
        relation=relation,
        path_sound=file_url_s,
        path_img=file_url_i
    )
    db.add(cousin)
    db.commit()
    return 0

def calculate_age(birthdate):
    today = datetime.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def weakness_list(user_data):
    weakness_by_stage = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0})

    for record in user_data:
        key = (record.game_type, record.stage)
        weakness_by_stage[key]["total"] += record.total_questions
        weakness_by_stage[key]["correct"] += record.correct_count
        weakness_by_stage[key]["incorrect"] += record.incorrect_count

    # คำนวณอัตราความผิดพลาด
    weakness_score = []
    for (game_type, stage), stats in weakness_by_stage.items():
        incorrect_rate = stats["incorrect"] / stats["total"] if stats["total"] > 0 else 0
        if stats["total"] >= 5:  # มีข้อมูลพอสมควร
            weakness_score.append({
                "game_type": game_type,
                "stage": stage,
                "incorrect_rate": incorrect_rate
        })

    # เรียงลำดับจากจุดที่อ่อนที่สุด
    weakness_score.sort(key=lambda x: x["incorrect_rate"], reverse=True)
    return weakness_score

@router.get("/game_sound/pairing_mode")
async def pairing_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(PairingQuestion.stage).group_by(PairingQuestion.stage).order_by(PairingQuestion.stage).all()
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type=="pairing_mode").order_by(GameStageHistory.stage.desc()).first()
    if not all_stage_raw:
        all_stage_raw = []
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    stage_max_point_raw  = db.query(func.max(GameStageHistory.correct_count)).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type == "pairing_mode", GameStageHistory.stage != 0).group_by(GameStageHistory.stage).order_by(GameStageHistory.stage).all()
    stage_max_point = [ point[0] for point in stage_max_point_raw]
    max_stage_row = db.query(func.max(PairingQuestion.stage)).first()
    if max_stage_row:
        max_stage = max_stage_row[0]
    else:
        max_stage = 0
    all_point = round(sum(stage_max_point)/(max_stage*5), 2)*100
    return templates.TemplateResponse("main_sound1.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage, "stage_max_point":stage_max_point, "all_point":all_point})

@router.get("/game_sound/pairing_mode/special")
async def pairing_special(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user_data = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "pairing_mode"
        ).all()
    weakness = weakness_list(user_data)
    print(weakness)
    weak_pairings = [
        w for w in weakness
        if w["game_type"] == "pairing_mode" and w["incorrect_rate"] > 0.5
    ]
    if not weak_pairings:
        return {"msg": "ไม่มีด่าน pairing_mode ที่ผิดเกิน 70%"}
    weak_stages = [w["stage"] for w in weak_pairings]
    all_questions = db.query(PairingQuestion).filter(
        PairingQuestion.stage.in_(weak_stages)).all()
    sample_questions = random.sample(all_questions, min(5, len(all_questions)))
    questions_data = [{
        "stage": q.stage,
        "path_img": ast.literal_eval(q.all_path_img),
        "path_sound": q.path_sound,
        "answer": q.answer,
        "category_id": q.category_id
        } for q in sample_questions
    ]
    return templates.TemplateResponse("voicepic.html", {"request": request, "questions": questions_data, "stage": "special", "category": "special"})

@router.get("/game_sound/pairing_mode/{stage}")
async def play_pairing(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    questions_data_raw = db.query(PairingQuestion).filter(PairingQuestion.stage==stage).all()
    if not questions_data_raw:
        return RedirectResponse(url="/home/game_sound/pairing_mode/")
    stg, category = db.query(PairingQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==PairingQuestion.category_id).filter(PairingQuestion.stage==stage).first()
    questions_data = [
    {
        "stage": question.stage,
        "path_img": ast.literal_eval(question.all_path_img),
        "path_sound": question.path_sound,
        "answer": question.answer,
        "category_id": question.category_id
    } for question in questions_data_raw
]
    return templates.TemplateResponse("voicepic.html", {"request": request, "questions": questions_data, "stage":stage, "category":category})

@router.get("/game_sound/speaking_mode")
async def speaking_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(SpeakingQuestion.stage).group_by(SpeakingQuestion.stage).order_by(SpeakingQuestion.stage).all()
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type=="speaking_mode").order_by(GameStageHistory.stage.desc()).first()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    stage_max_point_raw  = db.query(func.max(GameStageHistory.correct_count)).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type == "speaking_mode", GameStageHistory.stage != 0).group_by(GameStageHistory.stage).order_by(GameStageHistory.stage).all()
    stage_max_point = [ point[0] for point in stage_max_point_raw]
    max_stage_row = db.query(func.max(SpeakingQuestion.stage)).first()
    if max_stage_row:
        max_stage = max_stage_row[0]
    else:
        max_stage = 0
    all_point = round(sum(stage_max_point)/(max_stage*5), 2)*100
    return templates.TemplateResponse("main_sound2.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage, "stage_max_point":stage_max_point, "all_point":all_point})

@router.get("/game_sound/speaking_mode/special")
async def speaking_special(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user_data = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "speaking_mode"
        ).all()
    weakness = weakness_list(user_data)
    print(weakness)
    weak_pairings = [
        w for w in weakness
        if w["game_type"] == "speaking_mode" and w["incorrect_rate"] > 0.5
    ]
    if not weak_pairings:
        return {"msg": "ไม่มีด่าน speaking_mode ที่ผิดเกิน 70%"}
    weak_stages = [w["stage"] for w in weak_pairings]
    all_questions = db.query(SpeakingQuestion).filter(
        SpeakingQuestion.stage.in_(weak_stages)).all()
    sample_questions = random.sample(all_questions, min(5, len(all_questions)))
    questions_data = [{
        "stage": q.stage,
        "path_img": ast.literal_eval(q.all_path_img),
        "path_sound": q.path_sound,
        "answer": q.answer,
        "category_id": q.category_id
        } for q in sample_questions
    ]
    return templates.TemplateResponse("game_sound2.html", {"request": request, "questions": questions_data, "stage": "special", "category": "special"})

@router.get("/game_sound/speaking_mode/{stage}")
async def play_speaking(request: Request, stage: int, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_sounds_raw = db.query(SpeakingQuestion).filter(SpeakingQuestion.stage==stage).order_by(SpeakingQuestion.speaking_id).all()
    stg, category = db.query(SpeakingQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==SpeakingQuestion.category_id).filter(SpeakingQuestion.stage==stage).first()
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
    return templates.TemplateResponse("game_sound2.html", {"request": request, "all_sounds": all_sounds, "stage":stage, "category": category})

def is_similar(a, b, threshold=0.7):
    return SequenceMatcher(None, a, b).ratio() >= threshold

@router.post("/check_voice")
async def check_voice(request: Request, label: str = Form(...), file: UploadFile = File(...), answer: str = Form(...)):
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
async def my_voice_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    count_cousin = db.query(Cousin).filter(Cousin.user_id==user_id).count()
    return templates.TemplateResponse("main_sound3.html", {"request": request, "count_cousin":count_cousin})

@router.get("/game_sound/my_voice_mode/play")
async def play_my_voice(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    cousin_count = db.query(Cousin).filter(Cousin.user_id == user_id).count()
    if cousin_count < 5:
        return RedirectResponse(url="/home/my_info?msg=กรุณาเพิ่มข้อมูลญาติอย่างน้อย 5 คนก่อนเล่น", status_code=302)
    cousins_raw = db.query(Cousin).filter(Cousin.user_id == user_id).all()
    cousins = [
    {
        "cousin_id": cousin.cousin_id,
        "user_id": cousin.user_id,
        "nickname": cousin.nickname,
        "relation": cousin.relation,
        "path_sound": cousin.path_sound,
        "path_img": cousin.path_img
    }
        for cousin in cousins_raw
    ]
    random.shuffle(cousins)
    questions_cosins = create_questions(cousins)
    return templates.TemplateResponse("game_sound3.html", {"request": request, "questions_cosins": questions_cosins, "category": "ครอบครัว"})

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
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type=="todo_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    stage_max_point_raw  = db.query(func.max(GameStageHistory.correct_count)).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type == "speaking_mode", GameStageHistory.stage != 0).group_by(GameStageHistory.stage).order_by(GameStageHistory.stage).all()
    stage_max_point = [ point[0] for point in stage_max_point_raw]
    max_stage_row = db.query(func.max(TodoQuestion.stage)).first()
    if max_stage_row:
        max_stage = max_stage_row[0]
    else:
        max_stage = 0
    all_point = round(sum(stage_max_point)/(max_stage*5), 2)*100
    return templates.TemplateResponse("main_guess1.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage, "stage_max_point":stage_max_point, "all_point":all_point})

@router.get("/game_sound/todo_mode/special")
async def todo_special(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user_data = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "todo_mode"
        ).all()
    weakness = weakness_list(user_data)
    print(weakness)
    weak_pairings = [
        w for w in weakness
        if w["game_type"] == "todo_mode" and w["incorrect_rate"] > 0.5
    ]
    if not weak_pairings:
        return {"msg": "ไม่มีด่าน todo_mode ที่ผิดเกิน 70%"}
    weak_stages = [w["stage"] for w in weak_pairings]
    all_questions = db.query(TodoQuestion).filter(
        TodoQuestion.stage.in_(weak_stages)).all()
    sample_questions = random.sample(all_questions, min(5, len(all_questions)))
    questions_data = [{
        "stage": q.stage,
        "path_img": ast.literal_eval(q.all_path_img),
        "path_sound": q.path_sound,
        "answer": q.answer,
        "category_id": q.category_id
        } for q in sample_questions
    ]
    return templates.TemplateResponse("game_sound2.html", {"request": request, "questions": questions_data, "stage": "special", "category": "special"})

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
    stg, category = db.query(TodoQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==TodoQuestion.category_id).filter(TodoQuestion.stage==stage).first()
    return templates.TemplateResponse("choosepic.html", {"request": request, "todo_list": todo_list, "stage":stage, "category": category})

@router.get("/game_pic/what_you_see_mode")
async def what_you_see_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(SeeQuestion.stage).group_by(SeeQuestion.stage).order_by(SeeQuestion.stage).all()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type=="what_you_see_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    stage_max_point_raw  = db.query(func.max(GameStageHistory.correct_count)).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type == "what_you_see_mode", GameStageHistory.stage != 0).group_by(GameStageHistory.stage).order_by(GameStageHistory.stage).all()
    stage_max_point = [ point[0] for point in stage_max_point_raw]
    max_stage_row = db.query(func.max(SeeQuestion.stage)).first()
    if max_stage_row:
        max_stage = max_stage_row[0]
    else:
        max_stage = 0
    all_point = round(sum(stage_max_point)/(max_stage*5), 2)*100
    return templates.TemplateResponse("main_guess2.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage, "stage_max_point":stage_max_point, "all_point":all_point})

@router.get("/game_sound/what_you_see_mode/special")
async def what_you_see_special(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user_data = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "what_you_see_mode"
        ).all()
    weakness = weakness_list(user_data)
    print(weakness)
    weak_pairings = [
        w for w in weakness
        if w["game_type"] == "what_you_see_mode" and w["incorrect_rate"] > 0.5
    ]
    if not weak_pairings:
        return {"msg": "ไม่มีด่าน what_you_see_mode ที่ผิดเกิน 70%"}
    weak_stages = [w["stage"] for w in weak_pairings]
    all_questions = db.query(SeeQuestion).filter(
        SeeQuestion.stage.in_(weak_stages)).all()
    sample_questions = random.sample(all_questions, min(5, len(all_questions)))
    questions_data = [{
        "stage": q.stage,
        "path_img": ast.literal_eval(q.all_path_img),
        "path_sound": q.path_sound,
        "answer": q.answer,
        "category_id": q.category_id
        } for q in sample_questions
    ]
    return templates.TemplateResponse("game_sound2.html", {"request": request, "questions": questions_data, "stage": "special", "category": "special"})

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
    stg, category = db.query(SeeQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==SeeQuestion.category_id).filter(SeeQuestion.stage==stage).first()
    return templates.TemplateResponse("game_guess2.html", {"request": request, "what_you_see": what_you_see, "stage":stage, "category":category})

@router.get("/game_pic/order_mode")
async def order_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    all_stage_raw = db.query(OrderQuestion.stage).group_by(OrderQuestion.stage).order_by(OrderQuestion.stage).all()
    all_stage = [(index, stage[0]) for index, stage in enumerate(all_stage_raw)]
    history_stage_raw = db.query(GameStageHistory).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type=="what_you_see_mode").order_by(GameStageHistory.stage.desc()).first()
    history_stage = history_stage_raw.stage if history_stage_raw else 0
    stage_max_point_raw  = db.query(func.max(GameStageHistory.correct_count)).filter(GameStageHistory.user_id == user_id, GameStageHistory.game_type == "order_mode", GameStageHistory.stage != 0).group_by(GameStageHistory.stage).order_by(GameStageHistory.stage).all()
    stage_max_point = [ point[0] for point in stage_max_point_raw]
    max_stage_row = db.query(func.max(OrderQuestion.stage)).first()
    if max_stage_row:
        max_stage = max_stage_row[0]
    else:
        max_stage = 0
    all_point = round(sum(stage_max_point)/(max_stage*5), 2)*100
    print(all_point)
    return templates.TemplateResponse("main_guess3.html", {"request": request, "all_stage":all_stage, "history_stage":history_stage, "stage_max_point":stage_max_point, "all_point":all_point})

@router.get("/game_sound/order_mode/special")
async def order_special(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    user_data = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "order_mode"
        ).all()
    weakness = weakness_list(user_data)
    print(weakness)
    weak_pairings = [
        w for w in weakness
        if w["game_type"] == "order_mode" and w["incorrect_rate"] > 0.5
    ]
    if not weak_pairings:
        return {"msg": "ไม่มีด่าน order_mode ที่ผิดเกิน 70%"}
    weak_stages = [w["stage"] for w in weak_pairings]
    all_questions = db.query(OrderQuestion).filter(
        OrderQuestion.stage.in_(weak_stages)).all()
    sample_questions = random.sample(all_questions, min(5, len(all_questions)))
    questions_data = [{
        "stage": q.stage,
        "path_img": ast.literal_eval(q.all_path_img),
        "path_sound": q.path_sound,
        "answer": q.answer,
        "category_id": q.category_id
        } for q in sample_questions
    ]
    return templates.TemplateResponse("game_sound2.html", {"request": request, "questions": questions_data, "stage": "special", "category": "special"})

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
    stg, category = db.query(SeeQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==SeeQuestion.category_id).filter(SeeQuestion.stage==stage).first()
    return templates.TemplateResponse("event_order.html", {"request": request, "order_questions": order_questions, "all_map_choices": all_map_choices, "stage":stage, "category":category})

@router.post("/submit/{game}/{mode}/{stage}")
async def post_submit(request: Request, game: str, mode: str, stage: str, finished: str = Form(...), corrected: int = Form(...), time: int = Form(...)):
    if finished == "true":
        # ตั้งค่า session ว่าเล่นเกมจบแล้ว
        request.session[f"{game}_{mode}_{stage}_finished"] = True

    return RedirectResponse(url=f"/home/submit/{game}/{mode}/{stage}?corrected={corrected}&time={time}", status_code=303)  # 303 = redirect หลัง POST

# GET: แสดงผลเฉพาะถ้าเกมจบ
@router.get("/submit/{game}/{mode}/{stage}")
async def get_submit(request: Request, game: str, mode: str, stage: str, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")
    key = f"{game}_{mode}_{stage}_finished"
    if request.session.get(key):
        del request.session[key]
        corrected = int(request.query_params.get('corrected', 0))
        time = float(request.query_params.get('time', 0))
        if stage == "special":
            stage_value = 0
        else:
            stage_value = int(stage)
        history = GameStageHistory(
            user_id=user_id,
            game_type=mode,
            stage=stage_value,
            total_questions=5,
            correct_count=corrected,
            incorrect_count=5-corrected,
            play_time=datetime.now(),
            duration=time
        )
        db.add(history)
        db.commit()
        print(stage_value)
        return templates.TemplateResponse("sum.html", {"request": request, "game": game, "mode": mode, "stage":stage_value, "corrected":corrected, "time":time})
    return RedirectResponse(url=f"/home/{game}/{mode}", status_code=302)

def calculate_stat(all_history_raw=[],stage_category_raw=[]):
    stage_to_category = {}
    for stage, cat_name in stage_category_raw:
        stage_to_category[stage] = cat_name
    
    grouped_data = defaultdict(lambda: {
        "duration": [],
        "correct_count": [],
        "incorrect_count": [],
        "total_questions": []
    })
    category_accuracy_data = defaultdict(list)

    for history in all_history_raw:
        stage = history.stage
        grouped_data[stage]["duration"].append(history.duration)
        grouped_data[stage]["correct_count"].append(history.correct_count)
        grouped_data[stage]["incorrect_count"].append(history.incorrect_count)
        grouped_data[stage]["total_questions"].append(history.total_questions)
        if stage in stage_to_category:
            accuracy_percent = (history.correct_count / history.total_questions) * 100
            category = stage_to_category[stage]
            category_accuracy_data[category].append(accuracy_percent)

    # แปลงเป็นรูปแบบที่ frontend ต้องการ
    stageData = {}
    avg_duration = []
    avg_accuracy = []
    all_corrects = []
    all_totals = []
    for stage, data in grouped_data.items():
        durations = data["duration"]
        corrects = data["correct_count"]
        totals = data["total_questions"]

        # คำนวณ accuracy เป็นเปอร์เซ็นต์
        accuracy = [
            round((c / t) * 100) if t else 0
            for c, t in zip(corrects, totals)
        ]

        all_corrects.extend(corrects)
        all_totals.extend(totals)

        stageData[str(stage)] = {
            "time": durations,
            "accuracy": accuracy
        }
        
        # คำนวณค่าเฉลี่ยเวลา และค่าเฉลี่ยความถูกต้อง (accuracy)
        avg_duration.append(round(mean(durations), 2) if durations else 0)
        avg_accuracy.append(round(mean(accuracy), 2) if accuracy else 0)

    category_avg_accuracy = {
        category: round(mean(acc_list), 1) if acc_list else 0
        for category, acc_list in category_accuracy_data.items()
    }
    # สรุปความแม่นยำมาและะน้อยสุดของแต่ละ category
    if category_avg_accuracy:
        most_skilled_category = max(category_avg_accuracy, key=category_avg_accuracy.get)
        least_skilled_category = min(category_avg_accuracy, key=category_avg_accuracy.get)
        
        most_skilled_category_avg = category_avg_accuracy[most_skilled_category]
        least_skilled_category_avg = category_avg_accuracy[least_skilled_category]
    else:
        most_skilled_category = "-"
        least_skilled_category = "-"
        most_skilled_category_avg = 0
        least_skilled_category_avg = 0

    if all_totals:
        overall_accuracy = round((sum(all_corrects) / sum(all_totals)) * 100, 2)
    else:
        overall_accuracy = 0
    all_durations = [d for data in grouped_data.values() for d in data["duration"]]
    overall_avg_time = round(mean(all_durations), 2) if all_durations else 0
    return {
        "stages": list(stageData.keys()),
        "stageData": stageData,
        "avg_duration":avg_duration,
        "avg_accuracy":avg_accuracy,
        "overall_accuracy": overall_accuracy,
        "category_avg_accuracy": list(category_avg_accuracy.values()),
        "category": list(category_avg_accuracy.keys(),),
        "overall_avg_time": overall_avg_time,
        "most_skilled_category": most_skilled_category,
        "least_skilled_category": least_skilled_category,
        "most_skilled_category_avg": most_skilled_category_avg,
        "least_skilled_category_avg": least_skilled_category_avg
    }


def analyze_accuracy_trend_with_prophet(history_list):
    ts_data = []

    for h in history_list:
        if h.total_questions > 0 and hasattr(h, "play_time"):
            accuracy = (h.correct_count / h.total_questions) * 100
            ts_data.append({
                "ds": h.play_time,
                "y": round(accuracy, 2)
            })

    if len(ts_data) < 10:
        return "ไม่มีข้อมูลเพียงพอสำหรับการวิเคราะห์แนวโน้ม (ต้องมีอย่างน้อย 10 รายการ)"

    df = pd.DataFrame(ts_data)
    df.sort_values("ds", inplace=True)

    model_prophet = Prophet()
    model_prophet.fit(df)
    future = model_prophet.make_future_dataframe(periods=3)
    forecast = model_prophet.predict(future)

    last_actual = df["y"].iloc[-1]
    avg_future = round(forecast["yhat"].iloc[-3:].mean(), 2)

    # แนวโน้ม
    if avg_future > last_actual + 3:
        trend = "เพิ่มขึ้น"
        message = (
            "🎉 เยี่ยมมากเลย! ความแม่นยำของคุณกำลัง **พัฒนาดีขึ้นอย่างต่อเนื่อง** "
            "แสดงถึงความตั้งใจและความก้าวหน้า รักษาความสม่ำเสมอแบบนี้ต่อไปนะคะ คุณทำได้ดีมากจริง ๆ ❤️"
        )
    elif avg_future < last_actual - 3:
        trend = "ลดลง"
        message = (
            "🫂 อย่าเพิ่งหมดกำลังใจนะคะ แม้ความแม่นยำจะลดลงบ้าง "
            "แต่ทุกก้าวคือการเรียนรู้ ลองพักแล้วกลับมาสู้ใหม่นะ คุณยังไปต่อได้แน่นอน ✨"
        )
    else:
        trend = "ทรงตัว"
        message = (
            "📈 คุณรักษาความเสถียรได้ดีมากเลย! ความแม่นยำคงที่แสดงถึงการควบคุมตัวเองได้ดี "
            "ลองต่อยอดอีกนิด แล้วจะเก่งขึ้นอีกแน่นอนนะคะ 😊"
        )

    # วิเคราะห์จุดเด่น
    accuracy_list = [d["y"] for d in ts_data]
    avg_accuracy = round(mean(accuracy_list), 2)
    accuracy_std = round(stdev(accuracy_list), 2) if len(accuracy_list) > 1 else 0

    highlights = []
    if avg_accuracy >= 80:
        highlights.append(f"- ความแม่นยำเฉลี่ยสูง ({avg_accuracy}%) — เยี่ยมมากเลย!")
    if accuracy_std < 10:
        highlights.append("- รักษาความสม่ำเสมอได้ดีมาก (ค่าความแปรปรวนน้อย)")

    highlights = highlights[:2]  # จำกัดแค่ 2 ข้อ

    return (
        "✅ จุดที่คุณทำได้ดี\n"
        + "\n".join(highlights) + "\n\n"
        + f"🔮 แนวโน้ม: ความแม่นยำของคุณกำลัง **{trend}** "
        + f"(จาก {last_actual}% → เฉลี่ย {avg_future}%)\n"
        + message
    )

@router.get("/stat/pairing_mode")
async def stat_pairing_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "pairing_mode"
    ).all()
    stage_category_raw  = db.query(PairingQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==PairingQuestion.category_id).distinct(Category.category_name, PairingQuestion.stage).order_by(PairingQuestion.stage).all()
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_sound.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })

@router.get("/stat/speaking_mode")
async def stat_speaking_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "speaking_mode"
    ).all()
    stage_category_raw  = db.query(SpeakingQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==SpeakingQuestion.category_id).distinct(Category.category_name, SpeakingQuestion.stage).order_by(SpeakingQuestion.stage).all()
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_sound1.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })

@router.get("/stat/my_voice_mode")
async def stat_my_voice_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "my_voice_mode"
    ).all()
    stage_category_raw  = [(1, "ครอบครัว")]
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_sound2.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })

@router.get("/stat/todo_mode")
async def stat_todo_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "todo_mode"
    ).all()
    stage_category_raw  = db.query(TodoQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==TodoQuestion.category_id).distinct(Category.category_name, TodoQuestion.stage).order_by(TodoQuestion.stage).all()
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_pic.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })

@router.get("/stat/what_you_see_mode")
async def stat_what_you_see_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "what_you_see_mode"
    ).all()
    stage_category_raw  = db.query(SeeQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==SeeQuestion.category_id).distinct(Category.category_name, SeeQuestion.stage).order_by(SeeQuestion.stage).all()
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_pic1.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })

@router.get("/stat/order_mode")
async def stat_order_mode(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/?msg=กรุณาเข้าสู่ระบบ")

    all_history_raw = db.query(GameStageHistory).filter(
        GameStageHistory.user_id == user_id,
        GameStageHistory.game_type == "order_mode"
    ).all()
    stage_category_raw  = db.query(OrderQuestion.stage, Category.category_name).outerjoin(Category, Category.category_id==OrderQuestion.category_id).distinct(Category.category_name, OrderQuestion.stage).order_by(OrderQuestion.stage).all()
    calculate_data = calculate_stat(all_history_raw, stage_category_raw)
    prophet_text_summary = analyze_accuracy_trend_with_prophet(all_history_raw)
    return templates.TemplateResponse("stat_pic2.html", {
        "request": request,
        "stages": calculate_data["stages"],
        "stageData": calculate_data["stageData"],
        "avg_duration": calculate_data["avg_duration"],
        "avg_accuracy": calculate_data["avg_accuracy"],
        "overall_accuracy": calculate_data["overall_accuracy"],
        "category_avg_accuracy": calculate_data["category_avg_accuracy"],
        "category": calculate_data["category"],
        "overall_avg_time": calculate_data["overall_avg_time"],
        "most_skilled_category": calculate_data["most_skilled_category"],
        "least_skilled_category": calculate_data["least_skilled_category"],
        "most_skilled_category_avg": calculate_data["most_skilled_category_avg"],
        "least_skilled_category_avg": calculate_data["least_skilled_category_avg"],
        "prophet_text_summary": prophet_text_summary
    })