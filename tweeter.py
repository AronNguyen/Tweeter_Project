from flask import Flask, render_template, request, session, redirect
from flaskext.mysql import MySQL
from flask_session import Session

mysql = MySQL()
app = Flask(__name__)
app.secret_key = '123456'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'tweeter'
app.config['SESSION_TYPE'] = 'filesystem'
mysql.init_app(app)
Session(app)


@app.route('/')
def main():
    if 'user_id' in session and session['user_id']:
        return redirect('/home')

    return render_template('index.html')

@app.route('/signin', methods=['GET'])
def signin():
    return render_template('signin.html')

@app.route('/signin', methods=['POST'])
def signinPost():
    email = request.form.get('email')
    password = request.form.get('password')

    if email and password:
        conn = mysql.connect()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = '%s' AND password = '%s'" % (email, password))
        found = cur.fetchall()

        cur.close()
        conn.close()

        if found:
            session['user_id'] = found[0][0]
            return redirect('/home')
        else:
            return render_template('message.html', message='Wrong email or password!')
    else:
        return render_template('message.html', message='You must enter your email and password!')

@app.route('/signout', methods=['GET'])
def signout():
    session['user_id'] = None
    return redirect('/')

@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signupPost():
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    password = request.form.get('password')

    if fname and lname and email and password:
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO users SET firstname = '%s', lastname = '%s', email = '%s', password = '%s', created_at = NOW()" % (
            fname,
            lname,
            email,
            password
        ))
        cur.close()
        conn.commit()
        conn.close()
        return render_template('message.html', message='Account created!')
    else:
        return render_template('message.html', message='You must enter all fields!')

@app.route('/home')
def home():
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT follows_user_id FROM followings WHERE user_id = '%d'" % (session['user_id']))
    followings = cur.fetchall()
    followed_ids = ['0']

    for following in followings:
        followed_ids.append(str(following[0]))

    cur.execute("SELECT t.content, u.firstname, u.id FROM tweets AS t INNER JOIN users AS u ON u.id = t.user_id WHERE t.user_id = '%d'" % (session['user_id']))
    your_tweets = cur.fetchall()

    cur.execute("SELECT t.content, u.firstname, u.id FROM tweets AS t INNER JOIN users AS u ON u.id = t.user_id WHERE t.user_id IN (%s)" % (','.join(followed_ids)))
    following_tweets = cur.fetchall()

    cur.execute("SELECT t.content, u.firstname, u.id FROM tweets AS t INNER JOIN users AS u ON u.id = t.user_id WHERE t.user_id NOT IN (%d, %s)" % (session['user_id'], ','.join(followed_ids)))
    other_tweets = cur.fetchall()

    cur.close()
    conn.commit()
    conn.close()

    return render_template(
        'home.html',
        your_tweets=your_tweets,
        following_tweets=following_tweets,
        other_tweets=other_tweets
    )

@app.route('/tweet', methods=['POST'])
def tweetPost():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO tweets SET user_id = '%s', content = '%s', created_at = NOW()" % (
        session['user_id'],
        request.form.get('content')
    ))
    cur.close()
    conn.commit()
    conn.close()

    return render_template('message.html', message='Tweet posted!')

@app.route('/profile')
def profile():
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = '%s'" % (request.args.get('user_id')))
    users = cur.fetchall()

    cur.execute("SELECT t.content, u.firstname, u.id FROM tweets AS t INNER JOIN users AS u ON u.id = t.user_id WHERE t.user_id = '%d'" % (users[0][0]))
    tweets = cur.fetchall()

    cur.close()
    conn.commit()
    conn.close()

    return render_template('profile.html', user=users[0], tweets=tweets)


#unfinished like, similar to follow





@app.route('/follow')
def follow():
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = '%s'" % (request.args.get('user_id')))
    users = cur.fetchall()

    cur.execute("INSERT INTO followings SET user_id = '%s', follows_user_id = '%s', created_at = NOW()" % (
        session['user_id'],
        request.args.get('user_id')
    ))

    cur.close()
    conn.commit()
    conn.close()

    return render_template('message.html', message='You are now following this user!')

if __name__ == '__main__':
    app.run(debug=True)
