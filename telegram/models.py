from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base()

class Player:
    def __init__(self, chat_id, user_id, name, photo, exp=0, money=50, hp=100, damage=20, luck=15, level=1):
        self.chat_id = chat_id
        self.user_id = user_id
        self.name = name
        self.photo = photo
        self.exp = exp
        self.money = money
        self.hp = hp
        self.damage = damage
        self.luck = luck
        self.level = level

    def __str__(self):
        return f"{self.name} (Ур. {self.level})"
    
    def get_exp_for_next_level(self):
        exp_for_next_level = 100 - self.exp
        return exp_for_next_level

    
    def get_max_level(self):
        return 20
    
    def add_exp(self, amount):
        self.exp += amount
        
        leveled_up = False
        while self.level < self.get_max_level(): 
            needed = self.get_exp_for_next_level()
            if self.exp >= needed:
                self.exp -= needed
                self.level += 1
                self.apply_level_bonus()
                leveled_up = True
            else:
                break
        
        if self.level >= self.get_max_level():
            self.exp = 0
        
        return leveled_up
    
    def apply_level_bonus(self):
        self.hp += 20
        self.damage += 5
        self.luck += 1
        

class Achievement:
    def __init__(self, id, photo, name, condition, description):
        self.id = id
        self.photo = photo
        self.name = name
        self. condition = condition
        self.description = description
    


class Event:
    def __init__ (self, datetime, user_id, chat_id,  id, name):
        self.datetime = datetime
        self.user_id = user_id
        self.chat.id = chat_id
        self.id = id
        self.name = name

class Boss:
    def __init__(self, money_reward, damage, luck, photo, id, hp, name, exp_reward):
        self.money_reward = money_reward
        self.damage = damage
        self.luck = luck
        self.photo = photo
        self.id = id
        self.hp = hp
        self.name = name
        self.exp_reward = exp_reward
        

class Item:
    def __init__(self, name, id, price, description, type):
        self.name = name
        self.id = id
        self.price = price
        self.description = description
        self.type = type
