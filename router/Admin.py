from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from fastapi.templating import Jinja2Templates
from database import Base, engine
from sqlalchemy.orm import Session
from models import OrderQuestion, TodoQuestion, SeeQuestion, SpeakingQuestion
import json
import os

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
async def pairing_mode(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})

@router.get("/pairing_mode/create")
async def pairing_mode_create(request: Request):
    return templates.TemplateResponse("voicepic_addmin.html", {"request": request})

@router.get("/pairing_mode/edit/{stage}")
async def pairing_mode_edit(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})

@router.get("/speaking_mode")
async def speaking_mode(request: Request, db: Session = Depends(get_db)):
    speaking = db.query(SpeakingQuestion).order_by(SpeakingQuestion.stage.desc()).first()
    return templates.TemplateResponse("admin_sound2.html", {"request": request, "stage":speaking.stage})

@router.get("/speaking_mode/create/{stage}")
async def speaking_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("create_guess2.html", {"request": request, "stage":stage})

@router.get("/speaking_mode/edit/{stage}")
async def speaking_mode_edit(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})

@router.post("/speaking_mode/create/{stage}")
async def speaking_create(stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), category=1):
    upload_at = "./uploads/speaking/sounds"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    speaking_question = SpeakingQuestion(
        stage=stage,
        path_sound=file_location,
        answer=answer,
        category_id=category
    )
    db.add(speaking_question)
    db.commit()
    return {"filename": file.filename, "answer": answer}

@router.get("/todo_mode")
async def todo_mode(request: Request, db: Session = Depends(get_db)):
    todo = db.query(TodoQuestion).order_by(TodoQuestion.stage.desc()).first()
    return templates.TemplateResponse("admin_guess1.html", {"request": request, "stage":todo.stage})

@router.get("/todo_mode/create/{stage}")
async def todo_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("choosepic_admin.html", {"request": request, "stage":stage})

@router.post("/todo_mode/create/{stage}")
async def todo_create(request: Request, stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), l_order: str = Form(...), category=1):
    upload_at = "./uploads/todo/img"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    todo_question = TodoQuestion(
        stage=stage,
        path_img=file_location,
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
    return templates.TemplateResponse("admin_guess2.html", {"request": request, "stage":see.stage})

@router.get("/what_you_see_mode/create/{stage}")
async def what_you_see_mode_create(request: Request, stage:int):
    return templates.TemplateResponse("create_sound2.html", {"request": request, "stage":stage})

@router.post("/what_you_see_mode/create/{stage}")
async def what_you_see_create(request: Request, stage:int, answer: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), category=1):
    upload_at = "./uploads/see/img"
    file_location = os.path.join(upload_at, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    see_question = SeeQuestion(
        stage=stage,
        path_img=file_location,
        answer=answer,
        category_id=category
    )
    db.add(see_question)
    db.commit()
    return 0

@router.post("/what_you_see_mode/edit/{stage}")
async def what_you_see_edit(request: Request, stage:int):
    return templates.TemplateResponse("create_sound2.html", {"request": request, "stage":stage})

@router.get("/order_mode")
async def order_mode(request: Request):
    return templates.TemplateResponse("admin_guess3.html", {"request": request})