import sqlite3
from flask import Flask, render_template, redirect, session, request, jsonify, make_response
from wtforms import PasswordField, BooleanField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('user_id', required=True, type=int)
parser2 = reqparse.RequestParser()
parser2.add_argument('user_name', required=True)
parser2.add_argument('password_hash', required=True)


def bySlovo(slovo):
    return slovo[1]


def abort_if_news_not_found(news_id):
    if not NewsModel(Artem.get_connection()).get(news_id):
        abort(404, message="News {} not found".format(news_id))


def abort_if_users_not_found(user_id):
    if not UsersModel(Artem.get_connection()).get(user_id):
        abort(404, message="Users {} not found".format(user_id))


class AddNewsForm(FlaskForm):
    title = StringField('Заголовок новости', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегестрироваться')


class DB:
    def __init__(self):
        conn = sqlite3.connect('server.db', check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class NewsModel:
    def __init__(self, connection):
        self.connection = connection

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             title VARCHAR(100),
                             content VARCHAR(1000),
                             level1 TEXT,
                             user_id INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, content, level1, user_id):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO posts 
                          (title, content, level1, user_id) 
                          VALUES (?,?,?,?)''', (title, content, level1, str(user_id)))
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


class UsersModel:
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


@app.route('/login', methods=['GET', 'POST'])
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


@app.route('/logout')
def logout():
    session.pop('username',0)
    session.pop('user_id',0)
    return redirect('/index')


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/add_news', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session:
        return redirect('/login')
    form = AddNewsForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        news.insert(title, content, session['user_id'])
        return redirect("/index")
    return render_template('add_news.html', title='Добавление новости',
                           form=form, username=session['username'])


@app.route('/delete_news/<int:news_id>', methods=['GET'])
def delete_news(news_id):
    if 'username' not in session:
        return redirect('/index')
    nm = NewsModel(Artem.get_connection())
    nm.delete(news_id)
    return redirect("/index")


@app.route('/registr', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        user_name = request.form['email']
        password = request.form['pass']
        user_model.insert(user_name, password)
        exists = user_model.exists(user_name, password)
        if (exists[0]):
            session['username'] = user_name
            session['user_id'] = exists[1]
        return redirect("/index")
    return render_template('registr.html')


@app.route('/adminka_for_me_only_jester', methods=['GET', 'POST'])
def adm():
    all_users = user_model.get_all()
    all_news = news.get_all()
    print(all_news, all_users)
    string = '''<table>
  <tr>
    <th>Login</th>
    <th>Количество статей</th>
  </tr>'''
    for i in all_users:
        name = i[1]
        num = i[0]
        summa = 0
        for ii in all_news:
            if num == ii[3]:
                summa += 1
        string += '''<tr>
    <td>{}</td>
    <td>{}</td>
  </tr>'''.format(name, summa)
    string += '</table>'
    return '''<!doctype html>
                        <html lang="en">
                          <head>
                            <meta charset="utf-8">
                            <meta name="viewport"
                            content="width=device-width, initial-scale=1, shrink-to-fit=no">
                            <link rel="stylesheet"
                            href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
                            integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm"
                            crossorigin="anonymous">
                            <title>Админка</title>
                          </head>
                          <body>
                            {}
                          </body>
                        </html>'''.format(string)


@app.route('/tag_on')
def tag_on():
    global tag
    tag = 1
    return redirect('/index')


@app.route('/tag_off')
def tag_off():
    global tag
    tag = None
    return redirect('/index')


@app.route('/levels',  methods=['GET', 'POST'])
def get_news():
    news2 = news.get_all(session, tag)
    return render_template('levels.html', news=news2)


@app.route('/news/<int:news_id>',  methods=['GET', 'DELETE', "POST"])
def get_one_news(news_id):
    if request.method == 'POST':
        news.delete(news_id)
        return redirect('/news')
    if request.method == 'GET':
        new = news.get(news_id)
        return jsonify({'news': new})
    else:
        new = news.get(news_id)
        return jsonify({'news': new})


@app.errorhandler(404)
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
