# @authors: Ashley, Emily, Louisa, Madelynn
import cs304dbi as dbi
from datetime import datetime

# ==========================================================
# This file is to hold functions that execute queries.
# These functions are called in app.py.

def add_post(conn, form, time, sid):
    ''' Adds a new post to the database and commits
    '''
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the web interface
    title = form['title']
    if title and len(title) > 30:
        title = title[:30]
    description = form['description']
    if description and len(description) > 500:
        description = description[:500]
    location = form['location']
    if location and len(location) > 50:
        location = location[:50]
    oncampus = form['oncampus']
    tag = form['tag']
    professor = form.get('professor', None) # default is None
    if professor and len(professor) > 50:
        professor = professor[:50]
    course = form.get('class', None)
    if course and len(course) > 8:
        course = course[:8]
    date = form.get('date')  
    date = datetime.strptime(date, '%m-%d-%Y') # re-formatted the date so sql will accept it
    # timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S') if date else None
    curs = dbi.dict_cursor(conn)

    # NEED TO LATER add sid
    curs.execute('''insert into post(title, description, timestamp, location, 
                    on_campus, tag, professor, class, date, status, sid) 
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''', 
                    [title, description, time, location, oncampus, tag, 
                    professor, course, date, 'open', sid]) 
    conn.commit()

def update_post(conn, form, time, pid):
    ''' Updates a post in the database and commits
    ''' 
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the web interface
    title = form['title']
    if title and len(title) > 30:
        title = title[:30]
    description = form['description']
    if description and len(description) > 500:
        description = description[:500]
    location = form['location']
    oncampus = form['oncampus']
    if location and len(location) > 50:
        location = location[:50]
    tag = form['tag']
    professor = form.get('professor', None) # default is None
    if professor and len(professor) > 50:
        professor = professor[:50]
    course = form.get('class', None)
    if course and len(course) > 8:
        course = course[:8]
        
    date = form.get('date')  
    date = datetime.strptime(date, '%m-%d-%Y') # re-format the date so sql will accept it
    curs = dbi.dict_cursor(conn)
    
    # Don't update timestamp for now, may change for alpha
    curs.execute('''update post set title = %s, description = %s, location = %s, 
                    on_campus = %s, tag = %s, professor = %s, class = %s, 
                    date = %s, status = %s where pid = %s''', 
                    [title, description, location, oncampus, tag, 
                    professor, course, date, 'open', pid]) 
    conn.commit()

def delete_post(conn, pid):
    '''
    Deletes post from the database and commit
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''delete from post where pid = %s''', [pid])
    conn.commit()


def get_postinfo(conn, pid):
    '''
    Retrieve the post information given the pid
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, 
                    title, description, timestamp, location, on_campus, tag, 
                    professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id and pid = %s''', [pid])
    result = curs.fetchone()
    return result
    
def get_posts(conn):
    '''
    Retrieves posts with information for the stream page and returns them
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, student.id as id, title, description, 
                    timestamp, location, on_campus, tag, professor, class, date, status, pid
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id;''')
    return curs.fetchall()

def filter_posts(conn, type):
    '''
    Filters posts based on criteron and returns
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select student.name as studentname, student.major1 as major, 
                    student.major2_minor as major2_minor, title, description, 
                    timestamp, location, on_campus, tag, professor, class, date, status
                    from post, student 
                    where post.sid is not NULL and post.sid = student.id and tag = %s;''', [type])
    return curs.fetchall()

def upload_profile_pic(conn, nm, filename):
    '''
    Uploads the user's profile picture to the database
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''insert into student(id,profile_pic) values (%s,%s)
                    on duplicate key update profile_pic = %s''',
                    [nm, filename, filename])
    conn.commit()

def add_profile_info(conn, name, phnumber, major1, major2_minor, dorm, id):
    '''
    Adds the user's profile information to the database
    '''
    # Parsing form entries and cutting off entries that are too long 
    # in case post request is not sent through the browser
    if name and len(name) > 40:
        name = name[:40]
    if phnumber and len(phnumber) > 12:
        phnumber= phnumber[:12]
    if dorm and len(dorm) > 20:
        dorm = dorm[:20]
    curs = dbi.dict_cursor(conn)
    
    curs.execute('''update student set name = %s, phone_num = %s, major1 = %s, 
                    major2_minor = %s, dorm_hall = %s where id = %s''', 
                    [name, phnumber, major1, major2_minor, dorm, id])
    conn.commit()

def get_user_info(conn, id):
    '''
    Gets the user's name given the id, may be null
    '''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select name, phone_num, email_address, major1, 
                    major2_minor, dorm_hall, profile_pic 
                    from student where id = %s''', [id])
    return curs.fetchone()

# def get_phnum(conn, id): 
#     '''
#     Gets the user's phone number given the id
#     '''
#     curs = dbi.dict_cursor(conn) 
#     curs.execute('''select phone_num from student where id = %s''', [id])
#     return curs.fetchone()