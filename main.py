from fastapi import FastAPI, Request, Form, Depends
from router import home_router, Admin
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from models import User, Category
from database import Base, engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=os.getenv("key_middle"))

load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID"))


templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

# ฟังก์ชันสร้างรหัสผ่านแฮช
def hash_password(password: str):
    return pwd_context.hash(password)

# ฟังก์ชันตรวจสอบรหัสผ่าน
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# welcome route
@app.get("/")
async def welcome(request: Request):
    msg = request.query_params.get("msg")
    return templates.TemplateResponse("index.html", {"request": request, "msg":msg})

@app.post("/login")
async def login(request: Request,
                  username: str = Form(...),
                  password: str = Form(...),
                  db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user.user_id == ADMIN_ID:
        return {"message": "admin"}
    elif user and verify_password(password, user.password):
        request.session["user_id"] = user.user_id
        return {"message": "เข้าสู่ระบบสำเร็จ"}
    else:
        return {"message": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

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
    check_user = db.query(User).filter(User.username == username).first()
    if (check_user):
        return {"message": "ชื่อผู้ใช้นี้มีผู้อื่นใช้แล้ว"}
    else:
        hashed_pw = hash_password(password)
        user = User(
            first_name=first_Name,
            last_name=last_Name,
            gender=gender,
            date=birth,
            username=username,
            password=hashed_pw,
            email=email
        )
        db.add(user)
        db.commit()
        return {"message": "สมัครสมาชิกสำเร็จ"}


app.include_router(home_router.router)
app.include_router(Admin.router)
