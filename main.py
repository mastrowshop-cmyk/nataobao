import asyncio
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from tinydb import TinyDB, Query

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ---
db = TinyDB('db.json')
users_table = db.table('users')
User = Query()

# ТВОЙ ID (замени на свой!)
OWNER_ID = 7668402802 

TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = "https://mastrowshop-cmyk.github.io/nataobao/"

bot = Bot(token=TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ЛОГИКА ПРОВЕРКИ РОЛЕЙ ---
def get_user_role(tg_id):
    if tg_id == OWNER_ID:
        return "admin"
    res = users_table.get(User.id == tg_id)
    return res['role'] if res else "user"

# --- БОТ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Открыть Панель", web_app=WebAppInfo(url=WEB_APP_URL))]
    ])
    await message.answer(f"Твой ID: `{message.from_user.id}`\nРоль: {get_user_role(message.from_user.id)}", 
                         reply_markup=kb, parse_mode="Markdown")

# --- API ДЛЯ ПРИЛОЖЕНИЯ ---
@app.post("/api/auth")
async def auth(user_data: dict):
    uid = user_data.get('id')
    return {
        "role": get_user_role(uid),
        "tg_id": uid,
        "full_name": user_data.get("first_name", "User")
    }

# ДОБАВЛЕНИЕ АДМИНА/ОПЕРАТОРА (вызывается из панели)
@app.post("/api/admin/manage_user")
async def manage_user(data: dict):
    target_id = int(data.get("target_id"))
    new_role = data.get("role") # 'admin' или 'operator' или 'user'
    
    users_table.upsert({'id': target_id, 'role': new_role}, User.id == target_id)
    return {"status": "success", "message": f"ID {target_id} теперь {new_role}"}

@app.get("/api/packages/{tg_id}")
async def get_pkgs(tg_id: int):
    return [{"tracking_number": "TEST-123", "status": "На складе", "weight": 1.0, "cost": 500}]

# --- ЗАПУСК ---
async def main_loop():
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main_loop())
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
