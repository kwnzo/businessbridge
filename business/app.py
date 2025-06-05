from flask import Flask, render_template, url_for, request, jsonify, json, after_this_request, send_file, redirect, session, Response, abort
from utils.db import (init_db,get_views, get_publics, record_view, 
                      insert_into_users, get_user_by_login, get_user_by_id, 
                      update_user_profile, update_user_avatar, 
                      delete_user_avatar, create_publication, get_user_articles, 
                      get_article_by_id, get_image_data, save_expert_request,
                      add_like, remove_like, has_liked, get_likes_count, check_user_like, 
                      has_expert_request, get_random_quote, get_all_experts, 
                      get_expert_articles, get_expert_info, EXPERTISE_AREAS, delete_article_db,
                      get_passport_request, has_pending_passport_request, create_passport_request,
                      get_user_notifications, mark_notifications_as_read, get_unread_notifications_count,
                      get_all_articles_for_display, get_friends, get_pending_requests, get_friendship_status, 
                      create_notification, send_friend_request, respond_to_friend_request,
                      get_private_chat_between_users, create_chat, add_user_to_chat)
from flask_limiter import Limiter
from flask_mysqldb import MySQL
from flask_login import current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from wtforms import ValidationError
from io import BytesIO  
import hashlib
import time
import aiomysql
import re
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import asyncio
import logging
from admin import admin_bp

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
    default_limits=["100/day", "100/minute"]
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

app.register_blueprint(admin_bp)


@app.route('/')
def home():
    user = None
    data = asyncio.run(get_publics(12))
    quote = asyncio.run(get_random_quote())  # Получаем случайную цитату
    has_unread = False
    unread_count = 0
    
    if 'user_id' in session:
        user = asyncio.run(get_user_by_id(session['user_id']))
        has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
        unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
    
        return render_template('index.html', 
                         current_user=user, 
                         data=data,
                         random_quote=quote,
                         has_unread_notifications=has_unread,
                         unread_count=unread_count)  # Передаем цитату в шаблон
    else:
        return render_template('index.html',
                         data=data,
                         random_quote=quote)

# ======================================================================================== ГЛАВНАЯ 
@app.route('/index')
def index(name=None):
    user = None
    data = asyncio.run(get_publics(12))
    quote = asyncio.run(get_random_quote())  # Получаем случайную цитату
    has_unread = False
    unread_count = 0
    
    if 'user_id' in session:
        user = asyncio.run(get_user_by_id(session['user_id']))
        has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
        unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
    
    return render_template('index.html', 
                         current_user=user, 
                         data=data,
                         random_quote=quote,
                         has_unread_notifications=has_unread,
                         unread_count=unread_count)  # Передаем цитату в шаблон

@app.route('/article_image/<int:article_id>')
def article_images(article_id):
    try:
        image_data, image_type = asyncio.run(get_image_data(article_id))
        
        if not image_data:
            abort(404)
            
        mime_type = f'image/{image_type.lower()}' if image_type else 'image/jpeg'
        
        return Response(
            image_data,
            mimetype=mime_type,
            headers={
                'Cache-Control': 'public, max-age=604800',
                'Content-Disposition': f'inline; filename="article_{article_id}"'
            }
        )
    
    except Exception as e:
        logging.error(f"Error loading image for article {article_id}: {e}")
        abort(500)

# ======================================================================================== ПОДТВЕРЖДЕНИЕ РЕГИСТРАЦИИ 
@app.route('/reg/confirm', methods = ('GET', 'POST'))
def confirm():
    return render_template('confirm.html')



# ======================================================================================== ПРОФИЛЬ 
@app.route('/profile')
@login_required
def account():
    try:
        user_id = session['user_id']
        user = asyncio.run(get_user_by_id(user_id))
        has_unread = asyncio.run(get_unread_notifications_count(user_id)) > 0
        unread_count = asyncio.run(get_unread_notifications_count(user_id))
        
        expert_info = None
        if user['user_role'] == 'expert':
            expert_info = asyncio.run(get_expert_info(user_id))

        user_articles = asyncio.run(get_user_articles(user_id, is_owner=True))
        has_request = asyncio.run(has_expert_request(user_id))
        
        return render_template('account.html', 
                            user=user,
                            current_user=user,
                            expert_info=expert_info,
                            EXPERTISE_AREAS=EXPERTISE_AREAS,
                            user_articles=user_articles,
                            has_expert_request=has_request,
                            is_own_profile=True,
                            has_unread_notifications=has_unread,
                            unread_count=unread_count)
    except Exception as e:
        logging.error(f"Ошибка профиля: {str(e)}")
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
            has_unread = asyncio.run(get_unread_notifications_count(user_id)) > 0
            unread_count = asyncio.run(get_unread_notifications_count(user_id))
            
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
                                csrf_token=csrf_token,
                                has_unread_notifications=has_unread,
                                unread_count=unread_count)
                                
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
@app.route('/profile/create-publication', methods=['GET', 'POST'])
@login_required
def create_publication_route():
    # Проверяем статус аккаунта
    user = asyncio.run(get_user_by_id(session['user_id']))
    has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
    unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))

    if user['account_status'] != 'verified':
        if request.method == 'POST':
            return jsonify({
                "success": False,
                "message": "Для создания статей необходимо подтвердить аккаунт",
                "show_verification_modal": True,
                "redirect": url_for('passport_verification')
            }), 403
        else:
            # Для GET запроса перенаправляем с параметром для показа модального окна
            return redirect(url_for('account', showVerificationModal='true'))

    # Остальной код обработчика
    if request.method == 'GET':
        csrf_token = generate_csrf()
        return render_template('create-publication.html', 
                            csrf_token=csrf_token,
                            current_user=user,
                            has_unread_notifications=has_unread,
                            unread_count=unread_count)
    
    if request.method == 'POST':
        try:
            print("Полученные данные формы:", request.form)  # Отладочное сообщение
            print("Полученные файлы:", request.files)       # Отладочное сообщение
            
            validate_csrf(request.form.get('csrf_token'))
            
            title = request.form.get('title')
            content = request.form.get('content')
            category = request.form.get('category')
            image = request.files.get('image')
            
            print(f"Поля: title={title}, content={content}, category={category}")  # Отладочное сообщение
            
            if not title or not content or not category:
                return jsonify({
                    "success": False,
                    "message": "Все обязательные поля должны быть заполнены",
                    "missing_fields": {
                        "title": not bool(title),
                        "content": not bool(content),
                        "category": not bool(category)
                    }
                }), 400
                
            image_data = None
            if image and image.filename:
                if image.content_length > 5 * 1024 * 1024:
                    return jsonify({
                        "success": False,
                        "message": "Размер изображения не должен превышать 5MB"
                    }), 400
                
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                if '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                    return jsonify({
                        "success": False,
                        "message": "Недопустимый формат изображения"
                    }), 400
                
                image_data = image.read()
            
            publication_id = asyncio.run(
                create_publication(
                    user_id=session['user_id'],
                    title=title,
                    content=content,
                    image_data=image_data,
                    category=category  # Передаем категорию
                )
            )
            
            return jsonify({
                "success": True,
                "message": "Статья успешно создана",
                "publication_id": publication_id,
                "redirect": "/profile"
            })
            
        except ValidationError as e:
            return jsonify({
                "success": False,
                "message": "Ошибка безопасности. Обновите страницу и попробуйте снова"
            }), 403
            
        except Exception as e:
            logging.error(f"Ошибка при создании статьи: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Произошла ошибка при создании статьи"
            }), 500

@app.route('/experts')
def experts():
    user = None
    has_unread = False
    unread_count = 0
    
    if 'user_id' in session:
        user = asyncio.run(get_user_by_id(session['user_id']))
        has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
        unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
    
    experts_list = asyncio.run(get_all_experts())
    
    # Получаем статьи для каждого эксперта
    for expert in experts_list:
        expert['articles'] = asyncio.run(get_expert_articles(expert['id']))
    
    return render_template(
        'experts.html',
        current_user=user,
        experts=experts_list,
        has_unread_notifications=has_unread,
        unread_count=unread_count
    )

# ======================================================================================== ПРОСМОТР СТАТЬИ
@app.route('/article-image/<int:article_id>')
def article_image(article_id):
    try:
        article = asyncio.run(get_article_by_id(article_id))
        if not article or not article.get('preview_image'):
            return send_file('static/img/article-placeholder.png')
        
        return send_file(
            BytesIO(article['preview_image']),
            mimetype='image/jpeg',
            download_name=f"article_{article_id}.jpg"
        )
    except Exception as e:
        logging.error(f"Error loading article image: {str(e)}")
        return send_file('static/img/article-placeholder.png')

@app.route('/article/<int:article_id>/<article_slug>')
@app.route('/article/<int:article_id>')
def view_article(article_id, article_slug=None):
    try:
        article = asyncio.run(get_article_by_id(article_id))
        if not article:
            return render_template('404.html'), 404
        
        # Получаем текущего пользователя
        current_user = None
        has_unread = False
        unread_count = 0
        
        if 'user_id' in session:
            current_user = asyncio.run(get_user_by_id(session['user_id']))
            has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
            unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
        
        # Проверка прав доступа
        is_owner = current_user and current_user['id'] == article['public_creator']
        is_admin = current_user and current_user['user_role'] == 'admin'
        
        if article['public_status'] == 'reject' and not (is_owner or is_admin):
            return render_template('404.html'), 404
        
        if article['public_status'] == 'waiting' and not (is_owner or is_admin):
            return render_template('404.html'), 404
        
        # Записываем просмотр (если статья доступна)
        if 'viewed_articles' not in session:
            session['viewed_articles'] = []

        if article_id not in session['viewed_articles']:
            asyncio.run(record_view(article_id))
            session['viewed_articles'].append(article_id)

        
        # Проверка slug и редирект при необходимости
        if article_slug and article_slug != article.get('topic_name_en', ''):
            return redirect(url_for('view_article', 
                                 article_id=article_id,
                                 article_slug=article['topic_name_en']))
        
        # Получаем данные автора
        author = asyncio.run(get_user_by_id(article['public_creator']))
        
        # Получаем статистику
        article_views = asyncio.run(get_views(article_id))
        likes_count = asyncio.run(get_likes_count(article_id))
        user_has_liked = False
        
        if 'user_id' in session:
            user_has_liked = asyncio.run(check_user_like(session['user_id'], article_id))
        
        return render_template(
            'reading-publication.html',
            article=article,
            author=author,
            current_user=current_user,
            article_views=article_views,
            user_has_liked=user_has_liked,
            likes_count=likes_count,
            is_article_owner=is_owner,
            is_admin=is_admin,
            has_unread_notifications=has_unread,
            unread_count=unread_count
        )
    except Exception as e:
        logging.error(f"Ошибка просмотра статьи: {str(e)}", exc_info=True)
        return render_template('404.html'), 404

@app.route('/api/like', methods=['POST'])
@csrf.exempt
@login_required
def handle_like():
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Неверный формат запроса'}), 400
            
        data = request.get_json()
        public_id = data.get('public_id')
        user_id = session['user_id']
        
        if not public_id:
            return jsonify({'success': False, 'message': 'Не указан ID статьи'}), 400
        
        # Проверяем лайк
        has_like = asyncio.run(check_user_like(user_id, public_id))
        
        if has_like:
            success = asyncio.run(remove_like(user_id, public_id))
            action = 'removed'
        else:
            success = asyncio.run(add_like(user_id, public_id))
            action = 'added'
        
        if success:
            likes_count = asyncio.run(get_likes_count(public_id))
            return jsonify({
                'success': True,
                'action': action,
                'likes_count': likes_count
            })
        return jsonify({'success': False, 'message': 'Ошибка обработки лайка'}), 400
            
    except Exception as e:
        logging.error(f"Ошибка обработки лайка: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500
    


@app.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    try:
        # Проверка CSRF токена
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            return jsonify({'success': False, 'message': 'Отсутствует CSRF токен'}), 400
            
        validate_csrf(csrf_token)
        
        # Получаем статью для проверки владельца
        article = asyncio.run(get_article_by_id(article_id))
        if not article:
            return jsonify({'success': False, 'message': 'Статья не найдена'}), 404
            
        # Проверяем, что пользователь - владелец или администратор
        current_user = asyncio.run(get_user_by_id(session['user_id']))
        if current_user['id'] != article['public_creator'] and current_user['user_role'] != 'admin':
            return jsonify({'success': False, 'message': 'Недостаточно прав'}), 403
        
        # Удаляем статью
        success = asyncio.run(delete_article_db(article_id))
        if success:
            return jsonify({'success': True, 'message': 'Статья успешно удалена'})
        return jsonify({'success': False, 'message': 'Ошибка при удалении статьи'}), 500
    except Exception as e:
        logging.error(f"Error deleting article: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500


# ======================================================================================== ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    print(f"Запрошен профиль пользователя с ID: {user_id}")  # Отладочное сообщение
    try:
        user = asyncio.run(get_user_by_id(user_id))
        print(f"Найден пользователь: {user}")  # Отладочное сообщение

        if not user:
            print("Пользователь не найден")  # Отладочное сообщение
            return render_template('404.html'), 404
        
        current_user = None
        has_unread = False
        unread_count = 0
        friendship_status = None
        
        if 'user_id' in session:
            current_user = asyncio.run(get_user_by_id(session['user_id']))
            has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
            unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
            
            # Получаем статус дружбы, если пользователь авторизован
            friendship_status, friendship_requester = asyncio.run(get_friendship_status(
                current_user['id'], 
                user_id
            )) if 'user_id' in session else (None, None)
        
        expert_info = None
        if user['user_role'] == 'expert':
            expert_info = asyncio.run(get_expert_info(user_id))
        
        is_own_profile = 'user_id' in session and session['user_id'] == user_id
        user_articles = asyncio.run(get_user_articles(user_id, is_owner=is_own_profile))

        return render_template(
            'account.html',
            user=user,
            expert_info=expert_info,
            EXPERTISE_AREAS=EXPERTISE_AREAS,
            current_user=current_user,
            user_articles=user_articles,
            is_own_profile=is_own_profile,
            friendship_status=friendship_status,
            friendship_requester=friendship_requester,  # Добавляем информацию об отправителе
            has_unread_notifications=has_unread,
            unread_count=unread_count
        )
    except Exception as e:
        logging.error(f"Error viewing user profile: {str(e)}")
        return render_template('404.html'), 404

    
# ======================================================================================== ЭКСПЕРТЫ
@app.route('/expert-request', methods=['GET', 'POST'])
@login_required
def expert_request():
    user = asyncio.run(get_user_by_id(session['user_id']))
    if user['account_status'] != 'verified':
        return redirect(url_for('account'))

    if request.method == "POST":
        try:

            validate_csrf(request.headers.get('X-CSRFToken'))  # Валидация CSRF

            # Получаем JSON данные и CSRF токен
            data = request.get_json()

            # Валидация обязательных полей
            required_fields = ['company', 'position', 'expertise', 'experience', 'description']
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"Поле {field} обязательно для заполнения")

            # Сохраняем заявку в БД
            success = asyncio.run(save_expert_request(
                user_id=session['user_id'],
                company=data['company'],
                position=data['position'],
                expertise=data['expertise'],
                experience=int(data['experience']),
                description=data['description'],
                other_expertise=data.get('otherExpertise', '')
            ))

            if not success:
                raise ValueError("Ошибка сохранения заявки")

            return jsonify({
                "success": True,
                "redirect": '/profile'
            })

        except ValidationError as e:
            return jsonify({"success": False, "message": "CSRF токен недействителен"}), 403
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception as e:
            logging.error(f"Ошибка экспертной заявки: {str(e)}")
            return jsonify({"success": False, "message": "Внутренняя ошибка сервера"}), 500

    # GET запрос
    if request.method == 'GET':
        csrf_token = generate_csrf()
    return render_template('expert-request.html', 
                         current_user=user,
                         csrf_token=csrf_token)
    

# ======================================================================================== ОШИБКА 404
@app.errorhandler(404)
def error(error):
    return render_template('404.html'), 404

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
            }), 200

        except Exception as e:
            # Логирование ошибки
            logging.error(f"Ошибка регистрации: {str(e)}")
            if "Duplicate entry" in str(e):
                return jsonify({
                    "success": False,
                    "message": "Номер или почта уже используются"
                }), 500
    
    return render_template('registration.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return render_template('index.html')

@app.route('/testing')
def tests():
    data = session.clear()
    if data:
        return data
    else:
        return "none", 200
    

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
    

@app.route('/chats')
@login_required
def chat_page():
    id_user = session['user_id']
    user = asyncio.run(get_user_by_id(session['user_id']))
    has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
    unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
    
    # Получаем список друзей для чатов
    friends = asyncio.run(get_friends(session['user_id']))
    
    return render_template('chats.html', 
                         current_user=user,
                         current_user_id = id_user,
                         friends=friends,
                         has_unread_notifications=has_unread,
                         unread_count=unread_count)


@app.route('/create_private_chat', methods=['POST'])
@csrf.exempt  # отключаем CSRF для fetch-запроса
def create_private_chat():
    # ✅ Получаем ID текущего юзера из сессии
    user1 = session.get('user_id')
    if not user1:
        print("❌ Нет user_id в сессии")
        return jsonify({'error': 'Unauthorized'}), 401

    # ✅ Парсим тело запроса
    try:
        data = request.get_json()
        user2 = int(data.get('friend_id'))
    except Exception as e:
        print("❌ Неверный формат данных:", e)
        return jsonify({'error': 'Invalid data'}), 400

    print(f"📩 Запрос на создание чата между {user1} и {user2}")

    # ✅ Проверка: уже существует чат?
    existing_chat = asyncio.run(get_private_chat_between_users(user1, user2))
    if existing_chat:
        print(f"✅ Уже есть чат: {existing_chat['id']}")
        return jsonify({'chat_id': existing_chat['id']})

    # ✅ Создаём новый чат
    new_chat_id = asyncio.run(create_chat(name='', is_group=False))
    asyncio.run(add_user_to_chat(new_chat_id, user1))
    asyncio.run(add_user_to_chat(new_chat_id, user2))
    print(f"✅ Новый чат создан: {new_chat_id}")

    return jsonify({'chat_id': new_chat_id})


@app.route('/profile/passport-verification', methods=['GET', 'POST'])
@login_required
def passport_verification():
    user_id = session['user_id']
    current_user = asyncio.run(get_user_by_id(user_id))
    has_unread = asyncio.run(get_unread_notifications_count(user_id)) > 0
    unread_count = asyncio.run(get_unread_notifications_count(user_id))

    
    # Если аккаунт уже подтвержден, перенаправляем в профиль
    if current_user['account_status'] == 'verified':
        return redirect(url_for('account'))
    
    if request.method == 'GET':
        try:
            # Проверяем, есть ли уже заявка
            existing_request = asyncio.run(get_passport_request(user_id))
        
            if existing_request and existing_request['status'] == 'pending':
                return render_template('passport-verification.html', 
                                    current_user=current_user,
                                    pending_request=True,
                                    has_unread_notifications=has_unread,
                                    unread_count=unread_count)

            
            csrf_token = generate_csrf()
            return render_template('passport-verification.html', 
                                    current_user=current_user,
                                    csrf_token=csrf_token,
                                    has_unread_notifications=has_unread,
                                    unread_count=unread_count)
            
        except Exception as e:
                logging.error(f"Error loading passport verification page: {str(e)}")
                return redirect(url_for('account'))

    # Обработка POST запроса
    try:
        validate_csrf(request.form.get('csrf_token'))
        
        # Проверяем, нет ли уже ожидающей заявки
        if asyncio.run(has_pending_passport_request(user_id)):
            return jsonify({
                "success": False,
                "message": "У вас уже есть ожидающая заявка на верификацию"
            }), 400
        
        # Получаем данные формы
        issued_by = request.form.get('issued_by')
        issue_date = request.form.get('issue_date')
        division_code = request.form.get('division_code')
        series = request.form.get('series')
        number = request.form.get('number')
        gender = request.form.get('gender')
        birth_date = request.form.get('birth_date')
        birth_place = request.form.get('birth_place')
        passport_photo = request.files.get('passport_photo')
        
        # Валидация данных
        if not all([issued_by, issue_date, division_code, series, number, 
                   gender, birth_date, birth_place, passport_photo]):
            return jsonify({
                "success": False,
                "message": "Все обязательные поля должны быть заполнены"
            }), 400
        
        # Проверка размера файла (до 5MB)
        if passport_photo.content_length > 5 * 1024 * 1024:
            return jsonify({
                "success": False,
                "message": "Размер файла не должен превышать 5MB"
            }), 400
        
        # Проверка формата файла
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        file_ext = passport_photo.filename.rsplit('.', 1)[1].lower() if '.' in passport_photo.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                "success": False,
                "message": "Допустимые форматы изображений: JPG, PNG"
            }), 400
        
        # Сохраняем заявку
        request_id = asyncio.run(create_passport_request(
            user_id=user_id,
            issued_by=issued_by,
            issue_date=issue_date,
            division_code=division_code,
            series=series,
            number=number,
            gender=gender,
            birth_date=birth_date,
            birth_place=birth_place,
            passport_photo=passport_photo.read()
        ))
        
        return jsonify({
            "success": True,
            "message": "Заявка на верификацию успешно отправлена",
            "redirect": url_for('account')
        })
        
    except ValidationError as e:
        return jsonify({
            "success": False,
            "message": "Ошибка безопасности. Обновите страницу и попробуйте снова"
        }), 403
        
    except Exception as e:
        logging.error(f"Error submitting passport verification: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Произошла ошибка при отправке заявки"
        }), 500

@app.route('/passport-photo/<int:request_id>')
@login_required
def get_passport_photo(request_id):
    try:
        # Проверяем, что пользователь имеет доступ к этому фото
        passport_request = asyncio.run(get_passport_request(session['user_id']))
        if not passport_request or passport_request['id'] != request_id:
            abort(403)
        
        photo_data = asyncio.run(get_passport_photo(request_id))
        if not photo_data:
            abort(404)
            
        return send_file(
            BytesIO(photo_data),
            mimetype='image/jpeg',
            as_attachment=False
        )
    except Exception as e:
        logging.error(f"Error getting passport photo: {str(e)}")
        abort(500)

@app.route('/check-account-status')
@login_required
def check_account_status():
    user = asyncio.run(get_user_by_id(session['user_id']))
    return jsonify({
        'status': user['account_status']
    })

@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    # Получаем все уведомления пользователя
    notifications_list = asyncio.run(get_user_notifications(user_id))
    
    # Помечаем уведомления как прочитанные
    asyncio.run(mark_notifications_as_read(user_id))
    
    # Получаем данные пользователя и счетчик непрочитанных уведомлений
    current_user = asyncio.run(get_user_by_id(user_id))
    unread_count = asyncio.run(get_unread_notifications_count(user_id))
    has_unread = unread_count > 0
    
    return render_template(
        'notifications.html',
        current_user=current_user,
        notifications=notifications_list,
        unread_count=unread_count,  # Добавляем счетчик
        has_unread_notifications=has_unread  # Добавляем флаг
    )

@app.route('/api/notifications/count')
@login_required
def unread_notifications_count():
    user_id = session['user_id']
    count = asyncio.run(get_unread_notifications_count(user_id))
    return jsonify({'count': count})


@app.route('/articles')
def all_articles():
    try:
        # Получаем текущего пользователя и данные для шапки
        user = None
        has_unread = False
        unread_count = 0
        
        if 'user_id' in session:
            user = asyncio.run(get_user_by_id(session['user_id']))
            has_unread = asyncio.run(get_unread_notifications_count(session['user_id'])) > 0
            unread_count = asyncio.run(get_unread_notifications_count(session['user_id']))
        
        # Обрабатываем параметры запроса
        selected_category = request.args.get('category', 'all')
        search_query = request.args.get('search', '').strip()
        
        # Получаем все статьи из базы данных
        all_articles = asyncio.run(get_all_articles_for_display())
        
        # Фильтрация статей
        filtered_articles = []
        for article in all_articles:
            # Проверяем соответствие категории (если выбрана не "все")
            category_match = (selected_category == 'all') or (article['category'] == selected_category)
            # Проверяем соответствие поисковому запросу (если есть)
            search_match = not search_query or (
                search_query.lower() in article['topic_name'].lower() or
                search_query.lower() in article['topic_text'].lower()
            )
            
            if category_match and search_match:
                # Удаляем бинарные данные для JSON сериализации
                safe_article = {k: v for k, v in article.items() if k != 'preview_image'}
                safe_article['has_image'] = bool(article.get('preview_image'))
                filtered_articles.append(safe_article)
        
        # Определяем заголовок для отображения
        if search_query:
            category_title = f'Результаты поиска: "{search_query}"'
        else:
            category_title = EXPERTISE_AREAS.get(selected_category, 'Все категории')
        
        return render_template(
            'articles.html',
            current_user=user,
            articles=filtered_articles,
            active_category=selected_category,
            search_query=search_query,
            EXPERTISE_AREAS=EXPERTISE_AREAS,
            has_unread_notifications=has_unread,
            unread_count=unread_count,
            category_title=category_title
        )
    except Exception as e:
        logging.error(f"Ошибка в маршруте /articles: {str(e)}", exc_info=True)
        abort(500)

@app.route('/api/articles')
def api_articles():
    category = request.args.get('category', 'marketing')
    all_articles = asyncio.run(get_all_articles_for_display())
    filtered = [a for a in all_articles if a['category'] == category]

    return jsonify({
        'category_name': EXPERTISE_AREAS.get(category, 'Категория'),
        'articles': [
            {
                'id': a['id'],
                'topic_name': a['topic_name'],
                'topic_name_en': a['topic_name_en'],
                'has_image': bool(a['preview_image'])
            } for a in filtered
        ]
    })

@app.route('/api/articles/search')
def search_articles_api():
    query = request.args.get('q', '').strip()
    print(f"Search query: '{query}'")  # Логирование
    
    if not query:
        return jsonify({'articles': []})
    
    all_articles = asyncio.run(get_all_articles_for_display())
    print(f"Total articles: {len(all_articles)}")  # Логирование
    
    filtered = [a for a in all_articles if query.lower() in a['topic_name'].lower()]
    print(f"Found articles: {len(filtered)}")  # Логирование
    
    result = {
        'articles': [
            {
                'id': a['id'],
                'topic_name': a['topic_name'],
                'topic_name_en': a.get('topic_name_en', ''),
                'has_image': bool(a.get('preview_image'))
            } for a in filtered
        ]
    }
    
    print(f"Returning: {result}")  # Логирование
    return jsonify(result)

@app.route('/friends')
@login_required
def friends_page():
    user_id = session['user_id']
    print(f"\n=== DEBUG: Getting friends for user {user_id} ===")  # Debug
    
    friends = asyncio.run(get_friends(user_id))
    print(f"Friends: {friends}")  # Debug
    
    pending_requests = asyncio.run(get_pending_requests(user_id))
    print(f"Pending requests: {pending_requests}")  # Debug
    
    current_user = asyncio.run(get_user_by_id(user_id))
    has_unread = asyncio.run(get_unread_notifications_count(user_id)) > 0
    unread_count = asyncio.run(get_unread_notifications_count(user_id))
    
    return render_template(
        'friends.html',
        current_user=current_user,
        friends=friends,
        pending_requests=pending_requests,  # Исправлено с friend_requests на pending_requests
        has_unread_notifications=has_unread,
        unread_count=unread_count
    )

@app.route('/api/friends/send-request', methods=['POST'])
@login_required
def handle_send_friend_request():
    """Обрабатывает отправку заявки в друзья"""
    try:
        data = request.get_json()
        friend_id = int(data.get('friend_id'))
        
        if not friend_id:
            return jsonify({'success': False, 'message': 'Не указан ID пользователя'}), 400
            
        success = asyncio.run(send_friend_request(session['user_id'], friend_id))
        
        if success:
            # Создаем уведомление для получателя
            current_user = asyncio.run(get_user_by_id(session['user_id']))
            notification_message = (
                f"{current_user['user_name']} {current_user['user_surname']} "
                f"отправил(а) вам заявку в друзья"
            )
            asyncio.run(create_notification(
                friend_id,
                notification_message,
                'friend_request',
                session['user_id']
            ))
            
            return jsonify({
                'success': True, 
                'message': 'Заявка отправлена',
                'refresh': True
            })
        return jsonify({
            'success': False, 
            'message': 'Не удалось отправить заявку (возможно, она уже существует)'
        }), 400
        
    except Exception as e:
        logging.error(f"Error sending friend request: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500

@app.route('/api/friends/respond', methods=['POST'])
@login_required
def handle_respond_to_friend_request():
    """Обрабатывает ответ на заявку в друзья"""
    try:
        data = request.get_json()
        friend_id = int(data.get('friend_id'))
        accept = bool(data.get('accept', False))
        
        if not friend_id:
            return jsonify({'success': False, 'message': 'Не указан ID пользователя'}), 400
            
        success = asyncio.run(respond_to_friend_request(
            session['user_id'], 
            friend_id, 
            accept
        ))
        
        if success:
            # Создаем уведомление
            current_user = asyncio.run(get_user_by_id(session['user_id']))
            target_user = asyncio.run(get_user_by_id(friend_id))
            
            if accept:
                # Уведомление для того, кто отправил заявку
                notification_message = (
                    f"{current_user['user_name']} {current_user['user_surname']} "
                    f"принял(а) вашу заявку в друзья"
                )
                asyncio.run(create_notification(
                    friend_id,
                    notification_message,
                    'friend_request_accepted',
                    session['user_id']
                ))
            else:
                # Уведомление об отклонении
                notification_message = (
                    f"{current_user['user_name']} {current_user['user_surname']} "
                    f"отклонил(а) вашу заявку в друзья"
                )
                asyncio.run(create_notification(
                    friend_id,
                    notification_message,
                    'friend_request_declined',
                    session['user_id']
                ))
            
            return jsonify({
                'success': True, 
                'message': 'Заявка ' + ('принята' if accept else 'отклонена'),
                'refresh': True
            })
        return jsonify({
            'success': False, 
            'message': 'Ошибка при обработке заявки'
        }), 500
        
    except Exception as e:
        logging.error(f"Error responding to friend request: {str(e)}")
        return jsonify({
            'success': False, 
            'message': 'Внутренняя ошибка сервера'
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