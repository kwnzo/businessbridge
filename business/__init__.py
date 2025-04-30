from flask import Flask, render_template, url_for, request, jsonify, json, after_this_request, send_file, redirect
from utils.db import init_db, insert_into_users
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash
import asyncio
import logging

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
logger = logging.getLogger(__name__)
app = Flask(__name__)


with open('data/config.json', 'r')  as f:
    config = json.load(f)

app.secret_key = config['secret-key']  # Сначала установите ключ
csrf = CSRFProtect(app)  # Затем инициализируйте CSRF
print(config['secret-key'])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index')
def index(name = None):
    return render_template('index.html', person = name)

@app.route('/reg/confirm', methods = ('GET', 'POST'))
def confirm():
    return render_template('confirm.html')

@app.route('/profile')
def account(name = None):
    return render_template('account.html')

@app.route('/profile/create-publication', methods = ('GET', 'POST'))
def publications():
    return render_template('create-publication.html')

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

            # Сохранение в БД
            loop.run_until_complete(
                insert_into_users(
                    username=username,
                    usersurname=usersurname,
                    userdaddy=userdaddy,
                    phone=phone,
                    email=email,
                    password=generate_password_hash(password)
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

@app.route('/login', methods = ('GET', 'POST'))
def login():
    if request.method == 'POST':
        print(request.method)
    else:
        print(request.method)
        #title_login = request.form['']
    return render_template('login.html')

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