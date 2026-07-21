import os
from aiogram import Router, types
from aiogram.filters import Command
import api
from .common_utils import get_player_or_none
from aiogram.types import FSInputFile

router = Router()

@router.message(Command("avatar"))
async def cmd_avatar(message: types.Message):
    player=get_player_or_none(message)
    if not player:
        await message.answer("Сначала нужно пройти регистрацию")
        return
    lvl_player=player.level 
    max2_level=player.max_level()
    if lvl_player<max2_level:
        need_exp_for_next_level=player.exp_next_level()
        stroke_exp=f"Опыт: {player.exp}/{need_exp_for_next_level}"
    else:
        stroke_exp="Достигнут максимальный уровень"
    text=f"""
    <b>{player.name}</b>

    Уровень: {player.level}/20
    {stroke_exp}
    HP:{player.hp}/100
    Урон: {player.damage}
    Удача: {int(player.luck*100)}
    Деньги: {player.money}
    """
    # Проверяем существует ли файл
    if os.path.exists(player.photo):
        try:
            photo = FSInputFile(player.photo)
            await message.answer_photo(photo=photo,caption=text)
        except Exception as e:
           print(f"Ошибка при отправки фото:{e}")
           await message.answer(text)
            
    else:
        # Если файл не найден, отправляем только текст
        await message.answer(text)

@router.message(Command("achievement"))
async def cmd_achievement(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    achievements = api.get_user_achievements(message.chat.id, message.from_user.id)
    
    if not achievements:
        await message.answer("Нет достижений")
        return
    
    text = f"<b>Достижения {player.name}:</b>\n\n"
    
    for ach in achievements[0, 10]:
        text += f"<b>{ach.name}</b>\n"

    
    if len(achievements) > 10:
        text += f"\n... и еще {len(achievements) - 10} достижений"
    
    await message.answer(text)
