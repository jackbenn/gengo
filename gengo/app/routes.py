from flask import render_template, request
from flask import Flask
import os
#import app
app = Flask(__name__)

@app.route('/gengo/static/<path:pathname>')
def gengo_static(pathname):
    '''Override default static method'''
    return app.send_static_file(pathname)

@app.route('/gengo/')
def index():
    return render_template('index.html')

@app.route('/gengo/new')
def new():
    return render_template('new.html')


@app.route('/gengo/join', methods=['GET'])
def join():
    return render_template('join.html')


@app.route('/gengo/game', methods=['GET'])
def game():
    game_name = request.args.get('game_name')
    board_size = int(request.args.get('board_size'))
    action = request.args.get('action')

    allow_suicide = "-"
    play_in_own_overlap = "-"
    play_black = "-"
    handicap = 1
    overlap='standard'

    if action == "new":
        allow_suicide = "allow_suicide" in request.args
        play_in_own_overlap = "play_in_own_overlap" in request.args
        play_black = "play_black" in request.args
        try:
            handicap = int(request.args.get('handicap'))
        except:
            handicap = 1
        overlap = request.args.get('overlap')
    return render_template('game.html',
                           game_name=game_name,
                           board_size=board_size,
                           allow_suicide=allow_suicide,
                           play_in_own_overlap=play_in_own_overlap,
                           play_black=play_black,
                           handicap=handicap,
                           overlap=overlap,
                           action=action)
