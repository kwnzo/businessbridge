from flask import Flask, render_template, url_for, request,jsonify, json, after_this_request, send_file
from utils.db import init_db
import base64
import io
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello'

@app.route('/index')
def index(name = None):
    return render_template('index.html', person = name)

@app.route('/about')
def about():
    return 'About'

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/profile')
def profile():
    return render_template('registration.html')


async def main():
    start = None
    try: 
        start = await init_db()

    except Exception as e:
        print(f'Exception: {e}')

    finally:
        if start == True:
            app.run(debug=True)

        else:
            print(f"start isn't True")

asyncio.run(main())
