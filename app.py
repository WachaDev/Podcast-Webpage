import os
import random

from flask import Flask, render_template, request, redirect, flash, abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FileField, TextAreaField
from wtforms.validators import InputRequired, Length, EqualTo, Email, Regexp, Optional
from bcrypt import hashpw, gensalt, checkpw
from werkzeug.utils import secure_filename
from jinja2 import TemplateNotFound
from sqlalchemy import not_, and_, or_

from database import SessionLocal, init_db
from models import Users, Podcast

app = Flask(__name__)
app.config['SECRET_KEY'] = 'b$2b$12$3MUJHIrPW2tS5o3LdjYme'
app.config['UPLOAD_IMAGE_FOLDER'] = '/home/wachadev/Programming/Python/Pd_wepage/Podcast-Webpage/uploads/images'
app.config['UPLOAD_AUDIO_FOLDER'] = '/home/wachadev/Programming/Python/Pd_wepage/Podcast-Webpage/uploads/audio'

DATABASE_EXCEPTION = 'Oh no! We\'re having problems from the server-side'

IMAGE_ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
AUDIO_ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'oga', 'flac'}

session = SessionLocal()
init_db()

class CreateAccountForm(FlaskForm):
    email = StringField('email', validators=[
        InputRequired('This field is required.'), 
        Email('Invalid e-mail.'), 
        Regexp(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', 
        0,
        'Write your e-mail address with a format someone@example.com.')
    ])
    username = StringField('usrname', validators=[
        InputRequired('This field is required.'), 
        Length(-1, 20, '20 is the max characters long.')
    ])
    password = PasswordField('psw', validators=[
        InputRequired('This field is required.'), 
        EqualTo('confirm_password', 'Password must match.'), 
        Regexp(r'(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}', 
        0, 
        'Must contain at least one  number and one uppercase and \
            lowercase letter, and at least be between 8 and 16 characters.')
    ])
    confirm_password = PasswordField('confirm_psw',validators=[
        InputRequired('This field is required.')
    ])

class LoginForm(FlaskForm):
    username = StringField('usrname', validators=[
        InputRequired('A username is required.')
    ])
    password = PasswordField('psw', validators=[
        InputRequired('A password is required.')
    ])
    remember = BooleanField('remember_me')

class UploadPodcastForm(FlaskForm):
    title = StringField('title', validators=[
        InputRequired('We need a title!')
    ])
    image = FileField('image', validators=[Optional()])
    audio = FileField('audio', validators=[
        InputRequired('We need your podcast here!')
    ])
    description = TextAreaField('description', validators=[Optional()])


@app.route('/')
def home():
    try:    
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)


@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    err_email = None
    err_usr = None
    form = CreateAccountForm()

    if form.validate_on_submit():
        email = form.email.data
        usrname = form.username.data
        psw = form.password.data

        usrname_exists = bool(session.query(Users.id).filter_by(username=usrname).scalar())
        email_exists = bool(session.query(Users.id).filter_by(e_mail=email).scalar())

        if email_exists:
            err_email = 'This e-mail already exists.'
        elif usrname_exists:
            err_usr = 'This username already exists.'
        else:
            encode_psw = hashpw(psw.encode('UTF-8'), gensalt())

            new_user = Users(
                e_mail=email,
                username=usrname,
                password=encode_psw,
            )

            try:
                session.add(new_user)
                session.commit()
                return redirect('/login')
            except:
                session.rollback()
                return DATABASE_EXCEPTION

    try: 
        return render_template('create_account.html', form=form, err_email=err_email, err_usr=err_usr)
    except TemplateNotFound:
        abort(404)
            
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    err_db = None
    form = LoginForm()
    
    if form.validate_on_submit():
        usrname = form.username.data
        psw = form.password.data
        remember = form.remember.data
        
        user_exists = session.query(Users).filter_by(username=usrname).first()
        
        if user_exists:
            check_psw = checkpw(psw.encode('UTF-8'), user_exists.password)
            if check_psw:
                flash(f'Welcome {usrname}!')
                return redirect('/')
            else:
                err_db = 'Invalid password'  
        else:
            err_db = 'Invalid username'

    try:
        return render_template('login.html', form=form, err_db=err_db)
    except TemplateNotFound:
        abort(404)


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    err_image = None
    err_audio = None
    img_folder = app.config['UPLOAD_IMAGE_FOLDER']
    audio_folder = app.config['UPLOAD_AUDIO_FOLDER']
    form = UploadPodcastForm()
    
    if form.validate_on_submit():
        title = form.title.data
        image = form.image.data
        audio = form.audio.data
        description = form.description.data

        if not allowed_file(image.filename, IMAGE_ALLOWED_EXTENSIONS):
            err_image = 'Invalid image format, use ' + \
                ', '.join(IMAGE_ALLOWED_EXTENSIONS) + ' instead.'
        elif not allowed_file(audio.filename, AUDIO_ALLOWED_EXTENSIONS):
            err_audio = 'Invalid audio format, use ' + \
                ', '.join(AUDIO_ALLOWED_EXTENSIONS) + ' instead.'
        else:
            image_name = secure_filename(image.filename)
            img_path = os.path.join(img_folder, image_name)
            image.save(img_path)

            audio_name = secure_filename(audio.filename)
            audio_path = os.path.join(audio_folder, audio_name)
            audio.save(audio_path)

            new_podcast = Podcast(
                title=title,
                image=img_path,
                audio=audio_path,
                description=description,
            )

            try:
                session.add(new_podcast)
                session.commit()
                flash('Uploaded')
                return redirect('/')
            except:
                session.rollback()
                return DATABASE_EXCEPTION

    try:
        return render_template('upload.html', form=form, err_image=err_image, err_audio=err_audio)
    except:
        abort(404)


@app.errorhandler(404)
def not_found(e):
    return '<h1>Page not found</h1>', 404


if __name__ == '__main__':
    app.run(debug=True)
