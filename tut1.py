from flask import Flask, render_template, request, session,redirect
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import math
import smtplib


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.secret_key = 'super-secret'
app.config['UPLOAD_FOLDER'] = params['upload_location']
'''app.config.update(
    MAIL_SERVER=smtplib.SMTP('smtp.gmail.com',587)
    #MAIL_PORT='465',
    MAIL_USE_SSL='True',
    MAIL_USERNAME=['gmail-user'],
    MAIL_PASSWORD=['gmail-pass']
)
mail = Mail(app)
'''
if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    '''sno,name,email,phn_nm,msg,date'''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(25), nullable=False)
    phn_nm = db.Column(db.String(15), nullable=False)
    msg = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(10), nullable=True)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(10), nullable=True)
    img_file = db.Column(db.String(10), nullable=True)
    subtitle = db.Column(db.String(80), nullable=True)


# home
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts']) ]
    # Pagination logic
    # First we will arrange all the post in list and then according to
    # the page no request we get from user we will slice that part and pass it as arg to index.html
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page+1)
    elif page == last:
        prev = "/?page=" + str(page-1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)
    #posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    #return render_template('index.html', params=params, posts=posts)


# contact
@app.route("/contact.html", methods=["GET", "POST"])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone_no = request.form.get('phn_nm')
        message = request.form.get('msg')
        entry = Contacts(name=name, email=email, phn_nm=phone_no, msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        text = "you got this mail from wall_you_got"
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login("prathamkishore47@gmail.com","Pkishore@2605")
        server.sendmail("prathamkishore47@gmail.com",email,text)
        '''mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone_no
                          )'''
    return render_template('contact.html',params=params )


# about
@app.route("/about")
def about():
    return render_template('about.html', )

# dashboard
@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('manage.html', params=params, posts=posts)
    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == params['admin_user'] and password == params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('manage.html', params=params, posts=posts)
    return render_template('login.html', params=params)


# post
@app.route("/post.html/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            stitle = request.form.get('stitle')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()
            if sno == '0':
                post = Posts(title=box_title, slug=slug, content=content, subtitle=stitle, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/dashboard')

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params,post=post,sno=sno)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/uploader", methods=['GET', 'POST'])
def upload():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "file uploaded successfully"

@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/postgroup")
def postgroup():
    posts = Posts.query.filter_by().all()[0:params['posts']]
    return render_template('postgroup.html', params=params, posts=posts)


app.run(debug=True)
