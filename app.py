from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os
import json
from google.cloud import translate_v2 as translate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



OPENWEATHERMAP_API_KEY = 'bf8a757f0ee33aafb55adbcda8b8944e'
COINMARKETCAP_API_KEY = 'af9f6918-15fb-4c16-a4d0-52f2bdd11fb5'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    tags = db.Column(db.String(200))

with app.app_context():
    db.create_all()

@app.route("/")
def main():
    return render_template('main.html')

@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']
        # Получаем дату из формы, если она указана
        date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M') if request.form['date'] else datetime.utcnow()
        
        news = News(title=title, description=description, tags=tags, date=date)
        db.session.add(news)
        db.session.commit()
        return redirect('/news')
    
    news_list = News.query.order_by(News.date.desc()).all()
    return render_template('news.html', news_list=news_list)

@app.route("/news/<int:id>", methods=['GET', 'POST'])
def news_detail(id):
    news = News.query.get_or_404(id)
    
    if request.method == 'GET':
        return render_template('news_detail.html', news=news)
        
    elif request.method == 'POST':
        if request.form.get('_method') == 'PUT':
            news.title = request.form.get('title', news.title)
            news.description = request.form.get('description', news.description)
            news.tags = request.form.get('tags', news.tags)
            date = request.form.get('date')
            if date:
                news.date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
            db.session.commit()
            return redirect(url_for('news_detail', id=id))
            
        elif request.form.get('_method') == 'DELETE':
            db.session.delete(news)
            db.session.commit()
            return redirect(url_for('news'))
            
    return redirect(url_for('news'))

@app.route("/about_us")
def about_us():
    return render_template('about_us.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return redirect(url_for('user_profile', user_id=user.id))
        else:
            return "Введены неверные данные"
    return render_template('login.html')

@app.route("/user/<int:user_id>")
def user_profile(user_id):
    user = User.query.get(user_id)
    return render_template('user_profile.html', user=user)

@app.route("/user/<int:user_id>/edit", methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.password = request.form['password']
        db.session.commit()
        return redirect(url_for('user_profile', user_id=user.id))
    return render_template('edit_user.html', user=user)

@app.route("/array_operations", methods=['GET', 'POST'])
def array_operations():
    return render_template('array_operations.html')

@app.route("/quiz", methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        # Получаем ответы с формы
        answers = {
            'q1': request.form.get('q1'),
            'q2': request.form.get('q2'),
            'q3': request.form.get('q3'),
            'q4': request.form.get('q4'),
            'q5': request.form.get('q5'),
            'q6': request.form.get('q6'),
            'q7': request.form.get('q7')
        }
        
        # Логика оценки результатов
        score = sum(1 for answer in answers.values() if answer == 'correct')
        
        if score >= 5:
            result = "Вы отлично справились!"
        else:
            result = "Попробуйте снова!"

        return render_template('quiz_result.html', score=score, result=result)
    
    return render_template('quiz.html')

@app.route("/js_task")
def js_tasks():
    return render_template('js_task.html')

# Обработка ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/jokes_page")
def jokes_page():
    return render_template('joke.html')


@app.route("/api/joke")
def get_translated_joke():
    # Получение шутки из внешнего API
    joke_api_url = "https://official-joke-api.appspot.com/random_joke"
    response = requests.get(joke_api_url)
    
    if response.status_code != 200:
        return jsonify({"joke": "Не удалось получить шутку, попробуйте позже."})
    
    joke_data = response.json()
    original_joke = f"{joke_data['setup']} - {joke_data['punchline']}"
    
    # Перевод шутки с использованием DeepL API
    deepl_api_url = "https://api-free.deepl.com/v2/translate"
    params = {
        "auth_key": "38eec07f-176a-49ea-bbb3-e1c5d80cc9be:fx",
        "text": original_joke,
        "target_lang": "RU"
    }
    
    translation_response = requests.post(deepl_api_url, data=params)
    
    if translation_response.status_code == 200:
        translated_joke = translation_response.json()["translations"][0]["text"]
    else:
        translated_joke = f"Ошибка перевода: {translation_response.status_code} {translation_response.reason}"
    
    return Response(json.dumps({"joke": translated_joke}, ensure_ascii=False), content_type='application/json')


@app.route('/weather')
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({'error': 'Параметр "city" обязателен.'}), 400

    url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ru'

    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return jsonify({'error': data.get('message', 'Ошибка при получении данных.')}), response.status_code

        weather_info = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description']
        }

        return jsonify(weather_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cities')
def cities_weather():
    search_city = request.args.get('search_city')
    
    if search_city:
        # Перенаправляем на страницу подробной информации о городе
        return redirect(url_for('city_detail', city_name=search_city))
    
    # Список городов по умолчанию
    default_cities = ['Москва', 'Лондон', 'Нью-Йорк', 'Токио', 'Астана']
    
    weather_data = []
    
    for city in default_cities:
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ru'
        try:
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                weather = {
                    'city': data['name'],
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description']
                }
                weather_data.append(weather)
            else:
                weather_data.append({'city': city, 'error': data.get('message', 'Ошибка')})
        except Exception as e:
            weather_data.append({'city': city, 'error': str(e)})
    
    return render_template('cities.html', weather_data=weather_data)



@app.route('/crypto')
def get_crypto():
    currency = request.args.get('currency')
    if not currency:
        return jsonify({'error': 'Параметр "currency" обязателен.'}), 400

    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    parameters = {
        'symbol': currency.upper(),
        'convert': 'USD'
    }

    try:
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if response.status_code != 200:
            return jsonify({'error': data.get('status', {}).get('error_message', 'Ошибка при получении данных.')}), response.status_code

        if 'data' not in data or currency.upper() not in data['data']:
            return jsonify({'error': 'Криптовалюта не найдена.'}), 404

        crypto_info = data['data'][currency.upper()]
        price = crypto_info['quote']['USD']['price']

        return jsonify({
            'currency': crypto_info['name'],
            'price_usd': price
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/cryptos', methods=['GET', 'POST'])
def cryptos_prices():
    if request.method == 'POST':
    
        search_currency = request.form.get('search_currency')
        if search_currency:
            return redirect(url_for('get_crypto_page', currency=search_currency))
    

    symbols = ['BTC', 'ETH', 'XRP', 'LTC', 'BCH']
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    parameters = {
        'symbol': ','.join(symbols),
        'convert': 'USD'
    }
    crypto_data = []

    try:
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if response.status_code != 200:
            return jsonify({'error': data.get('status', {}).get('error_message', 'Ошибка при получении данных.')}), response.status_code

        for symbol in symbols:
            if symbol in data['data']:
                crypto = data['data'][symbol]
                crypto_info = {
                    'symbol': crypto['symbol'],
                    'name': crypto['name'],
                    'price_usd': round(crypto['quote']['USD']['price'], 2)
                }
                crypto_data.append(crypto_info)
            else:
                crypto_data.append({'symbol': symbol, 'error': 'Не найдено'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return render_template('cryptos.html', crypto_data=crypto_data)


@app.route('/cities/<city_name>')
def city_detail(city_name):
    url = f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang=ru'
    
    try:
        response = requests.get(url)
        data = response.json()

        # if response.status_code != 200:
        #     return render_template('city_error.html', error=data.get('message', 'Ошибка при получении данных.')), response.status_code

        weather_info = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }

        return render_template('cities_detail.html', weather=weather_info)
    except Exception as e:
        return render_template('city_error.html', error=str(e)), 500



@app.route('/crypto_page/<currency>')
def get_crypto_page(currency):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
    }
    parameters = {
        'symbol': currency.upper(),
        'convert': 'USD'
    }

    try:
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()

        if response.status_code != 200:
            return render_template('crypto_error.html', error=data.get('status', {}).get('error_message', 'Ошибка при получении данных.')), response.status_code

        if 'data' not in data or currency.upper() not in data['data']:
            return render_template('crypto_error.html', error='Криптовалюта не найдена.'), 404

        crypto_info = data['data'][currency.upper()]
        price = round(crypto_info['quote']['USD']['price'], 2)

        return render_template('crypto_detail.html', currency=crypto_info['name'], price_usd=price)
    except Exception as e:
        return render_template('crypto_error.html', error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)