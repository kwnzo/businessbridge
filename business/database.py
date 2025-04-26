import aiomysql
import asyncio
import logging


logger = logging.getLogger(__name__)
loop = asyncio.get_event_loop()




async def init_db():
    try:
        conn = await aiomysql.connect(
            user = 'root',
            password='t7Er3kOQkid2D!',
            db = 'business',
            host = '127.0.0.1'
            )
        logging.info('database were successfully connected')
        async with conn.cursor() as cursor:
            await cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
            id int auto_increment primary key,
            user_email varbinary(255) not null,
            user_password varbinary(100) not null,
            user_name varchar(255) not null,
            user_surname varchar(255) not null,
            user_daddy varhcar(255) not null,
            user_phone int not null,
            user_passport int
                                 )            
''')


    except Exception as e:
        print(f'Exception: {e}')