import configparser
import glob
import os
import shutil
import time
import uuid
from math import ceil

import pymysql as sql
from flask import Flask, render_template, redirect, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from forms import *

config = configparser.ConfigParser()
config.read('config.ini')

application = Flask(__name__)
application.config['SECRET_KEY'] = config['forms']['csrf_password']

login_manager = LoginManager(application)
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
                         'id': id} for id, title, desc, cost in raw_cakes]
        cooked_cakes.reverse()
        n_cake_pages = ceil(len(cooked_cakes) / int(config['view']['cakes_per_page']))
        return cooked_cakes, n_cake_pages


def get_feedback():
    feedback_list = list()
    for el in ['/' + p for p in glob.glob(f'static/img/feedback/*')]:
        feedback_list.append({'imgs': [el]})
    feedback_list.reverse()
    return feedback_list


def get_examples():
    examples_list = list()
    for dir_name in glob.glob(f'static/img/examples/*'):
        id = dir_name[dir_name.rfind('\\') + 1:]
        examples_list.append({'imgs': ['/' + p for p in glob.glob(dir_name + '/*')],
                              'id': id})
    examples_list.reverse()
    return examples_list


def get_max_example_id(examples):
    max_id = 0
    for example in examples:
        max_id = max(max_id, int(example['id']))
    return max_id

@login_manager.user_loader
def load_user(user_id):
    with sql.connect(user=config['database']['user'],
                     password=config['database']['password'],
                     host=config['database']['host'],
                     database=config['database']['name']) as con:
        cur = con.cursor()
        cur.execute(f'SELECT pass_hash FROM password WHERE pass_hash = "{user_id}";')
        return User(cur.fetchone()[0])


@application.route('/')
@application.route('/index')
def index():
    cakes, n_cake_pages = get_cakes()
    return render_template('index.html',
                           cakes=cakes,
                           active_page=0,
                           feedback=get_feedback(),
                           examples=get_examples(),
                           is_admin=current_user.is_authenticated,
                           title='Главная')


@application.route('/cakes/<int:cake_active_page>')
def cakes(cake_active_page):
    cakes, n_cake_pages = get_cakes()
    return render_template('cakes.html',
                           cakes=cakes,
                           active_page=2,
                           cake_active_page=cake_active_page,
                           n_cake_pages=n_cake_pages,
                           CAKES_PER_PAGE=int(config['view']['cakes_per_page']),
                           is_admin=current_user.is_authenticated,
                           title='Начинки')


@application.route('/about')
def about():
    return render_template('about.html',
                           active_page=1,
                           is_admin=current_user.is_authenticated,
                           title='Обо мне')


@application.route('/feedback')
def feedback():
    return render_template('feedback.html',
                           active_page=3,
                           feedback=get_feedback(),
                           is_admin=current_user.is_authenticated,
                           title='Отзывы')

@application.route('/examples')
def examples():
    return render_template('examples.html',
                           active_page=4,
                           examples=get_examples(),
                           is_admin=current_user.is_authenticated,
                           title='Примеры работ')


@application.route('/admin_login', methods=['GET', 'POST'])
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


@application.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    cake_form = CakeForm()
    example_form = ExampleForm()
    feedback_form = FeedbackForm()
    feedback_list = get_feedback()
    examples_list = get_examples()
    active_accordion = 'cake'
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
        elif request.args['action'] == 'create':
            if cake_form.validate_on_submit():
                with sql.connect(user=config['database']['user'],
                                 password=config['database']['password'],
                                 host=config['database']['host'],
                                 database=config['database']['name']) as con:
                    cur = con.cursor()
                    cur.execute('INSERT INTO cakes(title, description, cost) VALUES (%s, %s, %s)',
                                (cake_form.title.data, cake_form.description.data, cake_form.cost.data))
                    con.commit()

                    cur.execute('SELECT max(id) FROM cakes')
                    cake_id = cur.fetchone()[0]

                    if not os.path.exists(f'static/img/cakes/{cake_id}'):
                        os.mkdir(f'static/img/cakes/{cake_id}', mode=0o777)
                    if not cake_form.images.data[0].filename:
                        shutil.copy('./static/img/cake-default.jpg', f'./static/img/cakes/{cake_id}/cake.jpg')
                    else:
                        for img in cake_form.images.data:
                            img.save(f'./static/img/cakes/{cake_id}/{secure_filename(img.filename)}')
        elif request.args['action'] == 'update':
            if cake_form.validate_on_submit():
                cake_id = request.args['id']
                with sql.connect(user=config['database']['user'],
                                 password=config['database']['password'],
                                 host=config['database']['host'],
                                 database=config['database']['name']) as con:
                    cur = con.cursor()
                    cur.execute(f'UPDATE cakes SET title = %s, description = %s, cost = %s WHERE id = {cake_id};',
                                (cake_form.title.data, cake_form.description.data, cake_form.cost.data))
                    con.commit()

                    if len(cake_form.images.data) > 1 or cake_form.images.data[0].filename:
                        for root, dirs, files in os.walk(f'static/img/cakes/{cake_id}', topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                        for i, img in enumerate(cake_form.images.data):
                            img.save(f'./static/img/cakes/{cake_id}/{i}' + f'_{img.filename.split(".")[-1]}')
        active_accordion = 'cake'
    elif request.args.get('entity', None) == 'feedback':
        if request.args['action'] == 'delete':
            os.remove('.' + feedback_list[int(request.args["id"])][0])
        elif request.args['action'] == 'create':
            if feedback_form.validate_on_submit():
                if feedback_form.image.data.filename != '':
                    feedback_form.image.data.save(
                        f'./static/img/feedback/{time.time()}.{feedback_form.image.data.filename.split(".")[-1]}')
        active_accordion = 'feedback'
    elif request.args.get('entity', None) == 'example':
        if request.args['action'] == 'delete':
            if os.path.exists(f'static/img/examples/{request.args["id"]}'):
                shutil.rmtree(f'static/img/examples/{request.args["id"]}')
        elif request.args['action'] == 'create':
            if example_form.validate_on_submit():
                example_id = get_max_example_id(examples_list) + 1
                if not os.path.exists(f'static/img/examples/{example_id}'):
                    os.mkdir(f'static/img/examples/{example_id}', mode=0o777)
                if not example_form.images.data[0].filename:
                    shutil.copy('./static/img/cake-default.jpg', f'./static/img/examples/{example_id}/cake.jpg')
                else:
                    for img in example_form.images.data:
                        img.save(f'./static/img/examples/{example_id}/{secure_filename(img.filename)}')
        active_accordion = 'examples'
    cakes, n_cake_pages = get_cakes()
    return render_template('admin.html',
                           cakes=cakes,
                           n_cake_pages=n_cake_pages,
                           cake_form=cake_form,
                           examples=get_examples(),
                           example_form=example_form,
                           feedback_form=feedback_form,
                           feedback=get_feedback(),
                           is_admin=True,
                           active_accordion=active_accordion,
                           title='Панель администратора')


@application.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(application.root_path, 'static'), 'img/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    application.run(host='0.0.0.0')
