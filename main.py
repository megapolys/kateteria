from flask import Flask, render_template, redirect, request, send_from_directory, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from math import ceil
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql as sql
import configparser
import uuid
import glob
import os
import shutil
import time

from forms import *

config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
app.config['SECRET_KEY'] = config['forms']['csrf_password']

login_manager = LoginManager(app)
login_manager.login_view = '/admin_login'


class User(UserMixin):

    def __init__(self, id):
        self._id = id

    def get_id(self):
        return self._id


def get_cakes():
    with sql.connect(user=config['database']['user'],
                     password=config['database']['password'],
                     host=config['database']['host'],
                     database=config['database']['name']) as con:
        cur = con.cursor()
        cur.execute('SELECT * FROM cakes;')
        raw_cakes = cur.fetchall()
        cooked_cakes = [{'imgs': ['/' + p for p in glob.glob(f'static/img/cakes/{id}/*')],
                         'title': title,
                         'desc': desc,
                         'cost': cost,
                         'uuid': uuid.uuid4(),
                         'id': id} for id, title, desc, cost in raw_cakes]
        n_cake_pages = ceil(len(cooked_cakes) / int(config['view']['cakes_per_page']))
        return cooked_cakes, n_cake_pages


def get_feedback():
    return ['/' + p for p in glob.glob(f'static/img/feedback/*')]


@login_manager.user_loader
def load_user(user_id):
    with sql.connect(user=config['database']['user'],
                     password=config['database']['password'],
                     host=config['database']['host'],
                     database=config['database']['name']) as con:
        cur = con.cursor()
        cur.execute(f'SELECT pass_hash FROM password WHERE pass_hash = "{user_id}";')
        return User(cur.fetchone()[0])


@app.route('/')
@app.route('/index')
def index():
    cakes, n_cake_pages = get_cakes()
    return render_template('index.html',
                           cakes=cakes,
                           active_page=0,
                           feedback=get_feedback(),
                           is_admin=current_user.is_authenticated,
                           title='Главная')


@app.route('/cakes/<int:cake_active_page>')
def cakes(cake_active_page):
    cakes, n_cake_pages = get_cakes()
    return render_template('cakes.html',
                           cakes=cakes,
                           active_page=2,
                           cake_active_page=cake_active_page,
                           n_cake_pages=n_cake_pages,
                           CAKES_PER_PAGE=int(config['view']['cakes_per_page']),
                           is_admin=current_user.is_authenticated,
                           title='Торты')


@app.route('/about')
def about():
    return render_template('about.html',
                           active_page=1,
                           is_admin=current_user.is_authenticated,
                           title='Обо мне')


@app.route('/feedback')
def feedback():
    return render_template('feedback.html',
                           active_page=3,
                           feedback=get_feedback(),
                           is_admin=current_user.is_authenticated,
                           title='Отзывы')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if request.args.get('action', None) == 'logout':
            logout_user()
            return redirect('/index')
        else:
            return redirect('/admin')

    login_form = AdminLoginForm()
    if login_form.validate_on_submit():
        with sql.connect(user=config['database']['user'],
                         password=config['database']['password'],
                         host=config['database']['host'],
                         database=config['database']['name']) as con:
            cur = con.cursor()
            cur.execute('SELECT pass_hash FROM password;')
            pass_hash = cur.fetchone()[0]
            if check_password_hash(pass_hash, login_form.password.data):
                login_user(User(pass_hash), remember=login_form.remember_me.data)
                # logout_user()
                return redirect('/admin')
            else:
                return render_template('/admin_login.html',
                                       form=login_form,
                                       message='Пароль неверный!',
                                       title='Авторизация администратора')
    return render_template('/admin_login.html',
                           form=login_form,
                           title='Авторизация администратора')


@app.route('/admin')
@login_required
def admin():
    cake_form = CakeForm()
    feedback_form = FeedbackForm()
    feedback = get_feedback()
    show_cake = True
    show_feedback = False
    if request.args.get('entity', None) == 'cake':
        if request.args['action'] == 'delete':
            with sql.connect(user=config['database']['user'],
                             password=config['database']['password'],
                             host=config['database']['host'],
                             database=config['database']['name']) as con:
                cur = con.cursor()
                cur.execute('DELETE FROM cakes WHERE id = %s', request.args['id'])
                con.commit()

                if os.path.exists(f'static/img/cakes/{request.args["id"]}'):
                    shutil.rmtree(f'static/img/cakes/{request.args["id"]}')

                show_cake = True
                show_feedback = False
    elif request.args.get('entity', None) == 'feedback':
        os.remove('.' + feedback[int(request.args["id"])])

        show_cake = False
        show_feedback = True

    cakes, n_cake_pages = get_cakes()
    return render_template('admin.html',
                           cakes=cakes,
                           n_cake_pages=n_cake_pages,
                           cake_form=cake_form,
                           feedback_form=feedback_form,
                           feedback=get_feedback(),
                           is_admin=True,
                           show_cake=show_cake,
                           show_feedback=show_feedback,
                           title='Панель администратора')


@app.route('/create_cake', methods=['GET', 'POST'])
@login_required
def create_cake():
    form = CakeForm()
    if form.validate_on_submit():
        with sql.connect(user=config['database']['user'],
                         password=config['database']['password'],
                         host=config['database']['host'],
                         database=config['database']['name']) as con:
            cur = con.cursor()
            cur.execute('INSERT INTO cakes(title, description, cost) VALUES (%s, %s, %s)',
                        (form.title.data, form.description.data, form.cost.data))
            con.commit()

            cur.execute('SELECT max(id) FROM cakes')
            cake_id = cur.fetchone()[0]
            print(cake_id)

            if not os.path.exists(f'static/img/cakes/{cake_id}'):
                os.mkdir(f'static/img/cakes/{cake_id}', mode=0o777)
            if not form.images.data[0].filename:
                shutil.copy('./static/img/cake-default.jpg', f'./static/img/cakes/{cake_id}/cake.jpg')
            else:
                for img in form.images.data:
                    img.save(f'./static/img/cakes/{cake_id}/{secure_filename(img.filename)}')

    return redirect('/admin')


@app.route('/update_cake/<int:cake_id>', methods=['GET', 'POST'])
@login_required
def update_cake(cake_id):
    form = CakeForm()
    if form.validate_on_submit():
        with sql.connect(user=config['database']['user'],
                         password=config['database']['password'],
                         host=config['database']['host'],
                         database=config['database']['name']) as con:
            cur = con.cursor()
            cur.execute(f'UPDATE cakes SET title = %s, description = %s, cost = %s WHERE id = {cake_id};',
                        (form.title.data, form.description.data, form.cost.data))
            con.commit()

            print(form.images.data)
            if len(form.images.data) > 1 or form.images.data[0].filename:
                for root, dirs, files in os.walk(f'static/img/cakes/{cake_id}', topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                for i, img in enumerate(form.images.data):
                    img.save(f'./static/img/cakes/{cake_id}/{i}' + f'_{img.filename.split(".")[-1]}')

    return redirect('/admin')


@app.route('/create_feedback', methods=['GET', 'POST'])
@login_required
def create_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        form.image.data.save(f'./static/img/feedback/{time.time()}.{form.image.data.filename.split(".")[-1]}')

    return redirect('/admin')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
