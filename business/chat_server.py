# chat_server.py
import socketio
from fastapi import FastAPI
from utils.db import save_message

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@sio.event
async def connect(sid, environ):
    print(f"User connected: {sid}")

@sio.event
async def join(sid, data):
    chat_id = str(data['chat_id'])
    await sio.enter_room(sid, chat_id)
    print(f"User joined room: {chat_id}")

@sio.event
async def send_message(sid, data):
    chat_id = data['chat_id']
    sender_id = data['sender_id']
    content = data['content']
    
    await save_message(chat_id, sender_id, content)
    
    await sio.emit('new_message', data, room=str(chat_id))

@sio.event
async def disconnect(sid):
    print(f"User disconnected: {sid}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=5001)
