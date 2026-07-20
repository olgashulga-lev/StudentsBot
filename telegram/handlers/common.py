from aiogram import Router, types
from aiogram.filters import Command


router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    text = """
<b> Привет! Я ********</b>

Я помогу тебе и твоим друзьям играть в интересную игру!

<b> Основные команды:</b>
/start - показать это сообщение
/registration
    """
    await message.answer(text)
