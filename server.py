import json
from fastapi import FastAPI, WebSocket, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from typing import List, Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine("sqlite:///chat2.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    last_seen = Column(DateTime, default=datetime.utcnow)
    online = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    username = Column(String)  # المرسل
    receiver = Column(String)  # المستلم
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

active_connections: Dict[str, WebSocket] = {}

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    return {"message": "User registered"}

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter_by(username=username).first()
    if user and user.password == password:
        user.online = True
        user.last_seen = datetime.utcnow()
        db.commit()
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/messages")
def get_messages():
    messages = db.query(Message).order_by(Message.timestamp.desc()).limit(20).all()
    return [{"username": m.username, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in reversed(messages)]

@app.get("/status/{username}")
def get_status(username: str):
    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "online": user.online,
        "last_seen": user.last_seen.isoformat()
    }
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket

    user = db.query(User).filter_by(username=username).first()
    if user:
        user.online = True
        user.last_seen = datetime.utcnow()
        db.commit()

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)  # نتوقع {"content": "...", "receiver": "اسم_المستلم"}
            content = data_json["content"]
            receiver = data_json["receiver"]

            # حفظ الرسالة في قاعدة البيانات
            msg = Message(username=username, receiver=receiver, content=content)
            db.add(msg)
            db.commit()

            # إرسال الرسالة للطرف الآخر فقط
            if receiver in active_connections:
                await active_connections[receiver].send_text(f"{username}: {content}")
    except:
        if username in active_connections:
            del active_connections[username]
        user = db.query(User).filter_by(username=username).first()
        if user:
            user.online = False
            user.last_seen = datetime.utcnow()
            db.commit()
):
    await websocket.accept()
    active_connections[username] = websocket
    user = db.query(User).filter_by(username=username).first()
    if user:
        user.online = True
        user.last_seen = datetime.utcnow()
        db.commit()

    try:
        while True:
            data = await websocket.receive_text()
            msg = Message(username=username, content=data)
            db.add(msg)
            db.commit()
            for user_conn in active_connections.values():
                await user_conn.send_text(f"{username}: {data}")
    except:
        if username in active_connections:
            del active_connections[username]
        user = db.query(User).filter_by(username=username).first()
        if user:
            user.online = False
            user.last_seen = datetime.utcnow()
            db.commit()
