from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from router import home_router, Admin
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import User
from database import Base, engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

app = FastAPI()

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))


templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# welcome route
@app.get("/")
async def welcome(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login")
async def login(request: Request,
                  username: str = Form(...), 
                  password: str = Form(...),
                  db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    print(user.user_id == ADMIN_ID, type(ADMIN_ID), type(user.user_id))
    if user.user_id == ADMIN_ID:
        return {"message": "admin"}
    if user and user.password == password:
        return {"message": "เข้าสู่ระบบสำเร็จ"}
    else:
        return {"message": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}


@app.post("/register")
async def register(request: Request, 
                  first_Name: str = Form(...), 
                  last_Name: str = Form(...), 
                  birth: str = Form(...), 
                  gender: str = Form(...),
                  username: str = Form(...), 
                  password: str = Form(...), 
                  confirmPassword: str = Form(...), 
                  email: str = Form(...),
                  db: Session = Depends(get_db)):
    user = User(
        first_name=first_Name,
        last_name=last_Name,
        gender=gender,
        date=birth,
        username=username,
        password=password,
        email=email
    )
    db.add(user)
    db.commit()
    return 0


app.include_router(home_router.router)
app.include_router(Admin.router)
