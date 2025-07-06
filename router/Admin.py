from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/admin")

templates = Jinja2Templates(directory="templates")

@router.get("")
async def admin(request: Request):
    return templates.TemplateResponse("admin_sound1.html", {"request": request})