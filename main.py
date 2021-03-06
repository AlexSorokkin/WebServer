import sqlite3  # import всего нужного
from flask import Flask, render_template, redirect, session, request, jsonify, make_response, send_from_directory
from wtforms import PasswordField, BooleanField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_restful import reqparse, abort, Api, Resource
import random

app = Flask(__name__)  # создание приложения
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('user_id', required=True, type=int)
parser2 = reqparse.RequestParser()
parser2.add_argument('user_name', required=True)
parser2.add_argument('password_hash', required=True)


def bySlovo(slovo):  # сортировка уровней
    return slovo[1]


def abort_if_news_not_found(news_id):  # error
    if not NewsModel(Artem.get_connection()).get(news_id):
        abort(404, message="News {} not found".format(news_id))


def abort_if_users_not_found(user_id):  # error
    if not UsersModel(Artem.get_connection()).get(user_id):
        abort(404, message="Users {} not found".format(user_id))


class AddNewsForm(FlaskForm):  # form добавления новости
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):  # form входа
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegForm(FlaskForm):  # form регистрации
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегестрироваться')


class DB:  # база данных
    def __init__(self):
        conn = sqlite3.connect('server.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class NewsModel:  # class постов в базе данных
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             level_img VARCHAR(100),
                             level1 TEXT,
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, level_img, level1, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO posts 
                          (title, content, level_img, level1, user_id) 
                          VALUES (?,?,?,?,?)''', (title, content, level_img, level1, str(user_id)))
        cursor.close()
        self.connection.commit()

    def update(self, id, title, content):
        cursor = self.connection.cursor()
        cursor.execute('''UPDATE posts SET 
                                   title = ?, content = ? 
                                   WHERE id = ?''', (title, content, id))
        cursor.close()
        self.connection.commit()

    def get(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ?", ([str(news_id)]))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None, set_up=None):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts")
        rows = cursor.fetchall()
        if set_up:
            rows = sorted(rows, key=bySlovo)
        return rows

    def delete(self, news_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM posts WHERE id = ?''', ([str(news_id)]))
        cursor.close()
        self.connection.commit()


class UsersModel:  # class юзеров в базе данных
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128)
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users 
                          (user_name, password_hash) 
                          VALUES (?,?)''', (user_name, password_hash))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", [str(user_id)])
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def double_exist(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ?",
                       [user_name])
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)

    def delete(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM users WHERE `id`=?",
                       [user_id])
        cursor.close()
        self.connection.commit()


@app.route('/login', methods=['GET', 'POST'])  # страница входа
def login():
    if request.method == 'POST':
        user_name = request.form['email']
        password = request.form['pass']
        user_model.init_table()
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        return redirect("/index")
    return render_template('login.html')


@app.route('/logout')  # страница выхода
def logout():
    session.pop('username',0)
    session.pop('user_id',0)
    return redirect('/index')


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])  # основная страница
def index():
    return render_template('index.html')


@app.route('/add_post', methods=['GET', 'POST'])  # страница добавления лвла
def add_news():
    if 'username' not in session:
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['map']
        content = request.form['about']
        level_img = request.form['class']
        if level_img == 'Летняя':
            level_img = '2'
        elif level_img == 'Зимняя':
            level_img = '9'
        elif level_img == 'Джунгли':
            level_img = '7'
        elif level_img == 'Пустыня':
            level_img = '6'
        elif level_img == 'Ад':
            level_img = '11'
        level1 = request.files['file']
        level1 = level1.read()
        news.insert(title, content, level_img, level1, session['user_id'])
        a = news.get_all()
        a = a[-1][0]
        f = open('static/levels/{}.txt'.format(a), 'wb')
        f.write(level1)
        f.close()
        return redirect("/index")
    return render_template('add_post.html',
                           username=session['username'])


@app.route('/delete_level/<int:news_id>', methods=['GET'])  # страница удаления лвла
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/index')
    nm = NewsModel(Artem.get_connection())
    nm.delete(news_id)
    return redirect("/adminka_for_me_only_jester")


@app.route('/registr', methods=['GET', 'POST'])  # страница регистрации
def reg():
    if request.method == 'POST':
        user_name = request.form['email']
        password = request.form['pass']
        double_exist = user_model.double_exist(user_name)
        print(double_exist)
        if double_exist != (False,):
            return redirect('/registr')
        user_model.insert(user_name, password)
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        return redirect("/index")
    return render_template('registr.html')


@app.route('/adminka_for_me_only_jester', methods=['GET', 'POST'])  # страница админки
def adm():
    if 'username' not in session:
        return redirect('/login')
    if session['username'] != 'alexsorokkin@gmail.com':
        return redirect('/index')
    news2 = news.get_all(session, tag)
    return render_template('admin.html', news=news2)


@app.route('/adminka_for_me_only_jester/<int:id>', methods=['GET', 'POST'])  # страница удаления лвла
def adm1(id):
    if 'username' not in session:
        return redirect('/login')
    if session['username'] != 'alexsorokkin@gmail.com':
        return redirect('/index')
    user_model.delete(int(id))
    return redirect('/adminka_for_me_only_jester')


@app.route('/tag_on')  # страница изменеия сортировки
def tag_on():
    global tag
    tag = 1
    return redirect('/index')


@app.route('/tag_off')  # страница изменеия сортировки
def tag_off():
    global tag
    tag = None
    return redirect('/index')


@app.route('/levels_get')
def get_post():
    new = news.get_all()
    length = len(new)
    ran = random.randint(0, length-1)
    new = new[ran]
    f = open('static/levels/{}.txt'.format(new[0]), 'r')
    stroka = f.read()
    stroka = str(new[3])+stroka
    return jsonify({'ok': stroka})


@app.route('/levels',  methods=['GET', 'POST'])  # страница всех лвлов
def get_news():
    news2 = news.get_all(session, tag)
    return render_template('levels.html', news=news2)


@app.route('/levels/<int:news_id>',  methods=['GET', 'DELETE', "POST"])  # страница определённого лвла
def get_one_news(news_id):
    if request.method == 'POST':
        news.delete(news_id)
        return redirect('/news')
    if request.method == 'GET':
        new = news.get(news_id)
        author = user_model.get(new[5])
        author = author[1]
        return render_template('one_level.html', item=new, author=author)


@app.errorhandler(404)  # страница ошибки 404
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/news_put/<int:news_id>', methods=['PUT'])
def put_news(news_id):
    if not news.get(news_id):
        return jsonify({'error': 'Not found'})
    a = news.get(news_id)
    title = a[1]
    new = a[2]
    if 'title' in request.json:
        title = request.json['title']
    if 'content' in request.json:
        new = request.json['content']
    news.update(news_id, title, new)
    return jsonify({'success': 'OK'})


@app.route('/users/<int:news_id>',  methods=['GET', 'DELETE'])
def get_one_users(news_id):
    if request.method == 'GET':
        new = user_model.get(news_id)
        return jsonify({'users': new})
    else:
        new = user_model.get(news_id)
        return jsonify({'users': new})


@app.route('/users',  methods=['GET', 'POST'])
def get_users():
    if request.method == 'POST':
        user_model.insert(request.json['user_name'], request.json['password_hash'])
        return redirect('/users')
    users2 = user_model.get_all()
    users = []
    for i in users2:
        users.append(i[1])
    return render_template('index.html', users=users)


if __name__ == '__main__':
    Artem = DB()
    user_model = UsersModel(Artem.get_connection())
    user_model.init_table()
    news = NewsModel(Artem.get_connection())
    news.init_table()
    tag = None
    app.run(port=8800, host='127.0.0.1')
