from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from functools import wraps
from flask_wtf.csrf import generate_csrf, validate_csrf
from wtforms import ValidationError
from utils.db import (
    get_user_by_id,
    get_users_count,
    get_articles_count,
    get_experts_count,
    get_all_users,
    update_user_role,
    delete_user,
    search_articles,
    delete_article,
    get_all_articles,
    reject_expert_request_db,
    approve_expert_request_db,
    get_expert_requests,
    get_expert_requests_count,
    get_expert_request_details,
    get_publics_for_approve, get_articles_for_review, 
    get_articles_for_review_count, update_article_status, 
    reject_article_db, get_filtered_articles_count, 
    get_filtered_users_count, search_users, get_filtered_articles
)
import asyncio
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = asyncio.run(get_user_by_id(session['user_id']))
        if not user or user.get('user_role') != 'admin':
            return redirect(url_for('account'))
            
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    try:
        users_count = asyncio.run(get_users_count())
        articles_count = asyncio.run(get_articles_count())
        experts_count = asyncio.run(get_experts_count())
        
        # Убедимся, что передаем токен как строку, а не функцию
        return render_template('admin/dashboard.html',
                            users_count=users_count,
                            articles_count=articles_count,
                            experts_count=experts_count,
                            csrf_token=generate_csrf())  # generate_csrf без вызова как функции
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}", exc_info=True)
        return render_template('admin/error.html', message="Ошибка загрузки данных"), 500

@admin_bp.route('/users')
@admin_required
def users_management():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Получаем параметры фильтрации
        filters = {
            'q': request.args.get('q', '').strip(),
            'role': request.args.get('role', ''),
            'status': request.args.get('status', ''),
            'date_from': request.args.get('date_from', ''),
            'date_to': request.args.get('date_to', ''),
            'sort': request.args.get('sort', 'newest')
        }
        
        # Получаем пользователей с учетом фильтров
        users = asyncio.run(search_users(
            query=filters['q'],
            role=filters['role'],
            status=filters['status'],
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            sort=filters['sort'],
            limit=per_page,
            offset=offset
        ))
        
        # Получаем общее количество с учетом фильтров
        total_users = asyncio.run(get_filtered_users_count(
            query=filters['q'],
            role=filters['role'],
            status=filters['status'],
            date_from=filters['date_from'],
            date_to=filters['date_to']
        ))
        
        total_pages = (total_users + per_page - 1) // per_page if total_users else 1
        
        return render_template('admin/users.html',
                            users=users,
                            current_page=page,
                            total_pages=total_pages,
                            csrf_token_value=generate_csrf(),
                            filters=filters)
    except Exception as e:
        logger.error(f"Users management error: {str(e)}", exc_info=True)
        return render_template('admin/error.html', message="Ошибка загрузки пользователей"), 500

@admin_bp.route('/users/<int:user_id>/update_role', methods=['POST'])
@admin_required
def update_user_role_handler(user_id):  # Изменили имя функции
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        new_role = request.json.get('role')
        if new_role not in ['user', 'expert', 'admin']:
            return jsonify({'success': False, 'message': 'Неверная роль'}), 400
        
        success = asyncio.run(update_user_role(user_id, new_role))  # Используем импортированную функцию
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Ошибка обновления'}), 400
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности. Обновите страницу'}), 403
    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500
    
    
@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user_route(user_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for delete user")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        if session.get('user_id') == user_id:
            return jsonify({'success': False, 'message': 'Нельзя удалить себя'}), 400
        
        success = asyncio.run(delete_user(user_id))
        if success:
            logger.info(f"User {user_id} deleted")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Ошибка удаления'}), 400
    except ValidationError as e:
        logger.warning(f"CSRF validation failed for delete user: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности. Обновите страницу'}), 403
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500
    

@admin_bp.route('/articles')
@admin_required
def articles_management():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Получаем параметры фильтрации
        filters = {
            'q': request.args.get('q', '').strip(),
            'status': request.args.get('status', ''),
            'category': request.args.get('category', ''),
            'date_from': request.args.get('date_from', ''),
            'date_to': request.args.get('date_to', ''),
            'sort': request.args.get('sort', 'newest')
        }
        
        # Получаем статьи с учетом фильтров
        articles = asyncio.run(get_filtered_articles(
            query=filters['q'],
            status=filters['status'],
            category=filters['category'],
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            sort=filters['sort'],
            limit=per_page,
            offset=offset
        ))
        
        # Получаем общее количество с учетом фильтров
        total_articles = asyncio.run(get_filtered_articles_count(
            query=filters['q'],
            status=filters['status'],
            category=filters['category'],
            date_from=filters['date_from'],
            date_to=filters['date_to']
        ))
        
        total_pages = (total_articles + per_page - 1) // per_page if total_articles else 1
        
        return render_template('admin/articles.html',
                            articles=articles,
                            current_page=page,
                            total_pages=total_pages,
                            csrf_token_value=generate_csrf(),
                            search_query=filters['q'],
                            filters=filters)
    except Exception as e:
        logger.error(f"Articles management error: {str(e)}", exc_info=True)
        return render_template('admin/error.html', message="Ошибка загрузки статей"), 500

@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@admin_required
def delete_article_route(article_id):
    try:
        # Проверка CSRF токена
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for delete article")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)  # Исправлено здесь
        
        # Удаление статьи
        success = asyncio.run(delete_article(article_id))
        if success:
            logger.info(f"Article {article_id} deleted successfully")
            return jsonify({'success': True})
        
        logger.warning(f"Article {article_id} not found or not deleted")
        return jsonify({'success': False, 'message': 'Статья не найдена'}), 404
        
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности'}), 403
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка сервера'}), 500
    
@admin_bp.route('/requests')
@admin_required
def requests_management():
    if request.method == 'GET':
        publics = asyncio.run(get_publics_for_approve())
        
        return render_template('admin/requests.html', publics = publics, csrf = generate_csrf())

@admin_bp.route('/requests/expert')
@admin_required
def expert_requests():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Получаем параметры фильтрации
        filters = {
            'q': request.args.get('q', '').strip(),
            'date_from': request.args.get('date_from', ''),
            'date_to': request.args.get('date_to', ''),
            'sort': request.args.get('sort', 'newest')
        }
        
        # Получаем заявки с учетом фильтров
        requests = asyncio.run(get_expert_requests(
            search=filters['q'],
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            sort=filters['sort'],
            limit=per_page,
            offset=offset
        ))
        
        # Получаем общее количество с учетом фильтров
        total_requests = asyncio.run(get_expert_requests_count(
            search=filters['q'],
            date_from=filters['date_from'],
            date_to=filters['date_to']
        ))
        
        total_pages = (total_requests + per_page - 1) // per_page if total_requests else 1
        
        return render_template('admin/expert_requests.html',
                            requests=requests,
                            current_page=page,
                            total_pages=total_pages,
                            csrf_token_value=generate_csrf(),
                            filters=filters)
    except Exception as e:
        logger.error(f"Expert requests error: {str(e)}", exc_info=True)
        return render_template('admin/error.html', message="Ошибка загрузки заявок"), 500
        
@admin_bp.route('/requests/expert/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_expert_request(request_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for approve expert request")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        # Одобряем заявку и обновляем роль пользователя
        success = asyncio.run(approve_expert_request_db(request_id))
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Ошибка одобрения заявки'}), 400
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности'}), 403
    except Exception as e:
        logger.error(f"Error approving expert request: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500

@admin_bp.route('/requests/expert/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject_expert_request(request_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for reject expert request")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        rejection_reason = request.json.get('reason', '')
        if not rejection_reason:
            return jsonify({'success': False, 'message': 'Укажите причину отказа'}), 400
        
        # Отклоняем заявку с сохранением причины в user_data
        success = asyncio.run(reject_expert_request_db(request_id, rejection_reason))
        if success:
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Ошибка отклонения заявки'}), 400
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности'}), 403
    except Exception as e:
        logger.error(f"Error rejecting expert request: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500
def decline():
    pass
    
@admin_bp.route('/requests/expert/<int:request_id>/details')
@admin_required
def expert_request_details(request_id):
    try:
        request_data = asyncio.run(get_expert_request_details(request_id))
        if not request_data:
            return jsonify({'success': False, 'message': 'Заявка не найдена'}), 404
            
        return jsonify({
            'success': True,
            'request': {
                'company': request_data['company'],
                'position': request_data['position'],
                'expertise': request_data['expertise'],
                'other_expertise': request_data['other_expertise'],
                'experience': request_data['experience'],
                'description': request_data['description']
            }
        })
    except Exception as e:
        logger.error(f"Error getting expert request details: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500
    

@admin_bp.route('/requests/articles')
@admin_required
def article_requests():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page
        
        # Получаем параметры фильтрации
        filters = {
            'q': request.args.get('q', '').strip(),
            'date_from': request.args.get('date_from', ''),
            'date_to': request.args.get('date_to', ''),
            'sort': request.args.get('sort', 'newest')
        }
        
        # Получаем статьи с учетом фильтров
        articles = asyncio.run(get_articles_for_review(
            query=filters['q'],
            date_from=filters['date_from'],
            date_to=filters['date_to'],
            sort=filters['sort'],
            limit=per_page,
            offset=offset
        ))
        
        # Получаем общее количество с учетом фильтров
        total_articles = asyncio.run(get_articles_for_review_count(
            query=filters['q'],
            date_from=filters['date_from'],
            date_to=filters['date_to']
        ))
        
        total_pages = (total_articles + per_page - 1) // per_page if total_articles else 1
        
        return render_template('admin/article_requests.html',
                            articles=articles,
                            current_page=page,
                            total_pages=total_pages,
                            csrf_token_value=generate_csrf(),
                            filters=filters)
    except Exception as e:
        logger.error(f"Article requests error: {str(e)}", exc_info=True)
        return render_template('admin/error.html', message="Ошибка загрузки статей"), 500
    
@admin_bp.route('/articles/<int:article_id>/approve', methods=['POST'])
@admin_required
def approve_article(article_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for approve article")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        success = asyncio.run(update_article_status(article_id, 'accept'))
        if success:
            logger.info(f"Article {article_id} approved successfully")
            return jsonify({'success': True})
        
        logger.warning(f"Article {article_id} not found or not updated")
        return jsonify({'success': False, 'message': 'Статья не найдена'}), 404
        
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности'}), 403
    except Exception as e:
        logger.error(f"Error approving article: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500

@admin_bp.route('/articles/<int:article_id>/reject', methods=['POST'])
@admin_required
def reject_article(article_id):
    try:
        csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
        if not csrf_token:
            logger.warning("CSRF token is missing for reject article")
            return jsonify({'success': False, 'message': 'CSRF token is missing'}), 400
            
        validate_csrf(csrf_token)
        
        rejection_reason = request.json.get('reason', '')
        if not rejection_reason:
            return jsonify({'success': False, 'message': 'Укажите причину отказа'}), 400
        
        success = asyncio.run(reject_article_db(article_id, rejection_reason))
        if success:
            logger.info(f"Article {article_id} rejected with reason")
            return jsonify({'success': True})
        
        logger.warning(f"Article {article_id} not found or not rejected")
        return jsonify({'success': False, 'message': 'Статья не найдена'}), 404
        
    except ValidationError as e:
        logger.warning(f"CSRF validation failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Ошибка безопасности'}), 403
    except Exception as e:
        logger.error(f"Error rejecting article: {str(e)}")
        return jsonify({'success': False, 'message': 'Внутренняя ошибка сервера'}), 500