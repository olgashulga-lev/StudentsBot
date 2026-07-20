from aiogram import Router, types, F
from aiogram.filters import Command

import api
from .common_utils import get_player_or_none
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
router=Router()
@router.message(Command("use"))
async def cmt_use_item(message:types.message):
    player=get_player_or_none(message)
    if not player:
        await message.answer("У нас нет предметов")
        return 
    inventory=api.get_inventory(message.chat.id, message.from_user.id)
    if not inventory:
        await message.answer("У нас нет предмета")
        return
    usable_items=[ i for i in inventory if i.get("type")=="shop" and i.get("quantity",0)>0]
    permanent_items=[ i for i in inventory if i.get("type")=="permanent"]
    if not usable_items:
       await message.answer(" у  вас нет расходуемых предметов для ипользования")
       return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for item in usable_items:
        if item.get("item_id") in [1,2]:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{item.get('name')}(x{item.get('quantity')})",
                    callback_data=f"use_item_{item.get('id')}_{item.get('item_id')}"

                )
            ])
        if not keyboard.inline_kyeboard:
            await message.answer("нет расходуемых предметов для использования")
            return
        await message.answer(
            "Выберите предмет для использования:\n\n"
            "Зелье здоровья - восстанавливает 20 HP\n"
            "Зелье урона - +10 к урона на 1 бой",
            reply_markup=keyboard
        )
    
@router.callback.query(F.data.startwith('use_item_'))
async def cmd_use_item_callback(callback:types.CallbackQuery):
    data=callback.data.split('_')
    if len (data)<3:
        await callback.answer("Ошибка!")
        return
    try:
        inventory_id=int(data[2])
        item_id=int(data[3])
    except ValueError:
        await callback.asnwer("Ошибка!")
        return
    player= api.get_player(callback.message.chat.id,callback.from_user.id)
    if not player:
        await callback.answer("Сначала пройдите регистрацию!")
        return
    chat_id=callback.message.chat.id
    user_id=callback.from_user.id
    if item_id==1:
        heal_amount=20
        player.hp=min(100,player.hp+heal_amount)
        api.update_player(player)
        if api.remove_item_from_inventory(chat_id,user_id,item_id):
            await callback.answer(f"+{heal_amount} HP! Текущее HP:{player.hp}")
            await callback.message.edit_text(
                f"Вы использовали зелье здоровья!\n"
                f"Восстановлено:{heal_amount}HP\n"
                f"Текущее HP:{player.hp}"
            )
        else:
            await callback.answer("Ошибка при использовании предмета!")
    elif item_id==2:
        duration=300
        api.apply_effect(chat_id,user_id,'damage_bonus',10,duration)
        if api.remove_item_from_inventory(chat_id,user_id,item_id):
            await callback.answer(f"+ 10 к урону! Текущий урон:{player.damage}")
            await callback.message.edit_text(
                f"Вы использовали зелье урона!\n"
            )
        else:
            await callback.answer("Ошибка при использовании предмета!")      
    else:
        await callback.answer("Такого предмета нет!")  
@router.message(Command("effect"))
async def cmd_show_effects(message:types.Message):
    player= get_player_or_none(message)
    if not player:
        await message.answer("Сначала пройдите регистрацию!")
        return
    effects = api.get_active_effect(message.chat.id,message.from_user.id)
    inventory =api.get_inventory(message.chat.id,message.from_user.id)
    permament_bonuses = []
    for item in inventory:
        if item.get('type')== 'permanent':
            if item.get ('item_id')== 3:
                permament_bonuses.append("Меч: +15 к урону(постоянно)")
            elif item.get('item_id')==4:
                permament_bonuses.append("Броня: +20 к HP (постоянно)")
    text="<b>Активные эффекты</b>\n\n"
    if permament_bonuses:
        text+="<b>Постоянные улучшения:</b>\n"
        for bonus in permament_bonuses:
            text+=f"{bonus}\n"
        text+= "\n"
    if not effects and not permament_bonuses:
        await message.answer("У вас нет постоянных улучшений!")
        return
    effect_names={
        'damage_bonus':'Урон(временный)'
    }
    if effects:
        text+="<b>Временные эффекты:</b>"
        for e in effects:
            name=effect_names.get(e.get('effect_type'),e.get('effect_type'))
            minutes=e.get('remaining_seconds',0)//60
            seconds=e.get('remaining_seconds',0)%60
            text+=f"{name}:+{e.get('value')} (осталось {minutes}мин {seconds}сек)\n"
    await message.answer(text)
