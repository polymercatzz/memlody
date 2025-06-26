from fastapi import FastAPI, Request
from router import home_router
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# welcome route
@app.get("/")
async def welcome(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/login")
# async def login(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/register")
# async def register(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


app.include_router(home_router.router)
