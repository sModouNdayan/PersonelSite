from flask import Flask,render_template,flash,redirect,url_for,session,request,logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
#from passlib.hash import msdcc2


app=Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'databasesiteweb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql=MySQL(app)

#Articles=Articles()

@app.route('/')
def index() :
    return  render_template('home.html')

@app.route('/about')
def about() :
     return render_template('about.html')

@app.route('/articles')
def articles() :
    cur = mysql.connection.cursor()
    resultat = cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if resultat > 0:
        return render_template("articles.html",articles=articles)
    else:
        msg="No article found !"
        return render_template("articles.html",msg=msg)
    cur.close()


@app.route('/article/<string:id>')
def article(id) :
    cur = mysql.connection.cursor()
    resultat = cur.execute("SELECT * FROM articles WHERE id =%s",[id])
    article=cur.fetchone()

    return render_template('article.html',article=article)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session :
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please log in ", "danger")
            return redirect (url_for ("login"))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard() :
    
    cur = mysql.connection.cursor()
    resultat = cur.execute("SELECT * FROM articles")
    articles=cur.fetchall()
    if resultat > 0:
        return render_template("dashboard.html",articles=articles)
    else:
        msg="No article found !"
        return render_template("dashboard.html",msg=msg)
    cur.close()


 
@app.route('/logout')
@is_logged_in
def logout() :
    session.clear()
    flash('You are logged out ','success')
    
    return redirect(url_for('login'))




class RegisterForm (Form):
    name = StringField('Name',[validators.Length(min=1, max=50)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=6, max=50)])
    password=PasswordField('Password',[
        validators.DataRequired(),
        validators.EqualTo('confirm',message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method ==  'POST' and form.validate():

        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=form.password.data
        

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,username,password) VALUES (%s,%s,%s,%s)",(name,email,username,password))

        mysql.connection.commit()

        cur.close()

        flash('You now are registed and you can log in', 'success')
        
        redirect(url_for('login'))

    return render_template('register.html',form=form)    


@app.route('/login', methods=['GET','POST'])
def login ():
    if request.method ==  'POST' :
        username=request.form['username']
        password_given=request.form['password']
        

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username =%s", [username])
       

        if result > 0 :
            data = cur.fetchone()
            password = data['password']
            
            if password == password_given :
               session['logged_in'] = True
               session['username'] = username
               flash('You are now logged in ! ','success')

               return redirect(url_for('dashboard'))

            else:
                error="Invalid login !"
                return render_template('login.html',error=error) 
            cur.close()       
        else:
            error="Username not found !"
            return render_template('login.html',error=error)    
    return render_template('login.html')


class ArticleForm (Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])


@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if request.method ==  'POST' and form.validate():

        title=form.title.data
        body=form.body.data
       
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO articles (title,author,body) VALUES (%s,%s,%s)",(title,session['username'],body))

        mysql.connection.commit()

        cur.close()

        flash('Article created succesfuly', 'success')
        
        return redirect(url_for('dashboard'))

    return render_template('add_article.html',form=form)    


@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    cur = mysql.connection.cursor()
    
    resultat = cur.execute("SELECT * FROM articles WHERE id =%s",[id])

    article=cur.fetchone()

    form=ArticleForm(request.form)
    form.title.data=article['title']
    form.body.data=article['body']
    

    if request.method ==  'POST' and form.validate():

        title=request.form['title']
        body=request.form['body']
       
        cur = mysql.connection.cursor()
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s  ",(title,body,id))

        mysql.connection.commit()
        cur.close()
        flash('Article updated succesfuly  !','success')
        return redirect(url_for('dashboard')) 
    return render_template('edit_article.html',form=form) 

@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id) :
    cur = mysql.connection.cursor()
    resultat = cur.execute("DELETE FROM articles WHERE id =%s",[id])

    mysql.connection.commit()
    cur.close()
    flash('Article updated succesfuly  !','success')
    return redirect(url_for('dashboard')) 

if __name__ == '__main__':
    app.secret_key='1234'
    app.run(debug=True)
    