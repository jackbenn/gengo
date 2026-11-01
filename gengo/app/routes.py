from flask import abort, render_template, request
from flask import Flask
import os
#import app
app = Flask(__name__)

# Also enforced by the game server (server.MAX_BOARD_SIZE).
MAX_BOARD_SIZE = 51

# The Brython release in static/brython, added to its URLs so that browsers
# fetch the new files after an upgrade rather than mixing cached versions.
BRYTHON_VERSION = "3.14.3"


@app.context_processor
def page_settings():
    """Values every page needs.

    ws_url is where the browser opens its websocket to the game server. Empty
    (the default) means through the site's own /gengo/ws proxy, as deployed
    behind nginx. Set GENGO_WS_URL to reach the game server directly, as in
    local development: GENGO_WS_URL=ws://localhost:8765.
    """
    return {'brython_version': BRYTHON_VERSION,
            'ws_url': os.environ.get('GENGO_WS_URL', '')}


@app.route('/gengo/static/<path:pathname>')
def gengo_static(pathname):
    '''Override default static method'''
    return app.send_static_file(pathname)

@app.route('/gengo/')
def index():
    return render_template('index.html')

@app.route('/gengo/new')
@app.route('/gengo/join')
def redirect_to_index():
    from flask import redirect
    return redirect('/gengo/')


@app.route('/gengo/game', methods=['GET'])
def game():
    game_name = request.args.get('game_name')
    try:
        board_size = int(request.args.get('board_size'))
    except (TypeError, ValueError):
        abort(400, "board_size must be a whole number")
    if not 1 <= board_size <= MAX_BOARD_SIZE:
        abort(400, f"board_size must be from 1 to {MAX_BOARD_SIZE}")
    action = request.args.get('action')

    allow_suicide = "-"
    play_in_own_overlap = "-"
    play_black = "-"
    handicap = 1
    overlap = 'standard'
    show_scores = False

    if action == "new":
        allow_suicide = "allow_suicide" in request.args
        play_in_own_overlap = "play_in_own_overlap" in request.args
        play_black = "play_black" in request.args
        try:
            handicap = int(request.args.get('handicap'))
        except:
            handicap = 1
        overlap = request.args.get('overlap')
        show_scores = "show_scores" in request.args
    return render_template('game.html',
                           game_name=game_name,
                           board_size=board_size,
                           allow_suicide=allow_suicide,
                           play_in_own_overlap=play_in_own_overlap,
                           play_black=play_black,
                           handicap=handicap,
                           overlap=overlap,
                           show_scores=show_scores,
                           action=action)
