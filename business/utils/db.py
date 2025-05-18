
from werkzeug.security import generate_password_hash, check_password_hash
import re
from typing import Optional
from passlib.hash import bcrypt
import aiomysql
import asyncio
import logging
import json
import random
import datetime

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

async def get_user_articles(user_id: int, is_owner: bool = False) -> list:
    """Получает статьи пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            if is_owner:
                # Для владельца показываем все статьи
                await cur.execute("""
                    SELECT 
                        id, 
                        topic_name, 
                        COALESCE(topic_name_en, 'no-slug') as topic_name_en,
                        topic_text,
                        preview_image,
                        created_at,
                        public_status
                    FROM publics 
                    WHERE public_creator = %s
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                # Для других пользователей показываем только принятые статьи
                await cur.execute("""
                    SELECT 
                        id, 
                        topic_name, 
                        COALESCE(topic_name_en, 'no-slug') as topic_name_en,
                        topic_text,
                        preview_image,
                        created_at,
                        'accept' as public_status
                    FROM publics 
                    WHERE public_creator = %s AND public_status = 'accept'
                    ORDER BY created_at DESC
                """, (user_id,))
            return await cur.fetchall()

        
       

async def get_article_by_id(article_id: int) -> Optional[dict]:
    """Получает статью по ID (без проверки статуса)"""
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
                    p.*,
                    u.user_name,
                    u.user_surname
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE p.id = %s
                LIMIT 1
            """, (article_id,))
            return await cur.fetchone()
        

async def record_view(public_id: int, user_id: int = None):
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cursor:
            try:
                # Обновляем общий счётчик просмотров
                await cursor.execute("""
                    INSERT INTO publication_stats (public_id, views)
                    VALUES (%s, 1)
                    ON DUPLICATE KEY UPDATE views = views + 1
                """, (public_id,))
                
                # Записываем детализированный просмотр (если пользователь авторизован)
                if user_id:
                    await cursor.execute("""
                        INSERT INTO views (public_id, user_id)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE created_at = NOW()
                    """, (public_id, user_id))
                
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logging.error(f"Ошибка записи просмотра: {str(e)}")
                raise
                
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
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                try:
                    await cursor.execute('''
                        SELECT 
                            p.id, 
                            p.topic_name, 
                            p.topic_name_en, 
                            p.preview_image,
                            p.public_status
                        FROM publics p
                        LEFT JOIN publication_stats ps ON p.id = ps.public_id
                        WHERE p.public_status = 'accept'
                        ORDER BY ps.views DESC
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
        

async def get_expert_requests(
    search: str = '',
    date_from: str = '',
    date_to: str = '',
    sort: str = 'newest',
    limit: int = 10,
    offset: int = 0
) -> list:
    """Получает список заявок с фильтрацией"""
    async with aiomysql.connect(
        host=host,
        port=port,
        user=user,
        password=dbpassword,
        db=db
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Базовый запрос
            sql = """
                SELECT 
                    er.id, 
                    er.company, 
                    er.position, 
                    er.expertise,
                    er.other_expertise,
                    er.experience,
                    er.description,
                    er.created_at,
                    u.id as user_id,
                    u.user_name,
                    u.user_surname,
                    u.user_email
                FROM expert_requests er
                JOIN users u ON er.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            # Добавляем условия фильтрации
            if search:
                sql += " AND (u.user_name LIKE %s OR u.user_surname LIKE %s OR er.company LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            if date_from:
                sql += " AND DATE(er.created_at) >= %s"
                params.append(date_from)
            
            if date_to:
                sql += " AND DATE(er.created_at) <= %s"
                params.append(date_to)
            
            # Добавляем сортировку
            sql += " ORDER BY er.created_at " + ("DESC" if sort == 'newest' else "ASC")
            
            # Добавляем пагинацию
            if limit:
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
            
            # Выполняем запрос
            await cur.execute(sql, params)
            return await cur.fetchall()

async def get_expert_requests_count(
    search: str = '',
    date_from: str = '',
    date_to: str = ''
) -> int:
    """Получает количество заявок с учетом фильтров"""
    async with aiomysql.connect(
        host=host,
        port=port,
        user=user,
        password=dbpassword,
        db=db
    ) as conn:
        async with conn.cursor() as cur:
            sql = """
                SELECT COUNT(*)
                FROM expert_requests er
                JOIN users u ON er.user_id = u.id
                WHERE 1=1
            """
            params = []
            
            if search:
                sql += " AND (u.user_name LIKE %s OR u.user_surname LIKE %s OR er.company LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])
            
            if date_from:
                sql += " AND DATE(er.created_at) >= %s"
                params.append(date_from)
            
            if date_to:
                sql += " AND DATE(er.created_at) <= %s"
                params.append(date_to)
            
            await cur.execute(sql, params)
            result = await cur.fetchone()
            return result[0] if result else 0
        
        
async def approve_expert_request_db(request_id: int) -> bool:
    """Одобряет заявку на эксперта и обновляет роль пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                # Получаем user_id из заявки
                await cur.execute(
                    "SELECT user_id FROM expert_requests WHERE id = %s",
                    (request_id,))
                result = await cur.fetchone()
                if not result:
                    return False
                
                user_id = result[0]
                
                # Обновляем роль пользователя
                await cur.execute(
                    "UPDATE users SET user_role = 'expert' WHERE id = %s",
                    (user_id,))
                
                # Удаляем заявку
                await cur.execute(
                    "DELETE FROM expert_requests WHERE id = %s",
                    (request_id,))
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                logging.error(f"Error approving expert request: {str(e)}")
                return False

async def reject_expert_request_db(request_id: int, rejection_reason: str) -> bool:
    """Отклоняет заявку на эксперта с сохранением причины в user_data"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                # Получаем user_id из заявки
                await cur.execute(
                    "SELECT user_id FROM expert_requests WHERE id = %s",
                    (request_id,))
                result = await cur.fetchone()
                if not result:
                    return False
                
                user_id = result[0]
                
                # Получаем текущий user_data
                await cur.execute(
                    "SELECT user_data FROM users WHERE id = %s",
                    (user_id,))
                user_data = await cur.fetchone()
                user_data = json.loads(user_data[0]) if user_data and user_data[0] else {}
                
                # Добавляем информацию об отказе
                if 'expert_requests' not in user_data:
                    user_data['expert_requests'] = {}
                
                user_data['expert_requests']['last_rejection'] = {
                    'request_id': request_id,
                    'reason': rejection_reason,
                    'date': datetime.datetime.now().isoformat()
                }
                
                # Обновляем user_data
                await cur.execute(
                    "UPDATE users SET user_data = %s WHERE id = %s",
                    (json.dumps(user_data), user_id))
                
                # Удаляем заявку
                await cur.execute(
                    "DELETE FROM expert_requests WHERE id = %s",
                    (request_id,))
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                logging.error(f"Error rejecting expert request: {str(e)}")
                return False
        
async def get_expert_request_details(request_id: int) -> Optional[dict]:
    """Получает детали заявки на эксперта"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""
                SELECT company, position, expertise, other_expertise, experience, description
                FROM expert_requests
                WHERE id = %s
                LIMIT 1
            """, (request_id,))
            return await cur.fetchone()
        
async def get_user_rejections(user_id: int) -> dict:
    """Получает историю отклоненных заявок пользователя"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT user_data FROM users WHERE id = %s",
                (user_id,))
            result = await cur.fetchone()
            if not result or not result['user_data']:
                return {}
            
            user_data = json.loads(result['user_data'])
            return user_data.get('expert_requests', {})
        
async def get_publics_for_approve():
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('SELECT * FROM business.publics WHERE public_status = "waiting"')
            data = await cur.fetchall()
            if not data:
                return []
            
            return data 
        

async def has_expert_request(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя активная заявка на эксперта"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT 1 FROM expert_requests WHERE user_id = %s",
                (user_id,))
            return await cur.fetchone() is not None
        

async def get_articles_for_review(
    query: str = '',
    date_from: str = '',
    date_to: str = '',
    sort: str = 'newest',
    limit: int = 10,
    offset: int = 0
) -> list:
    """Получает список статей на проверку с фильтрацией"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            sql = """
                SELECT 
                    p.id, 
                    p.topic_name, 
                    p.public_status,
                    p.created_at,
                    p.public_creator,
                    u.user_name,
                    u.user_surname
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE p.public_status = 'waiting'
            """
            params = []
            
            if query:
                sql += " AND (p.topic_name LIKE %s OR u.user_name LIKE %s OR u.user_surname LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if date_from:
                sql += " AND DATE(p.created_at) >= %s"
                params.append(date_from)
            
            if date_to:
                sql += " AND DATE(p.created_at) <= %s"
                params.append(date_to)
            
            sql += " ORDER BY p.created_at " + ("DESC" if sort == 'newest' else "ASC")
            
            if limit:
                sql += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
            
            await cur.execute(sql, params)
            return await cur.fetchall()

async def get_articles_for_review_count(
    query: str = '',
    date_from: str = '',
    date_to: str = ''
) -> int:
    """Получает количество статей на проверке с учетом фильтров"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            sql = """
                SELECT COUNT(*)
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE p.public_status = 'waiting'
            """
            params = []
            
            if query:
                sql += " AND (p.topic_name LIKE %s OR u.user_name LIKE %s OR u.user_surname LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if date_from:
                sql += " AND DATE(p.created_at) >= %s"
                params.append(date_from)
            
            if date_to:
                sql += " AND DATE(p.created_at) <= %s"
                params.append(date_to)
            
            await cur.execute(sql, params)
            result = await cur.fetchone()
            return result[0] if result else 0

async def update_article_status(article_id: int, status: str) -> bool:
    """Обновляет статус статьи"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE publics SET public_status = %s WHERE id = %s",
                (status, article_id))
            await conn.commit()
            return cur.rowcount > 0

async def reject_article_db(article_id: int, rejection_reason: str) -> bool:
    """Отклоняет статью с сохранением причины"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            try:
                # Обновляем статус статьи
                await cur.execute(
                    "UPDATE publics SET public_status = 'reject' WHERE id = %s",
                    (article_id,))
                
                # Здесь можно добавить сохранение причины отклонения,
                # например, в отдельную таблицу или в JSON поле
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                logging.error(f"Error rejecting article: {str(e)}")
                return False
            
async def search_articles(
    query: str = '',
    status: str = '',
    date_from: str = '',
    date_to: str = '',
    sort: str = 'newest',  # Добавляем параметр сортировки
    limit: int = 10,
    offset: int = 0
) -> list:
    """Поиск статей с фильтрами"""
    async with aiomysql.connect(
        host=host,
        port=port,
        user=user,
        password=dbpassword,
        db=db
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            sql = """
                SELECT 
                    p.id, 
                    p.topic_name, 
                    p.topic_name_en,
                    p.created_at,
                    p.public_status,
                    u.id as user_id,
                    u.user_name,
                    u.user_surname
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE 1=1
            """
            params = []
            
            if query:
                sql += " AND (p.topic_name LIKE %s OR u.user_name LIKE %s OR u.user_surname LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if status:
                sql += " AND p.public_status = %s"
                params.append(status)
                
            if date_from:
                sql += " AND DATE(p.created_at) >= %s"
                params.append(date_from)
                
            if date_to:
                sql += " AND DATE(p.created_at) <= %s"
                params.append(date_to)
            
            # Добавляем сортировку
            sql += " ORDER BY p.created_at " + ("DESC" if sort == 'newest' else "ASC")
            
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            await cur.execute(sql, params)
            return await cur.fetchall()

async def get_filtered_articles_count(
    query: str = '',
    status: str = '',
    date_from: str = '',
    date_to: str = ''
) -> int:
    """Получение количества статей с фильтрами"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            sql = """
                SELECT COUNT(*)
                FROM publics p
                JOIN users u ON p.public_creator = u.id
                WHERE 1=1
            """
            params = []
            
            if query:
                sql += " AND (p.topic_name LIKE %s OR u.user_name LIKE %s OR u.user_surname LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if status:
                sql += " AND p.public_status = %s"
                params.append(status)
                
            if date_from:
                sql += " AND p.created_at >= %s"
                params.append(f"{date_from} 00:00:00")
                
            if date_to:
                sql += " AND p.created_at <= %s"
                params.append(f"{date_to} 23:59:59")
                
            await cur.execute(sql, params)
            result = await cur.fetchone()
            return result[0] if result else 0
        

async def search_users(
    query: str = '',
    role: str = '',
    status: str = '',
    date_from: str = '',
    date_to: str = '',
    sort: str = 'newest',
    limit: int = 10,
    offset: int = 0
) -> list:
    """Поиск пользователей с фильтрами"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            sql = """
                SELECT 
                    id, 
                    user_name, 
                    user_surname, 
                    user_email,
                    user_role,
                    account_status,
                    created_at
                FROM users
                WHERE 1=1
            """
            params = []
            
            if query:
                sql += " AND (user_name LIKE %s OR user_surname LIKE %s OR user_email LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if role:
                sql += " AND user_role = %s"
                params.append(role)
                
            if status:
                sql += " AND account_status = %s"
                params.append(status)
                
            if date_from:
                sql += " AND DATE(created_at) >= %s"
                params.append(date_from)
                
            if date_to:
                sql += " AND DATE(created_at) <= %s"
                params.append(date_to)
            
            # Добавляем сортировку
            sql += " ORDER BY created_at " + ("DESC" if sort == 'newest' else "ASC")
            
            sql += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            await cur.execute(sql, params)
            return await cur.fetchall()

async def get_filtered_users_count(
    query: str = '',
    role: str = '',
    status: str = '',
    date_from: str = '',
    date_to: str = ''
) -> int:
    """Получение количества пользователей с фильтрами"""
    async with aiomysql.connect(
            user=user,
            password=dbpassword,
            db=db,
            host=host,
            port=port
    ) as conn:
        async with conn.cursor() as cur:
            sql = """
                SELECT COUNT(*)
                FROM users
                WHERE 1=1
            """
            params = []
            
            if query:
                sql += " AND (user_name LIKE %s OR user_surname LIKE %s OR user_email LIKE %s)"
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
            
            if role:
                sql += " AND user_role = %s"
                params.append(role)
                
            if status:
                sql += " AND account_status = %s"
                params.append(status)
                
            if date_from:
                sql += " AND DATE(created_at) >= %s"
                params.append(date_from)
                
            if date_to:
                sql += " AND DATE(created_at) <= %s"
                params.append(date_to)
                
            await cur.execute(sql, params)
            result = await cur.fetchone()
            return result[0] if result else 0


