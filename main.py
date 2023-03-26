from flask import Flask, render_template
from math import ceil
import uuid

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    cakes = [(['/static/cakes/0/cake1.jpg', '/static/cakes/0/cake2.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4()),
             (['/static/cakes/0/cake1.jpg', '/static/cakes/0/cake2.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4()),
             (['/static/cakes/0/cake1.jpg', '/static/cakes/0/cake2.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4()),
             (['/static/cakes/0/cake2.jpg', '/static/cakes/0/cake1.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4())]

    return render_template('index.html', cakes=cakes, active_page=0)


@app.route('/cakes/<int:cake_active_page>')
def cakes(cake_active_page):

    CAKES_PER_PAGE = 5

    cakes = [(['/static/cakes/0/cake1.jpg', '/static/cakes/0/cake2.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4()),
             (['/static/cakes/0/cake2.jpg', '/static/cakes/0/cake1.jpg'], 'Клубничный торт', 'Заказывай, Пес!', uuid.uuid4())]
    n_cake_pages = ceil(len(cakes) / CAKES_PER_PAGE)
    return render_template('cakes.html',
                           cakes=cakes,
                           active_page=2,
                           cake_active_page=cake_active_page,
                           n_cake_pages=n_cake_pages,
                           CAKES_PER_PAGE=CAKES_PER_PAGE)


@app.route('/about')
def about():
    return render_template('about.html', active_page=1)


@app.route('/feedback')
def feedback():
    return render_template('feedback.html', active_page=3)


if __name__ == '__main__':
    app.run(debug=True)
