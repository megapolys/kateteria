from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from math import ceil
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pymysql as sql
import configparser
import uuid
import glob
import os

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
        cooked_cakes = [{'imgs': ['/' + p for p in glob.glob(f'static/cakes/{id}/*')],
                         'title': title,
                         'desc': desc,
                         'uuid': uuid.uuid4(),
                         'id': id} for id, title, desc in raw_cakes]
        n_cake_pages = ceil(len(cooked_cakes) / int(config['view']['cakes_per_page']))
        return cooked_cakes, n_cake_pages


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
    return render_template('index.html', cakes=cakes, active_page=0)


@app.route('/cakes/<int:cake_active_page>')
def cakes(cake_active_page):
    cakes, n_cake_pages = get_cakes()
    return render_template('cakes.html',
                           cakes=cakes,
                           active_page=2,
                           cake_active_page=cake_active_page,
                           n_cake_pages=n_cake_pages,
                           CAKES_PER_PAGE=int(config['view']['cakes_per_page']))


@app.route('/about')
def about():
    return render_template('about.html', active_page=1)


@app.route('/feedback')
def feedback():
    return render_template('feedback.html', active_page=3)


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
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
                return render_template('/admin_login.html', form=login_form, message='Пароль неверный!')
    return render_template('/admin_login.html', form=login_form)


@app.route('/admin')
@login_required
def admin():
    form = CakeCreateForm()
    if request.args.get('entity', None) == 'cake':
        if request.args['action'] == 'update':
            print(request.args['id'], request.args['action'])
        elif request.args['action'] == 'delete':
            with sql.connect(user=config['database']['user'],
                             password=config['database']['password'],
                             host=config['database']['host'],
                             database=config['database']['name']) as con:
                cur = con.cursor()
                print(int(request.args['id']))
                cur.execute('DELETE FROM cakes WHERE id = %s', request.args['id'])
                con.commit()

                if os.path.exists(f'static/cakes/{request.args["id"]}'):
                    os.rmdir(f'static/cakes/{request.args["id"]}')

    cakes, n_cake_pages = get_cakes()
    return render_template('admin.html', cakes=cakes, n_cake_pages=n_cake_pages, form=form)


@app.route('/create_cake', methods=['GET', 'POST'])
@login_required
def create_cake():
    form = CakeCreateForm()
    if form.validate_on_submit():
        with sql.connect(user=config['database']['user'],
                         password=config['database']['password'],
                         host=config['database']['host'],
                         database=config['database']['name']) as con:
            cur = con.cursor()
            cur.execute('INSERT INTO cakes(title, description) VALUES (%s, %s)', (form.title.data, form.description.data))
            con.commit()

            # TODO: fix no cakes case
            cur.execute('SELECT max(id) FROM cakes')
            cake_id = cur.fetchone()[0]

            if not os.path.exists(f'static/cakes/{cake_id}'):
                os.mkdir(f'static/cakes/{cake_id}', mode=0o777)
            for img in form.images.data:
                img.save(f'./static/cakes/{cake_id}/{secure_filename(img.filename)}')

    return redirect('/admin')


if __name__ == '__main__':
    app.run(debug=True)
