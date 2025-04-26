from config import *

password = input('Введите пароль: ')



hashed = config.hashed

hashed_password = password

ready_password = []

for i in hashed_password:
    if i in hashed:
        ready_password.append(hashed[i])


print(f'HASHED PASSWORD: {ready_password[::-1]}')


#print(f'INPUTED PASSWORD: {hashed_password}')


