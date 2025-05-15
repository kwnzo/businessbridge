
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
            async with conn.cursor(aiomysql.DictCursor) as cursor:  # Используем DictCursor
                try:
                    await cursor.execute('''
                        SELECT 
                            id, 
                            topic_name, 
                            topic_name_en, 
                            preview_image 
                        FROM publics
                    ''')
                    return await cursor.fetchall()
                except Exception as e:
                    logging.error(f'Error getting articles: {e}')
                    return []
                
async def get_image_data(article_id):
    async with aiomysql.create_pool(
        user=user,
        password=dbpassword,
        db=db,
        host=host,
        port=port
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    'SELECT preview_image, image_type FROM publics WHERE id = %s',
                    (article_id,))
                result = await cursor.fetchone()
                return await cursor.fetchall()

async def get_users_count() -> int:
    """Возвращает общее количество пользователей"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM users")
            result = await cur.fetchone()
            return result[0] if result else 0

async def get_articles_count() -> int:
    """Возвращает общее количество статей"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM publics")
            result = await cur.fetchone()
            return result[0] if result else 0

async def get_experts_count() -> int:
    """Возвращает количество экспертов"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM users WHERE user_role = 'expert'")
            result = await cur.fetchone()
            return result[0] if result else 0
        

async def get_all_users(limit: int = 10, offset: int = 0) -> list:
    """Получает список всех пользователей с пагинацией"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT id, user_name, user_surname, user_email, 
                       user_role, account_status, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return await cur.fetchall()

async def update_user_role(user_id: int, new_role: str) -> bool:
    """Обновляет роль пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET user_role = %s WHERE id = %s",
                (new_role, user_id))
            await conn.commit()
            return cur.rowcount > 0

async def delete_user(user_id: int) -> bool:
    """Удаляет пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            await conn.commit()
            return cur.rowcount > 0
        
async def search_users(query: str, limit: int = 10, offset: int = 0) -> list:
    """Поиск пользователей по имени, фамилии или email"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            search_pattern = f"%{query}%"
            await cur.execute("""
                SELECT id, user_name, user_surname, user_email, 
                       user_role, account_status, created_at
                FROM users
                WHERE user_name LIKE %s OR user_surname LIKE %s OR user_email LIKE %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, search_pattern, limit, offset))
            return await cur.fetchall()

async def get_all_articles(limit: int = 10, offset: int = 0) -> list:
    """Получает список всех статей с пагинацией"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT 
                    p.id, 
                    p.topic_name, 
                    p.topic_name_en,
                    p.created_at,
                    u.id as user_id,
                    u.user_name,
                    u.user_surname
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            return await cur.fetchall()
        
async def search_articles(query: str, limit: int = 10, offset: int = 0) -> list:
    """Поиск статей по названию или автору"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            search_pattern = f"%{query}%"
            await cur.execute("""
                SELECT 
                    p.id, 
                    p.topic_name, 
                    p.topic_name_en,
                    p.created_at,
                    u.id as user_id,
                    u.user_name,
                    u.user_surname
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE p.topic_name LIKE %s OR u.user_name LIKE %s OR u.user_surname LIKE %s
                ORDER BY p.created_at DESC
                LIMIT %s OFFSET %s
            """, (search_pattern, search_pattern, search_pattern, limit, offset))
            return await cur.fetchall()
        
async def delete_article(article_id: int) -> bool:
    """Удаляет статью из базы данных"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute("DELETE FROM publics WHERE id = %s", (article_id,))
                await conn.commit()
                return cur.rowcount > 0
            except Exception as e:
                await conn.rollback()
                logging.error(f"Error deleting article: {str(e)}")
                return False

async def insert_into_experts_application(fullName, company, position, expertise, otherExpertise, experience, description):
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                pass
            except Exception as e:
                logging.error(f"Error inserting expert's application: {e}")

async def save_expert_request(
    user_id: int,
    company: str,
    position: str,
    expertise: str,
    experience: int,
    description: str,
    other_expertise: str = ''
) -> bool:
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute("""
                    INSERT INTO expert_requests 
                    (user_id, company, position, expertise, other_expertise, experience, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, company, position, expertise, other_expertise, experience, description))
                await conn.commit()
                return True
            except Exception as e:
                logging.error(f"DB Error saving expert request: {str(e)}")
                return False
            
async def add_like(user_id: int, public_id: int) -> bool:
    """Добавляет лайк к статье. Возвращает True при успехе, False если лайк уже существует."""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO likes (user_id, public_id) VALUES (%s, %s)",
                    (user_id, public_id)
                )
                await conn.commit()
                return True
            except aiomysql.IntegrityError:
                # Лайк уже существует
                return False
            except Exception as e:
                logging.error(f"Ошибка при добавлении лайка: {e}")
                return False

async def remove_like(user_id: int, public_id: int) -> bool:
    """Удаляет лайк с статьи. Возвращает True при успехе."""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM likes WHERE user_id = %s AND public_id = %s",
                (user_id, public_id))
            await conn.commit()
            return cur.rowcount > 0

async def has_liked(user_id: int, public_id: int) -> bool:
    """Проверяет, поставил ли пользователь лайк статье."""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM likes WHERE user_id = %s AND public_id = %s",
                (user_id, public_id))
            return await cur.fetchone() is not None

async def get_likes_count(public_id: int) -> int:
    """Возвращает количество лайков у статьи."""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM likes WHERE public_id = %s",
                (public_id,))
            result = await cur.fetchone()
            return result[0] if result else 0
        

async def check_user_like(user_id: int, public_id: int) -> bool:
    """Проверяет, поставил ли пользователь лайк статье."""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM likes WHERE user_id = %s AND public_id = %s",
                (user_id, public_id))
            return await cur.fetchone() is not None