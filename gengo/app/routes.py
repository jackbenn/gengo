from flask import render_template, request
from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/join', methods=['GET'])
def join():
    return render_template('join.html')

@app.route('/game', methods=['GET'])
def game():
    game_name = request.args.get('game_name')
    board_size = int(request.args.get('board_size'))
    return render_template('game.html', game_name=game_name, board_size=board_size)
