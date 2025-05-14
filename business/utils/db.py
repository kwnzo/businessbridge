
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

async def create_publication(user_id: int, title: str, content: str, image_data: bytes = None) -> int:
    """Создает новую публикацию и возвращает её ID"""
    try:
        async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO publics (
                        public_creator,
                        topic_name,
                        topic_text,
                        preview_image
                    ) VALUES (%s, %s, %s, %s)
                """, (user_id, title, content, image_data))
                await conn.commit()
                return cur.lastrowid
    except Exception as e:
        logging.error(f'Ошибка при создании публикации: {e}')
        raise

async def get_user_articles(user_id: int) -> list:
    """Получает все статьи пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT id, topic_name, topic_name_en, topic_text, preview_image, created_at 
                FROM publics 
                WHERE public_creator = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return await cur.fetchall()

async def get_article_by_id(article_id: int) -> Optional[dict]:
    """Получает статью по ID"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT * FROM publics 
                WHERE id = %s
                LIMIT 1
            """, (article_id,))
            return await cur.fetchone()
        

async def record_view(public_id: int, user_id: int):
    async with aiomysql.create_pool(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        "INSERT INTO views (public_id, user_id) "
                        "VALUES (%s, %s) "
                        "ON DUPLICATE KEY UPDATE created_at = NOW()",
                        (public_id, user_id)
                    )
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    raise e
                
async def get_views(public_id: int):
    async with aiomysql.create_pool(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        'SELECT views FROM publication_stats WHERE public_id = %s',
                        (public_id,)
                    )
                    data = await cursor.fetchone()
                    # Extract the first value from the tuple (e.g., 24)
                    conn.close()
                    return data[0] if data else 0  # Return 0 if no rows found
                except Exception as e:
                    logging.error(f"Database error: {e}")
                    return 0  # Fallback value
                finally:
                    if 'conn' in locals():
                        conn.close()

async def get_publics():
    async with aiomysql.create_pool(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute('SELECT topic_name FROM publics')
                    data = await cursor.fetchall()
                    print(data)
                    return data
                except Exception as e:
                    logging.error(f'Index error: {e}')
                finally:
                    if 'conn' in locals():
                        try:
                            conn.close()
                            logging.info('conn closed after index')
                        except Exception as e2:
                            logging.error(f'Error at closing conn: {e}')