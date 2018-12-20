from flask import render_template
from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/index/')
def index():
    user = {'username': 'Jack'}
    board_size = 17
    return render_template('index.html', user=user, board_size=board_size)

@app.route('/game/')
def game():
    return render_template('index.html', user=user)
