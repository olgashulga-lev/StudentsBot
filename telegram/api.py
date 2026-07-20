import requests
import configparser
from pathlib import Path
from models import Player, Item

config = configparser.ConfigParser()
config.read('config.ini')
BACKEND_URL = f"http://{config['DEFAULT']['BACKHOST']}:{config['DEFAULT']['BACKPORT']}/api"

def _make_request(method, endpoint, data=None, params=None):
    url = f"{BACKEND_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            response = requests.delete(url, json=data, headers=headers, params=params)
        else:
            return None
        
        if response.status_code >= 400:
            print(f"Ошибка {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def get_player(chat_id, user_id):
    data = _make_request("GET", f"person/id/{chat_id}")
    if not data:
        return None
    
    for player_data in data:
        if player_data.get('userId') == user_id or player_data.get('user_id') == user_id:
            return Player(
                chat_id=chat_id,
                user_id=user_id,
                name=player_data.get('name', 'Unknown'),
                photo=player_data.get('photo', 'default.jpg'),
                exp=player_data.get('experience', 0),
                money=player_data.get('money', 50),
                hp=player_data.get('hp', 100),
                damage=player_data.get('damage', 20),
                luck=player_data.get('luck', 15) / 100,
                level=player_data.get('level', 1)
            )
    return None

def create_player(player):
    data = {
        'user_id' : player.user_id,
        'chat_id' : player.chat_id,
        'name' : player.name,
        'photo' : player.photo,
        'exp' : player.exp,
        'money' : player.money,
        'hp' : player.hp,
        'damage' : player.damage,
        'luck' : int(player.luck*100),
        'level' : player.name
    }
    return _make_request("POST", "person/create_alt", data)

def update_player(player):
    data = {
        'name' : player.name,
        'photo' : player.photo,
        'exp' : player.exp,
        'money' : player.money,
        'hp' : player.hp,
        'damage' : player.damage,
        'luck' : int(player.luck*100),
        'level' : player.name
    }
    params = {'chat_id' : player.chat_id, 'user_id' : player.user_id}
    return _make_request("PUT", "person/update", data, params)

def get_all_players():
    data= _make_request("GET", "person/all")
    if not data:
        return[]
    
    players=[]
    for p in data:
        players.append(Player(
            chat_id=p.get('chatId', 0),
            user_id=p['user_id'],
            name=p['name'],
            photo=p['photo'],
            exp=p['exp', 0],
            money=p['money',50],
            hp=p['hp',100],
            damage=p['damage',20],
            luck=p['luck',15]/100,
            level=p['level',1],
        ))
        return players
    
#Предметы
def get_items():
    data=_make_request("GET", "item/all")
    if not data:
        return []
    items=[]
    for i in data:
        items.append(Item(
            id=i['id'],
            name=i['name'],
            price=i['price'],
            decription=i['decription'],
            type=i['type']
        ))
    return items
def add_item_inventory(chat_id,user_id,item_id,item_name,item_type, quantity=1):
    data={
        'user_id': user_id,
        'chat_id': chat_id,
        'item_id': item_id,
        'item_name': item_name,
        'item_type': item_type,
        'quantity': quantity,
    }
    return _make_request("POST", "inventory/add", data=data)
def has_permament_item(chat_id,user_id,item_id):
    inventory=get_inventory(chat_id,user_id)
    for item in inventory:
        if item.get('item_id')==item_id:
            return True
        return False
def is_item_permament(item_id):
    permament_items=[3,4]
    return item_id in permament_items
def get_inventory(chat_id,user_id):
    data=_make_request("GET",f"inventory/{chat_id}/{user_id}")
    if not data:
        return[]
    
    items=[]
    for i in data:
        items.append({
            "id":i.get('id'),
            "item_id":i.get('item_id'),
            "name":i.get('name'),
            "type":i.get('type'),
            "quantity":i.get('quantity',1)
        })
        return(items)
def remove_item_from_inventory(chat_id,user_id,item_id):
    inventory=get_inventory(chat_id,user_id)
    item=next((i for i in inventory if i.get('item_id')==item_id), None)
    if not item:
        return False
    if item.get('quantity',0)>1:
        result=_make_request("PUT", "inventory/update", data={
            'inventory_id':item.get('id'),
            'quantity' :item.get('quantity')-1
        })
    else:
        result= _make_request ("DELETE", f"inventory/remove/{item.get('id')}")
    return result is not None
def get_active_effect(chat_id,user_id):
    data= _make_request("GET",f"effects/{chat_id}/{user_id}")
    if not data:
        return[]
    return data
def apply_effect(chat_id,user_id,effect_type,value,duration_seconds):
    params= {
        'chat_id':chat_id,
        'user_id':user_id,
        'effect_type':effect_type,
        'value':value,
        'duration_seconds':duration_seconds,
    }
    return _make_request("POST", "effects/apply",data=None, params=params)
def clear_expired_effect(chat_id,user_id):
    return _make_request("DELETE", f"effects/clear/{chat_id}/{user_id}")
