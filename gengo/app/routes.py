from flask import render_template, request
from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/join')
def index():
    return render_template('join.html')

@app.route('/game', methods=['GET'])
def game():
    game_size = int(request.args.get('name'))
    board_size = int(request.args.get('size'))
    return render_template('game.html', game_name=game_name, board_size=board_size)
