
from werkzeug.security import generate_password_hash, check_password_hash
import re
from typing import Optional
from passlib.hash import bcrypt
import aiomysql
import asyncio
import logging
import json
import random

with open('data/config.json', 'r')  as f:
    config = json.load(f)

dbpassword = config['password']
user = config['user']
db = config['db']
host = config['host']
port = config['port']

logging.basicConfig(level=logging.INFO)
loop = asyncio.get_event_loop()


async def init_db():
    try:
        conn = await aiomysql.connect(
            user = user,
            password=dbpassword,
            db = db,
            host = host,
            port = port
            )
    except Exception as e:
        print(f'Exception: {e}')

    finally:
        return True
    

async def get_user_by_login(login: str) -> Optional[dict]:
    async with aiomysql.connect(
            user = user,
            password=dbpassword,
            db = db,
            host = host,
            port = port
            ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM users 
                WHERE user_phone = %s OR user_email = %s
                LIMIT 1
            """, (login, login))
            return await cur.fetchone()
        

async def insert_into_users(username, usersurname, userdaddy, phone, email, password):
    # Очищаем номер телефона
    cleaned_phone = re.sub(r'\D', '', phone)
    
    try:
        conn = await aiomysql.connect(
            user=user,        
            password=dbpassword, 
            db=db,            
            host=host,
            port=port
        )
        async with conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (
                    user_name, 
                    user_surname, 
                    user_daddy,  
                    user_phone, 
                    user_email, 
                    user_password
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    username,
                    usersurname,
                    userdaddy,
                    cleaned_phone,  # Используем очищенный номер
                    email,
                    password,  # Используем хеш пароля
                ))
            await conn.commit()
        return "INSERTED"
        
    except Exception as e:
        logging.error(f'Exception while insert into users: {e}')
        raise  # Перебрасываем исключение для отладки
        
    finally:
        if 'conn' in locals():
            conn.close()  # Всегда закрывайте соединение!

async def get_user_by_id(user_id: int) -> Optional[dict]:
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
            ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM users 
                WHERE id = %s
                LIMIT 1
            """, (user_id,))
            return await cur.fetchone()
        

async def update_user_profile(user_id: int, update_data: dict) -> bool:
    """Обновляет профиль пользователя. Возвращает True, даже если данные идентичны."""
    try:
        async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
        ) as conn:
            async with conn.cursor() as cur:
                set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
                values = list(update_data.values())
                values.append(user_id)
                
                query = f"UPDATE users SET {set_clause} WHERE id = %s"
                await cur.execute(query, values)
                await conn.commit()
                return True  # Успех, даже если rowcount = 0
    except Exception as e:
        logging.error(f"Ошибка обновления профиля: {e}")
        return False

async def update_user_avatar(user_id: int, avatar_data: bytes) -> bool:
    """Обновляет аватар пользователя (возвращает True, даже если данные идентичны)"""
    try:
        async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET user_avatar = %s WHERE id = %s",
                    (avatar_data, user_id)
                )
                await conn.commit()
                return True  # Всегда True, если не было исключения
    except Exception as e:
        logging.error(f"Ошибка обновления аватара: {e}")
        return False

async def delete_user_avatar(user_id: int):
    """Удаляет аватар пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET user_avatar = NULL WHERE id = %s",
                (user_id,)
            )
            await conn.commit()
            return cur.rowcount > 0