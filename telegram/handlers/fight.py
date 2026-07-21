# fight
import random
import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import api
from .common_utils import get_player_or_none

router = Router()
active_duels = {} #Словарь для хранения активных дуэлей. Ключ — chat_id, значение — список дуэлей в этом чате

async def perform_duel(player1, player2, challenger_id, target_id, callback):
    api.clear_expired_effects(callback.message.chat.id, player1.user_id) #Очистка эффектов у игрока 1
    api.clear_expired_effects(callback.message.chat.id, player2.user_id) #очистка у 2 игрока
    
    effects1 = api.get_active_effects(callback.message.chat.id, player1.user_id)#Получение активных эффектов игрока 1
    effects2 = api.get_active_effects(callback.message.chat.id, player2.user_id)# у второго
    
    player1_damage = player1.damage
    player1_luck = player1.luck
    player1_hp = player1.hp
    player1_money = player1.money
    # для хранения урона, удачи и здоровья игроков 1 и 2
    
    
    for e in effects1:
        if e.get('effect_type') == 'damage_bonus':
            player1_damage += e.get('value', 0)
        elif e.get('effect_type') == 'luck_bonus':
            player1_luck += e.get('value', 0) / 100
        elif e.get('effect_type') == 'hp_bonus':
            player1_hp += e.get('value', 0)
    
    # сделать цикл для эффектов 2 игрока
    player2_damage = player2.damage
    player2_luck = player2.luck
    player2_hp = player2.hp
    player2_money = player2.money
    # для хранения урона, удачи и здоровья игроков 1 и 2
    
    
    for e in effects2:
        if e.get('effect_type') == 'damage_bonus':
            player2_damage += e.get('value', 0)
        elif e.get('effect_type') == 'luck_bonus':
            player2_luck += e.get('value', 0) / 100
        elif e.get('effect_type') == 'hp_bonus':
            player2_hp += e.get('value', 0)
    
    initial_hp1 = player1_hp #начальное здоровье игрока 1
    #написать для 2 игрока
    initial_hp2 = player2_hp
    
    text = f"<b>ДУЭЛЬ НАЧАЛАСЬ!</b>\n\n"
    text += f"{player1.name} {player1_hp} HP | {player1_damage} урона\n"
    text += f"{player2.name} {player2_hp} HP | {player2_damage} урона\n\n"
    text += f"<b>Бой идёт до 3 раундов или до смерти!</b>\n"
    text += "═" * 30 + "\n\n"
    
    round_num = 1
    
    while player1_hp > 0 and player2_hp > 0: # пока раунд не макс. и здоровье обоих игроков больше 0
        text += f"<b>РАУНД {round_num}</b>\n"
        creet1 = random.randint(1, 100)
        if creet1 <= player1_luck:
           base_damage1 = int(base_damage1 * 1.3)
           text += f"{player1.name} повезло! Критический удар!\n"            
        creet2 = random.randint(1, 100)
        if creet2 <= player1_luck:
           base_damage2 = int(base_damage2 * 1.3)
           text += f"{player2.name} повезло! Критический удар!\n"            
        

        player2_hp -= base_damage1
        if player2_hp <= 0:
            player2_hp = 0
            text += f"{player1.name} нанёс {base_damage1} урона → {player2_hp} HP\n"
            text += f"{player2.name} повержен!\n"
            break
        else:    
            text += f"{player1.name} нанёс {base_damage1} урона → {player2_hp} HP\n"
        player1_hp -= base_damage2
        if player1_hp <= 0:
            player1_hp = 0
            text += f"{player2.name} нанёс {base_damage2} урона → {player1_hp} HP\n"
            text += f"{player1.name} повержен!\n"
            break
        else:    
            text += f"{player2.name} нанёс {base_damage2} урона → {player1_hp} HP\n"

            text += "═" * 30 + "\n\n"
    
    exp_for_winner = random.randint(15, 20)#опыт для победителя
    exp_for_loser = random.randint(5, 10)#опыт для проигравшего
    
    if player2_hp <= 0:
        win_money = player2_money * 0.15
        player1_money += win_money
        player2_money -= win_money
        winner = player1
        loser = player2

        player2_hp = 100

        leveledW = player1.add_exp(exp_for_winner)#добавляет опыт и проверяет повышение уровня
        leveledL = player2.add_exp(exp_for_loser)

    
    else:

        win_money = player1_money * 0.15
        player2_money += win_money
        player1_money -= win_money
        winner = player2
        loser = player1

        player1_hp = 100
        #написать про здоровье 2

        leveledL = player1.add_exp(exp_for_loser)#добавляет опыт и проверяет повышение уровня
        leveledW = player2.add_exp(exp_for_winner)
        
    api.update_player(player1)
    api.update_player(player2)

        
    text += f"<b>{winner.name} ПОБЕДИЛ!</b>\n"
    text += f"+{win_money} монет!\n"
    text += f"+{exp_for_winner} опыта"
    if leveledW:
        text += f"{winner.name} ПОВЫСИЛ УРОВЕНЬ ДО {winner.level}!"
    text += f"\nОсталось HP: {winner.hp}\n"
    
    text += f"\n{loser.name} проиграл\n"
    text += f"+{exp_for_loser} опыта (за участие)"
    if leveledL:
        text += f"{loser.name} ПОВЫСИЛ УРОВЕНЬ ДО {loser.level}!"
    
    if player2_hp <= 0:
        text += f"\n{loser.name} мёртв!"
        
    return text




@router.message(Command("fight"))
async def cmd_duel(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("игрока нат в бд")
        return
    
    all_players = api.get_all_players()
    available_players = []
    for x in available_players:
        if x.user_id == message.from_user.id:#ID пользователя, который написал команду /fight
            continue
        
        in_duel = False
        if in_duel == True:
            for duel in active_duels [message.chat.id]:
                if x.user_id == duel['player1'] or x.user_id == duel['player2']:
                    in_duel = True
                    break
        
        if not in_duel:
            available_players.append(x)
    
    if not available_players:
        await message.answer("нет доступных игроков")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])#Это клавиатура, которая появляется под сообщением в виде кнопок. При нажатии на кнопку отправляется callback-запрос.
    
    for p in available_players[0, 5]:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{p} (Ур. {p.level} | {p.hp} HP)",
                callback_data=f"duel_select_{p.user_id}"
            )
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="Отмена",
            callback_data="duel_cancel"
        )
    ])
    
    await message.answer(
        "<b>Выберите противника для дуэли:</b>\n\n"
        f"Ваш баланс: {player.money} монет\n"
        f"Ваше HP: {player.hp}\n"
        f"Ваш урон: {player.damage}\n\n"
        f"Бой будет длиться до смерти!",
        reply_markup= keyboard
    )


@router.callback_query(F.data.startswith("duel_select_"))
async def cmd_duel_select(callback: types.CallbackQuery):
    data = callback.data.split('_')
    
    if len(data) < 3:
        await callback.answer("error")
        return
    
    try:
        target_id = int(data[2])
    except ValueError:
        await callback.answer("error")
        return
    
    player = api.get_player(callback.message.chat.id, callback.from_user.id)#Получи данные игрока из базы по chat_id и user_id, которые взяты из callback-запроса".
    if not player:
        await callback.answer("no player")
        return
    
    if player.hp <= 0:
        await callback.answer("dead")
        return
    
    all_players = api.get_all_players()#Получи список всех зарегистрированных игроков из базы данных
    target = next((p for p in all_players if p.user_id == target_id), None)#Пройти по всем игрокам, найти первого, у кого user_id равен target_id. Если такого игрока нет — вернуть None
    
    if not target:
        await callback.answer("error")
        return
    
    if player.hp:
        await callback.answer("alive")
        return
    
    if callback.from_user.id == target_id:
        await callback.answer("error")
        return
    
    if callback.message.chat.id in active_duels:
        for duel in active_duels[callback.message.chat.id]:
            if duel['player1'] == target_id or duel['player2'] == target_id:
                await callback.answer("игрок уже учавствует в дуэли")
                return
    
    if callback.message.chat.id not in active_duels:
        active_duels[callback.message.chat.id] = []
    
    active_duels[callback.message.chat.id].append({
        'player1': callback.from_user.id,
        'player2': target_id,
        'status': 'waiting',#ожидание
        'challenger_chat_id': callback.message.chat.id,
        'target_chat_id':target.chat_id
    })
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Принять",
                    callback_data=f"accept_duel_{callback.from_user.id}_{target_id}"#данные при нажатие на кнопку
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отклонить",
                    callback_data=f"refuse_duel_{callback.from_user.id}_{target_id}"
                )
            ]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>Вы вызвали {target.name} на дуэль!</b>\n\n"
        f"Ожидайте ответа...\n"
    )
    
    try:
        await callback.bot.send_message(
            chat_id=target.chat_id,
            text=(
                f"<b>ВЫЗОВ НА ДУЭЛЬ!</b>\n\n"
                f"<b>{player.name}</b> вызывает вас на дуэль!\n\n"
                f"<b>Статистика вызывающего:</b>\n"
                f"   HP: {player.hp}\n"
                f"   Урон: {player.damage}\n"
                f"   Удача: {int(player.luck * 100)}%\n\n"
                f"<b>Ваша статистика:</b>\n"
                f"   HP: {target.hp}\n"
                f"   Урон: {target.damage}\n"
                f"   Удача: {int(target.luck * 100)}%\n\n"
            ),
            reply_markup=keyboard#кнопки принять отказаться
        )
    except Exception as e:
        print(f"Ошибка отправки сообщения противнику: {e}")
        await callback.message.edit_text(
            f"Не удалось отправить вызов {target.name}!\n"
            f"Убедитесь, что бот может писать ему в личные сообщения."
        )
        return
    
    await callback.answer(f"Вызов отправлен {target.name}!")


@router.callback_query(F.data.startswith("refuse_duel_"))
async def cmd_duel_refuse(callback: types.CallbackQuery):#команда отказа от дуэли
    data = callback.data.split('_')
    if len(data) < 4:
        await callback.answer("error")
        return
    
    try:
        challenger_id = int(data[2])
        target_id = int(data[3])
    except ValueError:
        await callback.answer("error")
        return
    
    if callback.from_user.id != target_id:
        await callback.answer("error")
        return
    
    if callback.message.chat.id in active_duels:#Если в этом чате есть активные дуэли
        for duel in active_duels[callback.message.chat.id][:]:#Копия списка дуэлей в чате
            if duel['player1'] == challenger_id and duel['player2'] == target_id:
                active_duels[callback.message.chat.id].remove(duel)#Удаляем эту дуэль из списка активных
                break
    
    await callback.message.edit_text(
        f"{callback.from_user.first_name} отказался от дуэли"
    )
    await callback.answer("вы отказались от дуэли")


@router.callback_query(F.data == "duel_cancel")
async def cmd_duel_cancel(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("отменено")

@router.callback_query(F.data.startswith("accept_duel_"))
async def cmd_duel_accept(callback: types.CallbackQuery):#команда принятия дуэли
    data = callback.data.split('_')
    
    if len(data) < 4:
        await callback.answer("error")
        return
    
    try:
        challenger_id = int(data[2])
        target_id = int(data[3])
    except ValueError:
        await callback.answer("error")
        return
    
    if callback.from_user.id != target_id:
        await callback.answer("это не ваш вызов")
        return
    
    duel = None
    duel_key = None
    for key, duels in active_duels.items():
        for d in duels:
            if d['player1'] == challenger_id and d['player2'] == target_id and d['status'] == 'waiting':
                duel = d
                duel_key = key
                break
        if duel:
            break
    
    if not duel:
        await callback.answer("дуэль завершена")
        return
    
    player1 = api.get_player(duel['challenger_chat_id'], challenger_id)#Получи данные вызывающего игрока по его chat_id и user_id
    if not player1:
        all_players = api.get_all_players()#Получаем всех игроков из базы
        player1 = next((p for p in all_players if p.user_id == challenger_id), None)#Если не удалось получить игрока по chat_id, попробуй найти его по user_id среди всех игроков
    
    player2 = api.get_player(duel['callback.message.chat.id'], target_id)
    if not player2:
        all_players = api.get_all_players()
        player2 = next((p for p in all_players if p.user_id == target_id), None)

    if not player1 or not player2:
        await callback.answer("игроки не найдены")
        return
    
    if player1.hp <= 0:
        await callback.answer("этот игрок мертв")
        active_duels[duel_key].remove(duel)
        await callback.message.edit_text("дуэль отменена, вызывающийся Игорёк мертв")
        return
    
    if player2.hp <= 0:
        await callback.answer("ты мертв")
        return
    
    duel['status'] = 'fighting'
    
    await callback.message.edit_text(
        f"<b>ДУЭЛЬ НАЧИНАЕТСЯ!</b>\n\n"
        f"{player1.name} {player1.hp} HP\n"
        f"{player2.name} {player2.hp} HP\n\n"
        f"Идёт расчёт боя..."
    )
    
    try:
        await callback.bot.send_message(
            chat_id=duel['challenger_chat_id'],#Отправь сообщение в чат вызывающего игрока
            text=(
                f"<b>{player2.name} ПРИНЯЛ ДУЭЛЬ!</b>\n\n"
                f"Бой начинается!"
            )
        )
    except Exception as e:
        print(f"Ошибка уведомления вызывающего: {e}")
    
    await asyncio.sleep(3)#Функция — приостанавливает выполнение на 2 секунды
    text = await perform_duel(player1, player2, challenger_id, target_id, callback)#Выполни функцию perform_duel(), которая рассчитывает все раунды боя, и сохрани результат в переменную text
    active_duels[duel_key].remove(duel)
    
    try:
        await callback.bot.send_message(
            chat_id=duel['challenger_chat_id'],
            text=text
        )
    except Exception as e:
        print(f"Ошибка отправки результата вызывающему: {e}")
    
    await callback.message.edit_text(text)
    await callback.answer("все закончилось")


@router.message(Command("fight_cancel"))
async def cmd_duel_cancel_all(message: types.Message):#команда отмены всех дуэлей
    if message.chat.id not in active_duels:
        await message.answer('нет активных дуэлей')
        return
    
    removed = False
    for duel in active_duels[message.chat.id][:]:
        if duel['player1'] == message.from_user.id or duel['player2'] == message.from_user.id:
            active_duels[message.chat.id].remove(duel)
            removed = True
    
    if removed:
        await message.answer('дуэль отменена')
    else:
        await message.answer('нет дуэли')
