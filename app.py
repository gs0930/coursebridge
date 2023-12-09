from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

# @authors: Ashley, Emily, Louisa, Madelynn

import cs304dbi as dbi
# import cs304dbi_sqlite3 as dbi

import helper 
import random
import bcrypt
from datetime import datetime
from datetime import timedelta


import sys, os, random
import imghdr

app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2*1024*1024 # 2 MB

# To increase session time 
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/')
def index():
    '''
    This renders to login page for users to sign in when they load the website 
    '''
    return render_template('login.html',title='Login Page')

@app.route('/main/')
def main():
    '''
    This is the welcome page 
    '''
    return render_template('main.html',title='Welcome Page')


@app.route('/stream/', methods=['GET', 'POST'])
def stream():
    '''
    This handler function gets posts to display for 'get', and for 'post' it 
    filters the posts first with the indicated filters before returning them
    '''
    conn = dbi.connect()
    if request.method == 'GET':
        posts = helper.get_posts(conn)     
    if request.method == 'POST':
        search_query = request.form.get('search_query')

        # Fetch posts based on the search query
        if search_query is not None:
            search_results = helper.search(conn, search_query)
        else:
            search_results = []

        # Fetch posts based on filters
        type = request.form.get('type')
        if type:
            filtered = helper.filter_posts(conn, type)
        else:
            filtered = helper.get_posts(conn)

        # Combine such that only posts *both* the search and filter grabbed will be displayed
        posts = []
        if len(search_results) > 0:
            for i in filtered:
                if i in search_results: # if common, add to posts to stream
                    posts.append(i)

        date_order = request.form.get('dateorder')

        # sort posts by date order
        if date_order == 'early':
            posts = sorted(posts, key=lambda x:x['date'])
        elif date_order == 'late':
            posts = sorted(posts, key=lambda x:x['date'], reverse=True)

    # reformatting for display purposes and slicing for database purposes
    for post in posts:
        if post['timestamp']:   
            post['timestamp'] = get_time_difference(post['timestamp'])
        if post['major']:
            post['major'] = post['major'].replace('_', ' ')
        post['tag'] = post['tag'].replace('_', ' ')
        if post['major2_minor']:
            post['major2_minor'] = post['major2_minor'].replace('_', ' ')
        if len(post['description']) > 75: # If the description is too long, cut it short
            post['description'] = post['description'][:76] + '...'
        
    return render_template('stream.html',
                            title='Stream - Coursebridge', posts = posts, majors=["Computer Science"])


def get_time_difference(timestamp):
    '''
    Helper function to convert the timestamp into a time format that is more
    digestible to users (e.g., Wednesday, 11/15)
    '''
    current_time = datetime.now()
    time_difference = current_time - timestamp

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return f"{days} {'day' if days == 1 else 'days'} ago"
    elif hours > 0:
        return f"{hours} {'hour' if hours == 1 else 'hours'} ago"
    else:
        return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"
    
@app.route('/create/', methods=['GET', 'POST'])
def create_post():
    '''
    For creating the post; calls helper.add() to insert a new post, get and post
    '''

    if request.method == 'GET':
        return render_template('create_post.html', title='Create Post - Coursebridge')
    else:
        conn = dbi.connect()

        form_info = request.form  # dictionary of form data

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Handling the case where the session expires while the user
        # is in the midst of creating a post
        if 'id' in session:
            id = session['id']

            # To get name to display
            name = helper.get_name(conn, id)['name']
            session['name'] = name   
            helper.add_post(conn, form_info, timestamp, id)
            flash('Your post is created!')
        else:
            flash('Sorry, your session has expired. Please login again.')
            redirect(url_for('login'))
        
        return redirect(url_for('stream')) # redirect to the stream page so users can view others' posts

@app.route('/createprofile/', methods=["GET", "POST"])
def create_profile():
    if request.method == 'GET':
        return render_template('profile_form.html', title="Create Profile - Coursebridge")
    else:
        try:
            id = int(session['id'])
            f = request.files['pic']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            filename = secure_filename('{}.{}'.format(id,ext))
            pathname = os.path.join(app.config['UPLOADS'],filename)
            f.save(pathname)
            conn = dbi.connect()

            name = request.form['name']
            phnumber = request.form['phonenum']
            major1 = request.form['major1']
            major2_minor = request.form['major2_minor']
            dorm = request.form['dorm']

            # Handling the case where the session expires while the user
            # is in the midst of creating a profile
            if 'id' in session:
                # upload file if it exists
                if f: 
                    helper.upload_profile_pic(conn, id, filename)

                helper.add_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id)
                # To get name to display on nav bar after creating a profile
                user_name = helper.get_name(conn, id)['name']
                session['name'] = user_name
                flash('Profile Created!')
            else:
                flash('Sorry, your session has expired. Please login again.')
                redirect(url_for('login'))

            # Bring first-time users to the welcome/main page
            return redirect(url_for('main'))
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return render_template('profile_form.html',src='',nm='')
        
      

# Will likely use a variant of this function for alpha
# @app.route('/pic/<nm>')
# def pic(nm):
#     conn = dbi.connect()
#     curs = dbi.dict_cursor(conn)
#     numrows = curs.execute(
#         '''select filename from picfile where nm = %s''',
#         [nm])
#     if numrows == 0:
#         flash('No picture for {}'.format(nm))
#         return redirect(url_for('index'))
#     row = curs.fetchone()
#     return send_from_directory(app.config['UPLOADS'],row['filename'])

@app.route('/display/<pid>')
def display_post(pid):
    '''
    Method for displaying a singular full post
    '''
    conn = dbi.connect()
    post = helper.get_postinfo(conn, pid)

    # reformatting data for display purposes
    if post['timestamp']:   
            post['timestamp'] = get_time_difference(post['timestamp'])
    if post['major']:
        post['major'] = post['major'].replace('_', ' ')
    post['tag'] = post['tag'].replace('_', ' ')
    if post['major2_minor']:
        post['major2_minor'] = post['major2_minor'].replace('_', ' ')

    return render_template('display_post.html', title='Display Post - Coursebridge', post=post, pid=pid)


@app.route('/update/<pid>', methods=["GET", "POST"])
def update_post(pid):
    '''
    Method for getting the update post page and also updating the post
    '''
    conn = dbi.connect()
    if request.method == 'GET':
        post = helper.get_postinfo(conn, pid)
        post['date'] = post['date'].strftime("%m-%d-%Y") # To prefill accurately

        return render_template('update_post.html', title='Update Post - Coursebridge', post=post, pid=pid)
    else:
        conn = dbi.connect()
        action = request.form.get('submit')
        if action == 'update':
            form_info = request.form  # dictionary of form data
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Handling the case where the session expires while the user
            # is in the midst of creating a post
            id = 0
            if 'id' in session:
                id = session['id']

                # To get name to display
                name = helper.get_name(conn, id)['name']
                session['name'] = name   
            else:
                flash('Sorry, your session has expired. Please login again.')
                redirect(url_for('login'))
            
            helper.update_post(conn, form_info, timestamp, pid)

            flash('Your post is updated!')
        else: # for deleting the post
            helper.delete_post(conn, pid)
            flash('Post was deleted successfully')
        return redirect(url_for('stream')) # redirect to the stream page so users can view others' posts

@app.route('/logout')
def logout():
    '''
    Function that checks the current status and logs out the user
    if they were logged in. 
    '''
    if 'username' in session:
        username = session['username']
        session.pop('username')
        session.pop('id')
        session.pop('logged_in')
        flash('You are logged out')
        return redirect(url_for('index'))
    else:
        flash('You are not logged in. Please login or signup')
        return redirect(url_for('index') )

@app.route('/join/', methods=["POST", "GET"])
def join():
    '''
    Allows new users to sign up for an account with email and password, 
    encrypted with bycrpt. 
    '''
    if request.method == 'GET':
        return render_template('join.html')
    
    # For form post from join
    username = request.form.get('username')
    passwd1 = request.form.get('password1')
    passwd2 = request.form.get('password2')
    if passwd1 != passwd2:
        flash('passwords do not match')
        return redirect( url_for('index'))
    hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                           bcrypt.gensalt())
    stored = hashed.decode('utf-8')
    print(passwd1, type(passwd1), hashed, stored)
    conn = dbi.connect()
    curs = dbi.cursor(conn)
    try:
        curs.execute('''INSERT INTO student(id,email_address,hashed)
                        VALUES(null,%s,%s)''',
                        [username, stored])
        conn.commit()
    except Exception as err:
        # flash('That username is taken: {}'.format(repr(err)))
        flash("An account already exists with this email. Please login :)")
        return redirect(url_for('index'))
    curs.execute('select last_insert_id()')
    row = curs.fetchone()
    id = row[0]
    # flash('FYI, you were issued ID {}'.format(id))
    flash('You successfully created an account with {}'.format(username))
    session['username'] = username
    session['id'] = id
    session['logged_in'] = True
    session['visits'] = 1
    # return redirect( url_for('user', username=username) )
    return redirect( url_for('create_profile') )  # redirect to creating profile after joining

@app.route('/login/', methods=["POST", "GET"])
def login():
    '''
    Gets the login for for user
    Logs in the user using a post method 
    '''
    # Gets the form for user to login 
    if request.method == 'GET':
        return render_template('login.html')
    
    # Posts the form once user fills out information 
    else:
        username = request.form.get('username')
        passwd = request.form.get('password')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''SELECT id,hashed
                        FROM student
                        WHERE email_address = %s''',
                    [username])
        row = curs.fetchone()
        if row is None:
            # Same response as wrong password,
            # so no information about what went wrong
            flash('Login incorrect. Try again or join')
            return redirect( url_for('index'))
        stored = row['hashed']
        print('database has stored: {} {}'.format(stored,type(stored)))
        print('form supplied passwd: {} {}'.format(passwd,type(passwd)))
        hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),
                                stored.encode('utf-8'))
        hashed2_str = hashed2.decode('utf-8')
        print('rehash is: {} {}'.format(hashed2_str,type(hashed2_str)))
        if hashed2_str == stored:
            print('they match!')
            flash('successfully logged in with '+username)
            session['username'] = username
            session['id'] = row['id']
            session['logged_in'] = True
            session['visits'] = 1
           
            # To get name to display
            name = helper.get_name(conn, row['id'])['name']
            session['name'] = name
            # return redirect( url_for('user', username=username) )
            return redirect( url_for('stream') )
        else:
            flash('login incorrect. Try again or join')
            return redirect( url_for('index'))

@app.route('/user/<username>')
def user(username):
    """
    Page that displays user information
    This is for alpha round -- ignore for now 
    """
    try: 
        username = session['username']
        if 'username' in session: 
            username = session['username']
            id = session['id']
            session['visits'] = int(session['visits']) + 1
            return render_template('greet.html', page_title = 'Welcome!')
    except Exception as err:
        flash("Error" + str(err))
        return redirect( url_for('index'))



# You will probably not need the routes below, but they are here
# just in case. Please delete them if you are not using them

# @app.route('/greet/', methods=["GET", "POST"])
# def greet():
#     if request.method == 'GET':
#         return render_template('greet.html', title='Customized Greeting')
#     else:
#         try:
#             username = request.form['username'] # throws error if there's trouble
#             flash('form submission successful')
#             return render_template('greet.html',
#                                    title='Welcome '+username,
#                                    name=username)

#         except Exception as err:
#             flash('form submission error'+str(err))
#             return redirect( url_for('index') )



if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'coursebridge_db' 
    print('will connect to {}'.format(db_to_use))
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
