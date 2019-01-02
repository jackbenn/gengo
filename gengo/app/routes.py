from flask import render_template, request
from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/game', methods=['GET'])
def game():
    board_size = int(request.args.get('size'))
    return render_template('game.html', board_size=board_size)
