
from werkzeug.security import generate_password_hash
import re
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
print(dbpassword, user, db, host, port)

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
        logging.info('database were successfully connected')
        async with conn.cursor() as cursor:
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_name VARCHAR(50) NOT NULL,
                user_surname VARCHAR(50) NOT NULL,
                user_daddy VARCHAR(50), 
                user_like_creator BIGINT NOT NULL DEFAULT 0,
                user_phone VARCHAR(20) NOT NULL UNIQUE, 
                user_email VARCHAR(100) NOT NULL UNIQUE,
                user_passport VARCHAR(50) UNIQUE DEFAULT 0,
                user_password VARBINARY(255) NOT NULL,
                user_publics INT DEFAULT 0,
                user_status INT NOT NULL,
                user_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );


                CREATE TABLE IF NOT EXISTS publics (
                id INT PRIMARY KEY AUTO_INCREMENT,
                public_creator INT NOT NULL,
                topic_name VARCHAR(255) NOT NULL,
                topic_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (public_creator) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS metrics (
                public_id INT PRIMARY KEY,
                likes INT NOT NULL DEFAULT 0,
                comments INT NOT NULL DEFAULT 0,
                views INT NOT NULL DEFAULT 0,
                FOREIGN KEY(public_id) REFERENCES publics(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                publication INT NOT NULL,
                comment_author INT NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(publication) REFERENCES publics(id) ON DELETE CASCADE,
                FOREIGN KEY(comment_author) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS likes (
                user_id INT NOT NULL,
                public_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, public_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (public_id) REFERENCES publics(id) ON DELETE CASCADE
                );
            ''')


    except Exception as e:
        print(f'Exception: {e}')

    finally:
        return True
    

async def insert_into_users(username, usersurname, userdaddy, phone, email, password):
    # Очищаем номер телефона
    cleaned_phone = re.sub(r'\D', '', phone)

    
    # Хешируем пароль
    hashed_password = bcrypt.hash(password)
    
    # Генерируем случайное число
    user_like_creator = random.randint(0, 425152)
    user_status = 1
    
    try:
        conn = await aiomysql.connect(
            user=user,        
            password=dbpassword, 
            db=db,            
            host=host,
            port = port
        )
        async with conn.cursor() as cursor:
            await cursor.execute("""
                INSERT INTO users (
                    user_name, 
                    user_surname, 
                    user_daddy, 
                    user_like_creator,  
                    user_phone, 
                    user_email, 
                    user_password,
                    user_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    username,
                    usersurname,
                    userdaddy,
                    user_like_creator,
                    cleaned_phone,  # Используем очищенный номер
                    email,
                    hashed_password,  # Используем хеш пароля
                    user_status
                ))
            await conn.commit()
        return "INSERTED"
        
    except Exception as e:
        logging.error(f'Exception while insert into users: {e}')
        raise  # Перебрасываем исключение для отладки
        
    finally:
        if 'conn' in locals():
            conn.close()  # Всегда закрывайте соединение!