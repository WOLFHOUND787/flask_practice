from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

@app.route("/news", methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags')
        
        news = News(title=title, description=description, tags=tags)
        db.session.add(news)
        db.session.commit()
        return redirect(url_for('news'))
        
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

# Обработка ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)