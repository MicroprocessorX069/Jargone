from flask import Flask,render_template,flash ,redirect,url_for, session, logging,request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators,SubmitField, Field
from wtforms import TextField
from passlib.hash import sha256_crypt
from functools import wraps


app=Flask(__name__)
#Config MySQL
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
#app.config['MYSQL_PASSWORD']='vineet9623'
app.config['MYSQL_DB']='myflaskapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'
# init MySQL
mysql=MySQL(app)
id=1
@app.route('/')
def index():

    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if result>0:
        return render_template('articles.html',articles=articles)
    else:
        msg='No articles found :('
        return render_template('articles.html',msg=msg)
    cur.close()

@app.route('/article/<string:id>')
def article(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id =%s",[id])
    article=cur.fetchone()
    return render_template('article.html',article=article)

class RegisterForm(Form):
    name=StringField('Name', validators=[validators.Length(min=1, max=50)])
    username=StringField('Username', validators=[validators.Length(min=4, max=50)])
    email=StringField('Email', validators=[validators.Length(min=6, max=50)])
    password=PasswordField('Password', validators=[
    validators.DataRequired(),
    validators.EqualTo('confirm',message='Passwords do match')])
    confirm=PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))

        #creating cursor to query
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s, %s, %s, %s)",(name, email, username, password))
         #commit to db
        mysql.connection.commit()

         #close db
        cur.close()

        flash("You are now registered.",'success')

        return redirect(url_for('index'))
    return render_template('register.html',form=form)

#Login
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password_candidate=request.form['password']

        #Retrieve password from db
        cur=mysql.connection.cursor()
        #get user by user Name
        result=cur.execute("SELECT * FROM users WHERE username= %s",[username])
        if result>0:
            #get hash value of password
            data=cur.fetchone() # first the first appearing row with the Username
            password=data['password']

            #Now compare Passwords
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in']=True
                session['username']=username

                flash('You are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error='Invalid Crednetials'
                return render_template('login.html',error=error)
            cur.close()
        else:
            error='Username Not Found'
            return render_template('login.html',error=error)

    return render_template('login.html')

#Decorator used for authorization of login
#http://flask.pocoo.org/snippets/98/
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized  pLEASE LOGIN', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if result>0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg='No articles found :('
        return render_template('dashboard.html',msg=msg)
    cur.close()

#Article addition
class ArticleForm(Form):
    title=StringField('Title', validators=[validators.Length(min=1, max=200)])
    body=StringField('Body')

class NotesForm(Form):
    title=StringField('Title', validators=[validators.Length(min=1, max=200)])
    body=StringField('Body')
    notes=StringField('Notes')


@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])
    article=cur.fetchone()
    form=NotesForm(request.form)
    #Populating with article fieldds

    form.title.data=article['title']
    form.body.data=article['body']

    if request.method=="POST" and form.validate():
        title=form.title.data
        body=form.body.data
        notes=form.notes.data

        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO notes(title, body, notes) VALUES (%s, %s, %s)",(title,body,notes))
        mysql.connection.commit()
        cur.close()
        flash("Notes Created",'success')

        return redirect(url_for('notes'))
    return render_template('edit_article.html',form=form)

@app.route('/notes')
@is_logged_in
def notes():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM notes")
    note=cur.fetchone()
    return render_template("notes.html",note=note)


@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        #tags=form.tags.data
        title=form.title.data
        body=form.body.data

        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title, body, author) VALUES (%s, %s, %s)",(title,body,session['username']))
        #cur.execute("INSERT INTO research_papers(NAME, AUTHOR_NAME) VALUES (%s, %s)",(title,session['username']))
        #for tag in tags:
        #    cur.execute("INSERT INTO rp_tags(id,TAG) VALUES (%s,%s)",(id,tag))

        mysql.connection.commit()
        #id+=1
        cur.close()
        flash("Article Created",'success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)


@app.route('/add_research_paper',methods=['GET','POST'])
@is_logged_in
def add_research_paper():
    return render_template(add_research_paper)



@app.route('/reviews')
def reviews():
    return render_template("reviews.html")


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been successfully logged out','success')
    return redirect(url_for('login'))

@app.route('/comparison')
def comparison():
    return render_template("comparison.html")

@app.route('/faqs')
def faqs():
    return render_template("faqs.html")

if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
