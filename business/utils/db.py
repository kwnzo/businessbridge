import aiomysql
import asyncio
import logging
import json

with open('data/config.json', 'r') as f:
    config = json.load(f)

password = config['password']
user = config['user']
db = config['db']
host = config['host']

logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()

async def init_db():
    try:
        conn = await aiomysql.connect(
            user = user,
            password=password,
            db = db,
            host = host
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
                user_passport VARCHAR(50) UNIQUE,
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