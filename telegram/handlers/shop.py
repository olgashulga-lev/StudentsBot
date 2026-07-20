from aiogram import Router, types, F
from aiogram.filters import Command

import api
from .common_utils import get_player_or_none
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    player=get_player_or_none(message)
    if not player:
        await message.answer("Сначала нужно пройти регистрацию")
        return
    items=api.get_items()
    shop_items = [i for i in items if i.type == 'shop' or i.type == "permament"]
    if not shop_items:
        await message.answer('Магазин пуст')
        return
    text=f"<b>Магазин</b>\n Ваш баланс: {player.money}\n\n"

    inventory=api.get_inventory(message.chat.id, message.from_user.id)
    owned_permament_ids = [item.get('item_id') for item in inventory if item.get ('type') == 'permament']

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for item in shop_items:
        text += f"<b>{item.name}</b>\n"
        text += f"   {item.description}\n"
        text += f"   {item.price} монет\n\n"
        if item.type =='permament':
            if item.id in owned_permament_ids:
                text += "✅ Уже куплено\n"
            else:
                text+="⚠ Можно упить только один раз\n"
        text+="\n"
        if item.type == 'permament' and item.id in owned_permament_ids:
            pass
        else:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"Купить {item.name} ({item.price})",
                    callback_data=f"buy_{item.id}"
                )
            ])
    await message.answer(text, reply_markup=keyboard)
@router.callback_query(F.data.startwitch("buy_"))
async def cmd_shop_buy(callback: types.CallbackQuery):
    data= callback.data.split('_')
    if len(data)< 2:
        await callback.answer("Ошибка!")
        return
    try:
        item_id=int(data[1])
    except ValueError:
        await callback.answer("Ошибка!")
        return
    player=api.get_player(callback.message.chat.id,callback.from_user.id)
    if not player:
        await callback.answer("Ошибка!")
        return
    items=api.get_items()
    item=next((i for i in items if i.id == item_id), None)
    if not item:
         await callback.answer("Ошибка!")
         return
    if player.money<item.price:
        await callback.answer("Недостаточно средств")
        return
    if item.type == 'permament':
        inventory = api.get_inventory(callback.message.chat.id, callback.from_user.id)
        for inv_item in inventory:
            if inv_item.get('item_id')== item.id and inv_item.get('type') == 'permament':
                await callback.answer(f"Вы уже купили {item.name}!")
                return
    player.money-=item.price
    api.update_player(player)
    api.add_item_inventory(
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
        item_id=callback.item.id,
        item_name=callback.item.name,
        item_type=callback.item.type
    )
    if item.type == 'premament':
        if item.id ==3:
            player.damage+=15
            api.update_player(player)
            await callback.answer(f"Вы купили {item.name}! +15 к урону")
        elif item.id==4:
            player.hp=min(100,player.hp +20)
            api.update_player(player)
            await callback.answer(f"Вы купили {item.name}! +20 к HP")
    else:
        await callback.answer(f"{item.name} приобретен")
    text=f"<b>Магазин</b>\n Ваш баланс:{player.money}\n\n Куплено: {item.name}"
    await callback.message.edit_text(text)
