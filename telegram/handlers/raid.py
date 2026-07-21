from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import api
from .common_utils import get_player_or_none
import random
import uuid
import os

router = Router()
active_raids = {}

BOSS_IMAGES = {
    1: "static/bosses/big_frog.jpg",
    2: "static/bosses/orc.jpg",
    3: "static/bosses/dragon.jpg"
}

def generate_raid_id():
    return str(uuid.uuid4())[:8]

async def perform_raid_battle(raid, boss, callback=None):
    total_damage=0
    boss_hp=raid.get("boss_current_hp",boss.hp)
    players_names=[]
    players_damage=[]
    players_data=[]

    for user_id in raid['players']:
         player=None
         for p in api.get_all_players():
              if p.user_id==user_id:
                   player==p
                   break
              if player:
                   api.clear_expired_effects(player.chat_id,user_id)
    for user_id in raid['players']:
         player=None
         player_chat_id=None
         all_players=api.get_all_players
         for p in api.get_all_players():
              if p.user_id==user_id:
                   player==p
                   player_chat_id=p.chat_id
                   break
         if player:
            players_names.append(player.name)
            players_data.append(player)
            effects=api.get_active_effect(player_chat_id,user_id) if player_chat_id else[]
            basic_damage=player.damage
            bonus_damage=0
            for e in effects:
                 if e.get('effect_type')== 'damage_bonus':
                      bonus_damage+=e.get('value',0)
            total_player_damage=basic_damage+bonus_damage
            damage=random.randit(5,20)+total_player_damage//5

            total_damage+=damage
            boss_hp-=damage
            players_damage.append(damage)
    return{
         'total_damage':total_damage,
         'boss_hp':boss_hp,
         'players_names':players_names,
         'players_damage':players_damage,
         'players_data':players_data
    }

@router.message(Command("raid"))
async def cmd_raid(message: types.Message):
     player=get_player_or_none(message)
     if not player:
          await message.answer("Нужно пройти регистрацию!")
          return
     if not active_raids:
          await message.answer(
               "Активных рейдов нет!\n\n"
               "Создайте свой рейд командой:\n"
               "/boss1 - Большая жаба"
               "/boss2 - Орк"
               "/boss3 - Дракон"
          )
          return
     text="<b>Активные рейды</b>\n\n"
     for raid_id,raid in active_raids.items():
          boss=next((b for b in api.get_bosses() if b.id == raid['boss_id']),None)
          if boss:
               creator=None
               all_players=api.get_all_players()
               for p in all_players:
                    if p.user_id==raid['creator_id']:
                         creator=p
                         break
                
               creator_name = creator.name if creator else f"Игрок {raid['creator_id']}"
               is_participant=message.from_user.id in raid['players']
               status="ВЫ УЧАСТВУЕТЕ" if is_participant else f"{len(raid['players'])}/5"
               text+= f"<b>{boss.name}</b>\n"
               text+= f"<b>{creator_name}</b>\n"
               text+= f"<b>{status}</b>\n"
               text += f"HP: {raid.get('boss_current_hp', boss.hp)}\n"

               if not is_participant and raid['status']=='recruiting':
                    text+=f"/join {creator_name}- присоединиться\n"
               elif is_participant:
                    text+=f"Вы уже в этом рейде!"
               else:
                    text+=f"Рейд уже начался!"
               await message.asnwer(text)
            

               
            

               

@router.message(Command("join"))
async def cmd_join_by_name(message: types.Message):
     player=get_player_or_none(message)
     if not player:
          await message.answer("Нужно пройти регистрацию!")
          return
     args=message.text.split()
     if len(args)<2:
          await message.answer("Укажите имя создателя рейда")
          return
     creator_name = ' '.join(args[1:]).strip()
     found_raid=None
     found_raid_id=None
     for raid_id,raid in active_raids.items():
          if raid['status'] != 'recruiting':
               continue
          creator=None
          all_players=api.get_all_players()
          for p in all_players:
               if p.user_id == raid['creator_id']:
                    creator=p
                    break
          if creator and creator.name.lower() == creator_name.lower():
            found_raid = raid
            found_raid_id = raid_id
            break
     if not found_raid:
          await message.answer("Рейд не найден")
          return
     for other_raid in active_raids.values():
          if message.from_user.id in other_raid['players']:
               await message.answer("Вы уже учавствуете в другом рейде!")
               return
          if len(found_raid['players']) >= found_raid.get('max_players', 5):
            await message.answer("Рейд полон! (максимум 5 игроков)")
            return
          found_raid['players'].append(message.from_user.id)
          creator=None
          all_players=api.get_all_players()
          for p in all_players:
               if p.user_id == raid['creator_id']:
                    creator=p
                    break
          if creator:
               try:
                    await message.bot.send_message(
                         chat_id=creator.chat_id,
                         text=f"{player.name} присоединился к рейду {len(found_raid['players'])}/5"
               
                    )
               except:
                    pass
          await message.answer(f"Вы присоединились к рейду {creator_name}")




async def start_raid(message: types.Message, boss_id: int):
    player=get_player_or_none(message)
    if not player:
          await message.answer("Нужно пройти регистрацию!")
          return
    all_bosses=api.get_bosses()
    boss=next((b for b in bosses if b.id == boss_id), None)
    if not boss:
         await message.answer("Нет такого босса!")
         return
    boss_image = BOSS_IMAGES.get(boss_id)
    if boss_image and os.path.exists(boss_image):
        try:
            photo = FSInputFile(boss_image)
            await message.answer_photo(
                photo=photo,
                caption=f"<b>{boss.name}</b>\nHP: {boss.hp}\nУрон: {boss.damage}"
            )
        except Exception as e:
            print(f"Ошибка при отправке фото босса: {e}")
    for raid in active_raids.values():
          if message.from_user.id in raid['players']:
               await message.answer("Вы уже учавствуете в другом рейде!")
               return
    raid_id=generate_raid_id()
    active_raids[raid_id]={
         'boss_id':boss_id,
         'players':[message.from_user.id],
         'status': 'recruiting',
         'boss_current_hp':boss.hp,
         'max_players':5,
         'created_at':message.date,
         'creator_name':player.name
    }

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать бой",
                    callback_data=f"start_raid_battle_{raid_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отменить рейд",
                    callback_data=f"cancel_raid_{raid_id}"
                )
            ]
        ]
    )

    await message.answer(
        f"<b>Рейд создан!</b>\n\n"
        f"Босс:{boss.name} \n"
        f"HP:{boss.hp} \n"
        f"Награда:{boss.money.reward}  монет\n"
        f"Опыт:{boss.exp.reward} \n\n"
        f"Создатель:{player.name} \n"
        f"Участников: 1/5\n\n"
        f"Друзья могут присоединиться из любого чата с ботом:\n"
        f"/join {player.name} \n\n"
        f"Когда наберётся 2+ игроков, нажмите «Начать бой»",
        reply_markup=keyboard
    )

@router.message(Command("boss1"))
async def cmd_boss1(message: types.Message):
    await start_raid(message, 1)

@router.message(Command("boss2"))
async def cmd_boss1(message: types.Message):
    await start_raid(message, 2)

@router.message(Command("boss3"))
async def cmd_boss1(message: types.Message):
    await start_raid(message, 3)



@router.message(Command("raid_status"))
async def cmd_raid_status(message: types.Message):
   raid_data=None
   raid_id=None
   for r_id,raid in active_raids.items():
        if message.from_user.id in raid['players']:
             raid_data=raid
             raid_id=r_id
             break
   if not raid_data: 
        await message.answer('Мы не нашли что игрок участвуент в каком-то рейде')
        return
   boss=next((b for b in api.get_bosses() if b.id == raid['boss_id']),None)
   if not boss:
        await message.answer("Ошибка!")
        return
   players_names=[]
   all_players=api.get_all_players()
   for user_id in raid_data['players']:
        for p in all_players:
             if p.user_id==user_id:
                  players_names.append(p.name)
                  break
   text=f"статус рейда\n\n"
   text+=f"босс:{boss.name}\n"
   text+=f"хп босса:{raid_data.get('boss_current_hp',boss.hp)}/{boss.hp}\n"
   text+=f"участников:{len(raid_data['players'])}/5\n"
   text+=f"статус рейда:{'набор'if raid_data["status"]=='recruting'else'битва'}\n\n"
   if players_names:
        text+="участники\n"
        for i,name in enumerate(players_names,1):
             text+=f"{i}.{name}\n"
             await message.answer(text)
             
        




   


@router.message(Command("leave_raid"))
async def cmd_leave_raid(message: types.Message):
    

@router.callback_query(F.data.startswith("start_raid_battle_"))
async def cmd_raid_battle(callback: types.CallbackQuery):
    
        achievement_config = {
            1: {"name": "", "desc": ""},
            2: {"name": "", "desc": ""},
            3: {"name": "", "desc": ""}
        }

        

@router.callback_query(F.data.startswith("cancel_raid_"))
async def cmd_cancel_raid(callback: types.CallbackQuery):
   
async def check_and_give_boss_achievements(boss_id, user_id, chat_id, bot):
    achievement_config = {
        1: {
            'name': "",
            'description': ""
        },
        2: {
            'name': "",
            'description': ""
        },
        3: {
            'name': "",
            'description': ""
        }
    }
    
    
    await callback.message.edit_text("Рейд отменён")
