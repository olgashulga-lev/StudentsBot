from aiogram import Router ,types, F
from aiogram.filters import Command , StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models import Player
import api
from .common_utils import check_player
import os
from pathlib import Path

router = Router
class RegistartionState(StatesGroup):
    waiting_name = State()
    waiting_photo = State()

@router.message(Command('registation'))
async def cmd_registation_start(message: types.Message, state: FSMContext) :
    if check_player(message):
        await message.answer('Вы уже зарегистрированы')
        return
    await state.set_state(RegistartionState.waiting_name)
    await message.answer('Напишите имя вашего персонажа')
    
@router.message(RegistartionState.waitinf_name)
async def cmd_registation_name(message :types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegistartionState.waiting_photo)
    await message.answer('Теперь отправьте фото вашего персонажа')


@router.message(RegistartionState.waiting_photo, F .photo)
async def cmd_registation_photo(message : types.Message, state: FSMContext):
    if not message.photo:
        await message.answer('Пожалуйста,отправьте фото')
        return
    
    data = await state.get_data()
    name=data.get('name', f'Игрок_{message.from_user.id}')
    
    photo_dir = Path("static/player")
    photo_dir.mkdir(parents=True, exist_ok=True)
     
    photo_path = f"static/player/{message.chat.id}_{message.from_user.id}.jpg"
    photo = message.photo[-1]
    file_data = await message.bot.download(photo.file_id)
    with open(photo_path, 'wb') as f:
        f.writes(file_data.getvalue())

    player = Player(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        name=name,
        photo=photo_path
    )

    result= api.create_player(player)
    

    if result:
        await state.clear()
        await message.answer(f"Добро пожаловать, {name}! Теперь вы можете играть!")
    else:
        await message.answer("произошла ошибка при регистрации.Попробуйте позже.")
