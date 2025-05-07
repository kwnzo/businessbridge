from flask import Flask, render_template, url_for, request, jsonify, json, after_this_request, send_file, redirect, session
from utils.db import init_db, insert_into_users, get_user_by_login, get_user_by_id, update_user_profile, update_user_avatar, delete_user_avatar
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from wtforms import ValidationError
from io import BytesIO  
import hashlib
import time
import re
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import asyncio
import logging

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=604800
)

limiter = Limiter(
    app=app,
    key_func=lambda: request.remote_addr,
    default_limits=["100/day", "10/minute"]
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

with open('data/config.json', 'r')  as f:
    config = json.load(f)

app.secret_key = config['secret-key']  # Сначала установите ключ
csrf = CSRFProtect(app)  # Затем инициализируйте CSRF

@app.route('/')
def home():
    return render_template('index.html')

# ======================================================================================== ГЛАВНАЯ 
@app.route('/index')
def index(name=None):
    user = None
    if 'user_id' in session:
        user = asyncio.run(get_user_by_id(session['user_id']))
    return render_template('index.html', current_user=user)

# ======================================================================================== ПОДТВЕРЖДЕНИЕ РЕГИСТРАЦИИ 
@app.route('/reg/confirm', methods = ('GET', 'POST'))
def confirm():
    return render_template('confirm.html')



# ======================================================================================== ПРОФИЛЬ 
@app.route('/profile')
@login_required
def account():
    user_id = session['user_id']  
    try:
        user = asyncio.run(get_user_by_id(user_id))
        if not user:
            raise ValueError("User not found")
        
        if 'user_phone' in user and user['user_phone']:
            user['formatted_phone'] = format_phone(user['user_phone'])
        
        return render_template('account.html', 
                            user=user,
                            current_user=user)
    except Exception as e:
        session.clear()
        return redirect(url_for('login'))

def format_phone(phone):
    if not phone:
        return ""
    phone = str(phone)
    return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"

app.template_filter('format_phone')(format_phone)

@app.route('/profile/avatar/<int:user_id>')
def user_avatar(user_id):
    user = asyncio.run(get_user_by_id(user_id))
    if user and user.get('user_avatar'):
        return send_file(BytesIO(user['user_avatar']), mimetype='image/jpeg')
    return send_file('static/img/avatar.jpg')

# ======================================================================================== РЕДАКТИРОВАНИЕ ПРОФИЛЯ
@app.route('/profile/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'GET':
        try:
            user_id = session['user_id']
            user = asyncio.run(get_user_by_id(user_id))
            if not user:
                raise ValueError("User not found")
            
            # Форматируем телефон для отображения
            if 'user_phone' in user and user['user_phone']:
                user['formatted_phone'] = format_phone(user['user_phone'])
                
            # Генерируем CSRF токен
            csrf_token = generate_csrf()
            
            return render_template('edit-profile.html', 
                                user=user,
                                current_user=user,  # Добавляем current_user
                                csrf_token=csrf_token)
                                
        except Exception as e:
            logging.error(f"Error loading edit profile: {str(e)}", exc_info=True)
            return redirect(url_for('account'))

    # Обработка POST запроса (оставляем без изменений)
    try:
        user_id = session['user_id']
        form_data = request.form
        files = request.files
        
        update_data = {}
        
        # Проверяем и обновляем основные данные
        if form_data.get('username'):
            update_data['user_name'] = form_data['username']
        if form_data.get('usersurname'):
            update_data['user_surname'] = form_data['usersurname']
        if form_data.get('userdaddy'):
            update_data['user_daddy'] = form_data['userdaddy']
        
        # Обработка телефона
        if form_data.get('phone'):
            cleaned_phone = re.sub(r'\D', '', form_data['phone'])
            if len(cleaned_phone) != 11:
                raise ValueError("Номер телефона должен содержать 11 цифр")
            update_data['user_phone'] = cleaned_phone
        
        # Обработка email
        if form_data.get('email'):
            if not re.match(r"[^@]+@[^@]+\.[^@]+", form_data['email']):
                raise ValueError("Неверный формат email")
            update_data['user_email'] = form_data['email']
        
        # Обработка пароля
        if form_data.get('new_password'):
            if len(form_data['new_password']) < 8:
                raise ValueError("Пароль должен содержать минимум 8 символов")
            if form_data['new_password'] != form_data['confirm_password']:
                raise ValueError("Пароли не совпадают")
            
            # Проверяем старый пароль
            user = asyncio.run(get_user_by_id(user_id))
            if not check_password_hash(user['user_password'], form_data['current_password']):
                raise ValueError("Неверный текущий пароль")
            
            update_data['user_password'] = generate_password_hash(form_data['new_password'])
        
        # Обновляем данные в БД, если есть что обновлять
        if update_data:
            success = asyncio.run(update_user_profile(user_id, update_data))
            if not success:
                raise ValueError("Не удалось обновить данные")
        
        # Обработка аватарки
        if 'avatar' in files and files['avatar'].filename:
            avatar_file = files['avatar']
            if avatar_file.content_length > 2 * 1024 * 1024:  # 2MB limit
                raise ValueError("Размер файла не должен превышать 2MB")
            
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            if '.' in avatar_file.filename and avatar_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                raise ValueError("Недопустимый формат изображения")
            
            avatar_data = avatar_file.read()
            success = asyncio.run(update_user_avatar(user_id, avatar_data))
            if not success:
                raise ValueError("Не удалось обновить аватар")
        
        # Удаление аватарки
        if form_data.get('remove_avatar') == 'true':
            success = asyncio.run(delete_user_avatar(user_id))
            if not success:
                raise ValueError("Не удалось удалить аватар")
        
        return jsonify({
            "success": True,
            "message": "Данные успешно обновлены",
            "redirect": url_for('account')
        })
        
    except Exception as e:
        logging.error(f"Error updating profile: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# ======================================================================================== СОЗДАНИЕ СТАТЬИ 
@app.route('/profile/create-publication', methods = ('GET', 'POST'))
def publications():
    return render_template('create-publication.html')


# ======================================================================================== ОШИБКА 404
@app.route('/error')
def error():
    return render_template('404.html')

# ======================================================================================== РЕГИСТРАЦИЯ
@app.route('/reg', methods=('GET','POST'))
def registration():
    if request.method == "POST":
        try:
            # Получение данных
            username = request.form.get("firstNames")
            usersurname = request.form.get('lastNames')
            userdaddy = request.form.get('middleNames')
            phone = request.form.get('phoneInputs') # Очистка номера
            email = request.form.get('emails')
            password = request.form.get('passwordInputs')

            hashed_password = generate_password_hash(password)
            # Сохранение в БД
            loop.run_until_complete(
                insert_into_users(
                    username=username,
                    usersurname=usersurname,
                    userdaddy=userdaddy,
                    phone=phone,
                    email=email,
                    password=hashed_password
                )
            )

            return jsonify({
                "success": True,
                "redirect": url_for('confirm')  # URL для редиректа
            })

        except Exception as e:
            # Логирование ошибки
            logging.error(f"Ошибка регистрации: {str(e)}")
            if "Duplicate entry" in str(e):
                return jsonify({
                    "success": False,
                    "message": "Номер или почта уже используются"
                }), 500
    
    return render_template('registration.html')


# ======================================================================================== ЛОГИН
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        try:
            csrf_token = generate_csrf()
            return render_template(
                'login.html',
                csrf_token=csrf_token,  # Передаем строку, а не функцию
                page_title="Авторизация"
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации CSRF: {str(e)}")
            # Временное решение, пока не создан error.html
            return "Ошибка сервера", 500

    # Обработка POST-запроса
    try:
        # Валидация CSRF в первую очередь
        validate_csrf(request.form.get('csrf_token'))

        # Безопасное получение данных
        login_credential = request.form.get('login', '')
        password = request.form.get('password', '')
        remember_me = 'rememberMe' in request.form

        # Нормализация данных
        #login_credential = login_credential.strip()
        password = password.strip()

        # Базовые проверки
        print(login_credential, password)
        if not login_credential or not password:
            logger.warning("Попытка входа с пустыми полями")
            return jsonify({
                'success': False,
                'message': 'Все поля обязательны для заполнения'
            }), 400

        # Поиск пользователя в БД
        user = asyncio.run(get_user_by_login(login_credential))
        
        if not user:
            logger.warning(f"Попытка входа несуществующего пользователя: {login_credential}")
            return jsonify({
                'success': False,
                'message': 'Пользователь с такими данными не найден'
            }), 404
            
        # Проверка пароля
        if not check_password_hash(user['user_password'], password):
            logger.warning(f"Неверный пароль для пользователя: {user['id']}")
            return jsonify({
                'success': False,
                'message': 'Неправильный пароль'
            }), 401

        # Проверка статуса аккаунта
        if user['account_status'] != 'verified':
            logger.warning(f"Попытка входа в неподтвержденный аккаунт: {user['id']}")
            return jsonify({
                'success': False,
                'message': 'Аккаунт не подтвержден. Проверьте вашу почту'
            }), 403

        # Создание сессии
        session.clear()
        session.permanent = remember_me
        session['user_id'] = user['id']
        session['_fresh'] = True
        session['user_agent_hash'] = hashlib.sha256(
            request.headers.get('User-Agent', '').encode()
        ).hexdigest()

        logger.info(f"[i] Успешный вход пользователя: {user['id']}")

        return jsonify({
            'success': True,
            'redirect': url_for('account'),
            'user': {
                'id': user['id'],
                'name': f"{user['user_name']} {user['user_surname']}"
            }
        })

    except ValidationError as e:
        logger.error(f"CSRF validation failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Ошибка безопасности. Обновите страницу и попробуйте снова'
        }), 403

    except Exception as e:
        logger.critical(f"Критическая ошибка при входе: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': 'Внутренняя ошибка сервера. Пожалуйста, попробуйте позже'
        }), 500

async def main():
    start = None
    try: 
        start = await init_db()

    except Exception as e:
        logging.error(f'Exception: {e}')

    finally:
        if start == True:
            app.run(debug=True)
        else:
            return logging.error(f"start isn't True")

asyncio.run(main())