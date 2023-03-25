from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    cakes = [('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!')]
    return render_template('index.html', cakes=cakes)


@app.route('/cakes')
def cakes():
    cakes = [('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake2.jpg', 'Клубничный торт', 'Заказывай, Пес!'),
             ('static/img/cake1.jpg', 'Клубничный торт', 'Заказывай, Пес!')]
    return render_template('cakes.html', cakes=cakes)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/feedback')
def feedback():
    return render_template('feedback.html')


if __name__ == '__main__':
    app.run(debug=True)
