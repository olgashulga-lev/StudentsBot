from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

# Настройки
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bot.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="МеханоБот API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Person(Base):
    __tablename__ = 'person'
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    photo = Column(String(255), default="default.jpg")
    experience = Column(Integer, default=0)
    money = Column(Integer, default=50)
    hp = Column(Integer, default=100)
    damage = Column(Integer, default=20)
    luck = Column(Integer, default=15)
    level = Column(Integer, default=1)


class Achievement(Base):
    __tablename__ = "achievement"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    image = Column(String(255), default="default_achievement.jpg")
    condition = Column(String(255), nullable=True)


class Inventory(Base):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    item_id = Column(Integer, nullable=False)
    item_name = Column(String(100), nullable=False)
    item_type = Column(String(50), nullable=False)
    quantity = Column(Integer, default=1)
    purchased_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'chat_id', 'item_id', name='uq_user_item'),
    )
   
class ActiveEffectDB(Base):
    __tablename__ = "active_effects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    effect_type = Column(String(50), nullable=False)
    value = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer, nullable=False)

# Создание таблиц
Base.metadata.create_all(bind=engine)

class PersonCreate(BaseModel):
    user_id: int
    chat_id: int
    name: str
    photo: str = 'default.jpg'
    level: int = 1

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    photo: Optional[str] = None
    experiense: Optional[int] = None
    money: Optional[int] = None
    hp: Optional[int] = None
    damage: Optional[int] = None
    luck: Optional[int] = None
    level: Optional[int] = None

class PersonResponse(BaseModel):
    userId: int
    chatId: int
    name: str
    photo: str
    experiense: int
    money: int
    hp: int
    damage: int
    luck: int
    level: int=1
    class Config:
        from_attributes = True

class AchievementCreate(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    image: str = "default_achievement.jpg"
    condition: Optional[str] = None
    

class AchievementResponse(BaseModel):
    id: int
    name: str
    photo: str
    condition: Optional[str] = None
    description: str
    
    class Config:
        from_attributes = True

class ItemResponse(BaseModel):
    name: str
    id: int
    price: int
    description: str
    type: str
    
    class Config:
        from_attributes = True

class InventoryAddRequest(BaseModel):
    user_id: int
    chat_id: int
    item_id: int
    item_name: str
    item_type: str
    quantity: int = 1

    
class InventoryItemResponse(BaseModel):
    id: int
    item_id: int
    name: str
    type: str
    quantity: int
    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_person(db: Session, chat_id: int, user_id: int):
    return db.query(Person).filter(
        Person.chat_id == chat_id,
        Person.user_id == user_id
    ).first()

@app.get("/api/person/id{chat_id}", response_model=List[PersonResponse])

def get_players_by_chat(chat_id:int, db:Session=Depends(get_db)):
    players=db.query(Person).flter(Person.chat_id == chat_id).all()
    return [
        PersonResponse(
            userId=p.user_id,
            chatId= p.chat_id,
            name= p.name,
            photo= p.photo,
            experiense= p.experiense,
            money= p.money,
            hp= p.hp,
            damage= p.damage,
            luck= p.luck,
            level= p.level
        )
        for p in players
    ]

@app.post("/api/person/create_alt", status_code=201)

def create_player_alt(data: dict, db: Session = Depends(get_db)):
    try:
        user_id = data.get("user_id")
        chat_id= data.get("chat_id")
        name= data.get("name")
        photo= data.get("photo", 'defaultl.jpg')
        level= data.get("level", 1)
        if not all([user_id, chat_id, name]):
            raise HTTPException(status_code=400, detail="Missing reqired fields")
        
        existing = get_person(db, chat_id, user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Игрок уже существует")
        
        db_player = Person(
            chat_id = chat_id,
            user_id = user_id,
            name = name,
            photo = photo,
            exp = 0,
            money = 50,
            hp = 100,
            damage = 20,
            luck = 15,
            level = 1
        )

        db.add(db_player)
        db.commit()
        db.refresh(db_player)



        return{"message": "Игрок создан"}


    except Exception as err:
        raise HTTPException(status_code=400,detail=str(err))
    
@app.put("/api/person/update")
def update_player(
    chat_id: int,
    user_id:int,
    data: PersonUpdate,
    db: Session = Depends(get_db)
):
        
    player = get_person(db, chat_id, user_id)

    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(player, key, value)
        db.commit()
        return {"message": "Игрок обновлен"}
    
@app.get("/api/person/all", response_model=List[PersonResponse])
def get_get_all_players(db: Session = Depends(get_db)):
    players = db.query(Person).all()
    return [
        PersonResponse(
        userId=p.user_id,
        chatId= p.chat_id,
        name= p.name,
        photo= p.photo,
        experiense= p.experiense,
        money= p.money,
        hp= p.hp,
        damage= p.damage,
        luck= p.luck,
        level= p.level
        )
        for p in players
    ]

@app.put("/api/person/update_level") #обновление уровня игрока
def update_player_level(
    chat_id: int,
    user_id:int,
    level: int,
    #id чата и польз., уровень(пишем тип)
    db: Session = Depends(get_db)
):
    player = get_person(chat_id, user_id, user_id, db)  # Вызываем вспомогательную функцию для поиска игрока
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    
    player.level = level
    db.commit()
    return {"message": "Уровень", "level": level}

# Items (для магазина)
@app.get("/api/item/all", response_model=List[ItemResponse])
def get_items(db: Session = Depends(get_db)):
    return [
        ItemResponse(id=1, name="Зелье здоровья", price=50, description="Восстанавливает 20 HP", type="shop"),
        ItemResponse(id=2, name="Зелье урона", price=50, description="+10 урона на бой", type="shop"),
        ItemResponse(id=3, name="меч", price=100, description="+15 урона", type="shop"),
        ItemResponse(id=4, name="броня", price=150, description="+20 к максимальному здоровью", type="shop")
    ]

@app.get("/api/inventory/{chat_id}/{user_id}", response_model=List[InventoryItemResponse])
def get_inventory(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    items = db.query(Inventory).filter(
        Inventory.chat_id == chat_id,
        Inventory.user_id == user_id
    ).all()
    
    return [
        InventoryItemResponse(
            id=inv.id,
            item_id=inv.item_id,
            name=inv.item_name,
            type=inv.item_type,
            quantity=inv.quantity
        )
        for inv in items
    ]

@app.post("/api/inventory/add")
def add_to_inventory(request: InventoryAddRequest, db: Session = Depends(get_db)):
    existing = db.query(Inventory).filter(
        Inventory.user_id == request.user_id,
        Inventory.chat_id == request.chat_id,
        Inventory.item_id == request.item_id
    ).first()
    
    if existing:
        existing.quantity += request.quantity
    else:
        new_item = Inventory(
            user_id=request.user_id,
            chat_id=request.chat_id,
            item_id=request.item_id,
            item_name=request.item_name,
            item_type=request.item_type,
            quantity=request.quantity
        )
        db.add(new_item)
    db.commit()
    return {"message": "Предмет добавлен в инвентарь."}

# Achievement
@app.get("/api/achievement/person/{chat_id}/{user_id}", response_model=List[AchievementResponse])
def get_user_achievements(chat_id: int, user_id: int, db: Session = Depends(get_db)):
    achievements = db.query(Achievement).filter(
        Achievement.chat_id == chat_id,
        Achievement.user_id == user_id
    ).all()
    return [
        AchievementResponse(
            id=a.id,
            name=a.name,
            photo=a.image,
            condition=a.condition,
            description=a.description
        )
        for a in achievements
    ]

@app.post("/api/achievement/create", status_code=201)
def create_achievement(achievement: AchievementCreate, db: Session = Depends(get_db)):
    db_achievement = Achievement(
        user_id=achievement.user_id,
        chat_id=achievement.chat_id,
        name=achievement.name,
        description=achievement.description,
        image=achievement.image,
        condition=achievement.condition
    )
    db.add(db_achievement)
    db.commit()
    return {"message": "Достижение выдано"}


@app.post("/api/effects/apply") #применение эффекта
def apply_effect(
    # ID чата, польз., тип эффекта, величина эффекта, длительность в секундах(тип обозначаем)
    user_id: int
    chat_id: int
    effect_type: str
    value: int
    duration_seconds: int
    db: Session = Depends(get_db)
):
    effect = ActiveEffectDB(
        user_id = user_id,
        chat_id = chat_id,
        effect = effect,
        effect_type = effect_type,
        value = value,
        duration = duration,
        db= db

    )
    db.add(effect)
    db.commit()
    return {"message": "примениен эффект"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=800)
