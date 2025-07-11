from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.templating import Jinja2Templates
from database import Base, engine
from sqlalchemy.orm import Session
from models import OrderQuestion, TodoQuestion, SeeQuestion, SpeakingQuestion, PairingQuestion
from typing import List
import json
import os
import shutil

router = APIRouter(prefix="/admin")

templates = Jinja2Templates(directory="templates")


Base.metadata.create_all(bind=engine)

def get_db():
    db = Session(bind=engine)
    try:
        print("connect")
        yield db
    finally:
        print("close")
        db.close()

@router.get("/pairing_mode")
async def pairing_mode(request: Request, db: Session = Depends(get_db)):
    pairing = db.query(PairingQuestion).order_by(PairingQuestion.stage.desc()).first()
    if not pairing:
        stage = 0
    else:
        stage = pairing.stage
    return templates.TemplateResponse("admin_sound1.html", {"request": request, "stage": stage})

@router.get("/pairing_mode/create/{stage}")
async def pairing_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("voicepic_addmin.html", {"request": request, "stage": stage})

@router.post("/pairing_mode/create/{stage}")
async def pairing_create(request: Request, stage:int, answer: int = Form(...), file_img: List[UploadFile] = File(...), file_sound: List[UploadFile] = File(...), db: Session = Depends(get_db), category=1):
    upload_at_s = "./static/pairing_mode/sounds"
    upload_at_i = "./static/pairing_mode/img"
    path_img = []
    path_sound = ""
    os.makedirs(upload_at_s, exist_ok=True)
    os.makedirs(upload_at_i, exist_ok=True)
    for file in file_img:
        file_path = os.path.join(upload_at_s, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_url = file_path.replace("\\", "/")[1:]
        path_img.append(file_url)
    for file in file_sound:
        file_path = os.path.join(upload_at_i, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_url = file_path.replace("\\", "/")[1:]
        path_sound = file_url
    pairing = PairingQuestion(
        stage=stage,
        path_img=f"{path_img}",
        path_sound=path_sound,
        answer=path_img[answer],
        category_id=category
    )
    db.add(pairing)
    db.commit()
    return 0

@router.get("/pairing_mode/edit/{stage}")
async def pairing_mode_edit(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})

@router.get("/speaking_mode")
async def speaking_mode(request: Request, db: Session = Depends(get_db)):
    speaking = db.query(SpeakingQuestion).order_by(SpeakingQuestion.stage.desc()).first()
    if not speaking:
        stage = 0
    else:
        stage = speaking.stage
    return templates.TemplateResponse("admin_sound2.html", {"request": request, "stage":stage})

@router.get("/speaking_mode/create/{stage}")
async def speaking_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("create_guess2.html", {"request": request, "stage":stage})

@router.get("/speaking_mode/edit/{stage}")
async def speaking_mode_edit(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})

@router.post("/speaking_mode/create/{stage}")
async def speaking_create(stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), category=1):
    upload_at = "./static/speaking/sounds"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    file_url = file_location.replace("\\", "/")[1:]
    speaking_question = SpeakingQuestion(
        stage=stage,
        path_sound=file_url,
        answer=answer,
        category_id=category
    )
    db.add(speaking_question)
    db.commit()
    return {"filename": file.filename, "answer": answer}

@router.get("/todo_mode")
async def todo_mode(request: Request, db: Session = Depends(get_db)):
    todo = db.query(TodoQuestion).order_by(TodoQuestion.stage.desc()).first()
    if not todo:
        stage = 0
    else:
        stage = todo.stage
    return templates.TemplateResponse("admin_guess1.html", {"request": request, "stage":stage})

@router.get("/todo_mode/create/{stage}")
async def todo_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("choosepic_admin.html", {"request": request, "stage":stage})

@router.post("/todo_mode/create/{stage}")
async def todo_create(request: Request, stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), l_order: str = Form(...), category=1):
    upload_at = "./static/todo/img"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    file_url = file_location.replace("\\", "/")[1:]
    todo_question = TodoQuestion(
        stage=stage,
        path_img=file_url,
        choice_4= json.loads(l_order),
        answer=answer,
        category_id=category
    )
    db.add(todo_question)
    db.commit()
    return {"filename": file.filename, "answer": answer}
 
@router.get("/todo_mode/edit/{stage}")
async def todo_mode_edit(request: Request, stage:int):
    return templates.TemplateResponse("choosepic_admin.html", {"request": request, "stage":stage})


@router.get("/what_you_see_mode")
async def what_you_see_mode(request: Request, db: Session = Depends(get_db)):
    see = db.query(SeeQuestion).order_by(SeeQuestion.stage.desc()).first()
    if not see:
        stage = 0
    else:
        stage = see.stage
    return templates.TemplateResponse("admin_guess2.html", {"request": request, "stage":stage})

@router.get("/what_you_see_mode/create/{stage}")
async def what_you_see_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("create_sound2.html", {"request": request, "stage":stage})

@router.post("/what_you_see_mode/create/{stage}")
async def what_you_see_create(request: Request, stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), category=1):
    upload_at = "./static/see/img"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    file_url = file_location.replace("\\", "/")[1:]
    see_question = SeeQuestion(
        stage=stage,
        path_img=file_url,
        answer=answer,
        category_id=category
    )
    db.add(see_question)
    db.commit()
    return 0

@router.get("/what_you_see_mode/edit/{stage}")
async def what_you_see_edit(request: Request, stage:int):
    return templates.TemplateResponse("create_sound2.html", {"request": request, "stage":stage})

@router.get("/order_mode")
async def order_mode(request: Request, db: Session = Depends(get_db)):
    order = db.query(OrderQuestion).order_by(OrderQuestion.stage.desc()).first()
    if not order:
        stage = 0
    else:
        stage = order.stage
    return templates.TemplateResponse("admin_guess3.html", {"request": request, "stage":stage})

@router.get("/order_mode/create/{stage}")
async def order_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("event_order_addmin.html", {"request": request, "stage":stage})

@router.post("/order_mode/create/{stage}")
async def order_create(request: Request, stage:int, answer: str = Form(...), db: Session = Depends(get_db), category=1):
    order_question = OrderQuestion(
        stage=stage,
        map_choice_4=answer,
        category_id=category
    )
    db.add(order_question)
    db.commit()
    return 0

@router.get("/order_mode/edit/{stage}")
async def order_mode_edit(request: Request, stage:int):
    return templates.TemplateResponse("event_order_addmin.html", {"request": request, "stage":stage})
