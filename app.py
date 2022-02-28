"""
This is a simple link-shortening tool that has a number of obvious issues
with it.

Your goal is to find and fix at least 4 issues. To install:

    py -3 -m venv .venv
    .venv\scripts\activate
    pip install flask flask-wtf flask-sqlalchemy short_url
    set FLASK_DEV=development
    set FLASK_APP=app.py 
    flask run
"""
import short_url
from flask import (
    Flask,
    make_response,
    render_template,
    render_template_string,
    redirect,
    url_for,
    flash
)
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import fields, validators
from sqlalchemy import text
from sqlalchemy.sql import select

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AB'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = False
db = SQLAlchemy(app)

class LinkForm(FlaskForm):
    name = fields.StringField('Name', validators=[validators.DataRequired()])
    url = fields.URLField('URL', validators=[validators.DataRequired()])
    submit = fields.SubmitField()

links = db.Table(
    'links',
    db.metadata,
    db.Column('id', db.Integer, primary_key=True),
    db.Column('name', db.Text),
    db.Column('url', db.Text)
)

db.create_all()

INDEX_TEMPLATE = '''<html>
    <head>
    </head>
    <body>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                <p>{{ message | safe }}</p>
                <a onclick={{ message }}>Hello</a>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="/">
            {{ form.url.label }}
            {{ form.url() }}
            {{ form.name.label }}
            {{ form.name() }}
            {{ form.submit() }}
        </form>
    </body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index_page():
    form = LinkForm()

    if form.validate_on_submit():
        stmt = links.insert().values(name=text(f'"{form.name.data}"'), url=text(f'"{form.url.data}"'))
        result = db.session.execute(stmt)
        db.session.commit()

        shorter_url = url_for(
            '.redirect_page',
            slug=short_url.encode_url(result.inserted_primary_key[0]),
            _external=True
        )
        flash(
            f'Your short url is: {shorter_url}, which redirects'
            f' to {form.url.data}.'
        )
        return redirect(url_for('.index_page'))

    return render_template_string(INDEX_TEMPLATE, form=form)

@app.route('/<slug>')
def redirect_page(slug):
    decoded_id = short_url.decode_url(slug)
    stmt = select(links).where(links.c.id == decoded_id)
    result = db.engine.execute(stmt)
    row = result.fetchone()

    return redirect(row.url)

@app.route('/xss/<param>/<param2>')
def xss(param):
    resp = make_response(render_template("xss.html", param=param))
    resp.headers['Content-Security-Policy'] = "default-src 'self';"
    return resp

@app.route('/storedxss/')
def storedxss():
    stmt = select(links)
    urls = db.engine.execute(stmt)
    resp = make_response(render_template("storedxss.html", urls=urls))
    resp.headers['Content-Security-Policy'] = "default-src 'self';"
    return resp