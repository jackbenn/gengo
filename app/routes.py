from flask import render_template
from flask import Flask
app = Flask(__name__)


@app.route('/')
@app.route('/index/')
def index():
    user = {'username': 'Jack'}
    return render_template('index.html', user=user)
