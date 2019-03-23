#!/usr/bin/env python3
from dbpass import db_password

import psycopg2
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    url_for,
    flash,
    jsonify,
    session as login_session)

import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from slugify import slugify
from markdown import markdown

app = Flask(__name__)
app.secret_key = 'super_secret_key'
# Load Jinja's "do" extension for operations in templates - like list.append()
app.jinja_env.add_extension('jinja2.ext.do')

document_root = "{}/".format(app.root_path)

CLIENT_ID = json.loads(
    open('{}google_secret.json'.format(
        document_root), 'r').read())['web']['client_id']
APPLICATION_NAME = "Repertorio App"

dbname = 'catalog'

# Database connection for all methods using WITH


class DBconn:
    def __enter__(self):
        self.db = psycopg2.connect(host='localhost', dbname=dbname,
            user='catalog', password=db_password)
        return self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.commit()
        self.db.close()

# Show line breaks for new line chars stored in database


def nl2br(text):
    return markdown(text, extensions=['nl2br'])


# Make nl2br accessible from templates
app.jinja_env.globals.update(nl2br=nl2br)


def makeState():
    state = ''
    if 'username' not in login_session:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in range(32))
        login_session['state'] = state
    return state


def createUser(login_session):
    with DBconn() as c:
        url = slugify(login_session['username'])
        query = "SELECT COUNT(*) FROM musicians WHERE url = %s"
        c.execute(query, (url,))
        num = c.fetchone()
        if num[0] > 0:
            url = url + str(num[0])
        data = (url, login_session['username'], login_session['email'],
                login_session['picture'], 0)
        query = """INSERT INTO musicians (url,name,email,picture,public)
        VALUES (%s,%s,%s,%s,%s)"""
        c.execute(query, data)
        return url


def getUserID(email):
    with DBconn() as c:
        query = "SELECT url FROM musicians WHERE email = %s"
        c.execute(query, (email,))
        result = c.fetchone()
        try:
            return result[0]
        except TypeError:
            return None


def listRepertoire(c, musician_id):
    query = """SELECT w.id, w.composer, w.title, w.duration,
    i.name, c.name, c.id, i.url
    FROM works w, instruments i, categories c
    WHERE  w.creator = %s AND i.url = w.instrument AND c.id = w.category
    ORDER BY i.url, c.id, split_part(w.composer, ' ', 2), w.title"""
    c.execute(query, (musician_id,))
    repertoire = c.fetchall()
    # Get the instruments from the works in the musician's repertoire list
    # and join them in a comma separated string.
    instruments = ', '.join({r[4] for r in repertoire})
    # The result will be a tuple:
    return (instruments, repertoire)


def listInstruments(c):
    # Get all instruments with the number of musicians
    # listing them in their repertoire
    query = """SELECT i.name, i.url, COUNT(DISTINCT m.name), i.creator
    FROM instruments i
    LEFT JOIN works w ON w.instrument = i.url
    LEFT JOIN musicians m ON m.url = w.creator
    GROUP BY i.name,i.rank,i.url
    ORDER BY i.rank"""
    c.execute(query)
    return c.fetchall()


def listMusicians(c, instrument):
    # Get musicians, who already have a repertoire
    if instrument == 0:
        # If instrument is not defined, get all musicians (start page),
        # together with their instruments
        query = """SELECT m.name, m.url, m.picture,
        STRING_AGG(DISTINCT i.name, ', ')
        FROM musicians m, works w, instruments i
        WHERE w.creator = m.url AND i.url = w.instrument
        GROUP BY m.name,m.url
        ORDER BY name"""
        c.execute(query)
    else:
        # If instrument is specified, get musicians who play it
        query = """SELECT DISTINCT m.name, m.url, m.picture
        FROM musicians m, works w
        WHERE w.instrument = %s AND w.creator = m.url
        ORDER BY name"""
        c.execute(query, (instrument,))
    return c.fetchall()

# The OAuth mechanism is based on Udacity's OAuth 2.0 course material
# (https://github.com/udacity/OAuth2.0)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('{}google_secret.json'.format(
            document_root), scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    result = json.loads(result.decode())

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    try:
        login_session['username'] = data['name']
    except KeyError:
        login_session['username'] = data['email']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = "You are now logged in as {}".format(login_session['username'])
    flash(output)
    return url_for('showProfile', musician_id=login_session['user_id'])


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data.decode()

    app_id = json.loads(open('{}fb_client_secrets.json'.format(
        document_root), 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('{}fb_client_secrets.json'.format(
        document_root), 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?'
    url += 'grant_type=fb_exchange_token'
    url += '&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    result = result.decode()

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v3.2/me"

    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v3.2/me'
    url += '?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result.decode())
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v3.2/me/picture?'
    url += 'access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result.decode())

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = "You are logged in as {}".format(login_session['username'])
    flash(output)
    return url_for('showProfile', musician_id=login_session['user_id'])


app.route('/gdisconnect')


def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token:

        url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
            login_session['access_token'])
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]

        if result['status'] == '200':
            response = make_response(json.dumps(
                'Successfully disconnected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response
        else:
            response = make_response(json.dumps(
                'Failed to revoke token for given user.', 400))
            response.headers['Content-Type'] = 'application/json'
            return response
    print('Access Token is None')
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/{}/permissions?access_token={}'.format(
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have successfully been logged out."


@app.route('/disconnect')
def disconnect(*args):
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        response = "You have successfully been logged out."
    else:
        response = "You have successfully been logged out."
    if len(args) == 0:
        flash(response)
    return response


@app.route('/')
def showIndex():
    with DBconn() as c:
        musicians = listMusicians(c, 0)
        result = listInstruments(c)
        title = ''
        return render_template(
            'start.html',
            title=title,
            result=result,
            musicians=musicians,
            instrument=0,
            CLIENT_ID=CLIENT_ID,
            STATE=makeState(),
            login_session=login_session)

# JSON endpoint for a start page


@app.route('/api/')
def indexJSON():
    with DBconn() as c:
        # Get all instruments with name and ID
        instruments = listInstruments(c)
        instrument_list = []
        for instrument in instruments:
            inst_data = {"name": instrument[0], "id": instrument[1]}
            # If there are musicians who play this instrument,
            # get their name and ID
            if instrument[2] > 0:
                musician_list = [{"name": name[0], "id": name[1]} for name in
                                 listMusicians(c, instrument[1])]
                inst_data.update(musicians=musician_list)
            instrument_list.append(inst_data)
        result = {"instruments": instrument_list}
    return jsonify(result)


@app.route('/instruments/<instrument>')
def showInstrument(instrument):
    with DBconn() as c:
        query = "SELECT name FROM instruments WHERE url = %s"
        c.execute(query, (instrument,))
        instr_name = c.fetchone()[0]
        musicians = listMusicians(c, instrument)
        title = "{} | ".format(instr_name)
        return render_template(
            'start.html',
            title=title,
            musicians=musicians,
            instrument=instr_name,
            CLIENT_ID=CLIENT_ID,
            STATE=makeState(),
            login_session=login_session)

# JSON endpoint for a specific instrument


@app.route('/api/instruments/<instrument>')
def instrumentJSON(instrument):
    with DBconn() as c:
        query = """SELECT m.name, m.url, m.picture, w.id, w.composer, w.title,
        w.duration, c.name, c.id
        FROM musicians m, works w, categories c
        WHERE w.instrument = %s AND w.creator = m.url AND c.id = w.category
        ORDER BY m.url, c.id, SPLIT_PART(w.composer, ' ', 2), w.title"""
        c.execute(query, (instrument,))
        data = c.fetchall()
        musicians_list = []
        mus_set = set()
        m = 0
        i = 0
        for d in data:
            # Starting a new musician
            if d[1] not in mus_set:
                # If this is not the first musician, add the repertoire
                if m != 0:
                    categories_list[c - 1].update(works=works)
                    musicians_list[m - 1].update(repertoire=categories_list)
                # Clear the categories and update the set of musicians
                cat_set = set()
                categories_list = []
                c = 0
                works = []
                mus_set.add(d[1])
                # Serialize the musician's data and put it into a list
                musicians_list.append({"name": d[0], "id": d[1],
                                       "picture": d[2]})
                m += 1
            # If this work belongs to a new category, add category to the list
            if d[8] not in cat_set:
                cat_set.add(d[8])
                categories_list.append({"name": d[7], "id": d[8]})
                # If this not the first category, add the previous one
                # to the list
                if c > 0:
                    categories_list[c - 1].update(works=works)
                    works = []
                c += 1
            # Add the current work to the category's work list
            works.append({"id": d[3], "composer": d[4], "title": d[5],
                          "duration": d[6]})
            # If this is the last work in the list, complete the categories
            # and add the repertoire to the musician's info
            if i == len(data) - 1:
                categories_list[c - 1].update(works=works)
                musicians_list[m - 1].update(repertoire=categories_list)
            i += 1

        return jsonify(musicians_list)


@app.route('/musicians/<musician_id>')
def showProfile(musician_id):
    with DBconn() as c:
        # Get profile data for the selected musician
        query = """SELECT name, picture, bio, email, public, tel, address
        FROM musicians WHERE url = %s"""
        c.execute(query, (musician_id,))
        personal_data = c.fetchone()
        # Get the repertoire list
        works = listRepertoire(c, musician_id)
        # works is a tuple. Te first element is the instrument list (string),
        # the second one is the repertoire list
        if works[0] != '':
            title = "{} - {} | ".format(personal_data[0], works[0])
        else:
            title = "{} | ".format(personal_data[0])
        return render_template(
            'profile.html',
            title=title,
            personal_data=personal_data,
            instruments=works[0],
            works=works[1],
            url=musician_id,
            CLIENT_ID=CLIENT_ID,
            STATE=makeState(),
            login_session=login_session)

# JSON endpoint for musician profile


@app.route('/api/musicians/<musician_id>')
def profileJSON(musician_id):
    with DBconn() as c:
        # Get profile data for the selected musician
        query = """SELECT name, picture, bio, email, public, tel, address
        FROM musicians WHERE url = %s"""
        c.execute(query, (musician_id,))
        data = c.fetchone()
        # Do not show email address if it is set private
        if data[4] == 0:
            email = 'private'
        else:
            email = data[3]
        # Create base dictionary for JSON response
        response = {"name": data[0], "id": musician_id, "picture": data[1],
                    "email": email, "phone": data[5], "address": data[6],
                    "biography": data[2]}
        # Get repertoire
        rep_list = listRepertoire(c, musician_id)
        # Make a list of instruments from the first element
        instruments = rep_list[0].split(', ')
        # Create the repertoire list from the second one, sorted in categories
        instrument_list = []
        inst_set = set()
        m = 0
        i = 0
        for d in rep_list[1]:
            # Starting a new instrument
            if d[7] not in inst_set:
                # If this is not the first musician, add the repertoire
                if m != 0:
                    categories_list[c - 1].update(works=works)
                    instrument_list[m - 1].update(repertoire=categories_list)
                # Clear the categories and update the set of musicians
                cat_set = set()
                categories_list = []
                c = 0
                works = []
                inst_set.add(d[7])
                # Serialize the musician's data and put it into a list
                instrument_list.append({"name": d[4], "id": d[7]})
                m += 1
            # If this work belongs to a new category, add category to the list
            if d[6] not in cat_set:
                cat_set.add(d[6])
                categories_list.append({"name": d[5], "id": d[6]})
                # If this not the first category, add the previous one
                # to the list
                if c > 0:
                    categories_list[c - 1].update(works=works)
                    works = []
                c += 1
            # Add the current work to the category's work list
            works.append({"id": d[0], "composer": d[1], "title": d[2],
                          "duration": d[3]})
            # If this is the last work in the list, complete the categories
            # and add the repertoire to the musician's info
            if i == len(rep_list[1]) - 1:
                categories_list[c - 1].update(works=works)
                instrument_list[m - 1].update(repertoire=categories_list)
            i += 1

        repertoire = instrument_list
        response.update(instruments=instruments, repertoire=repertoire)
        return jsonify(response)

# Create edit forms with stored data


@app.route('/infotoedit', methods=['POST'])
def createForm():
    # Fill edit form with stored data
    what = request.args.get('what')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            if what == 'bio':
                with DBconn() as c:
                    query = """SELECT bio FROM musicians WHERE url = %s"""
                    c.execute(query, (login_session['user_id'],))
                    bio = c.fetchone()
                    if bio[0]:
                        response.append(bio[0])
                    else:
                        response.append('')
            elif what == 'contact':
                with DBconn() as c:
                    query = """SELECT tel,address FROM musicians
                    WHERE url = %s"""
                    c.execute(query, (login_session['user_id'],))
                    response.append(c.fetchone())
            elif what == 'add_work':
                # Let's create the form to add new works to the repertoire!
                # Search data for the form
                with DBconn() as c:
                    instruments = ''
                    categories = ''
                    query = """SELECT i.url, COUNT(*) AS num
                    FROM instruments i, works w, musicians m
                    WHERE  m.url = %s AND m.url = w.creator
                    AND w.instrument = i.url
                    GROUP BY i.url
                    ORDER BY num DESC"""
                    c.execute(query, (login_session['user_id'],))
                    main_instrument = c.fetchone()
                    # Get options for selects: first get all instruments
                    # and create <option> tags
                    query = "SELECT url, name FROM instruments ORDER BY rank"
                    c.execute(query)
                    for instrument in c.fetchall():
                        try:
                            if instrument[0] == main_instrument[0]:
                                selected = ' selected="selected"'
                            else:
                                selected = ''
                        except TypeError:
                            selected = ''
                        instruments += '<option value='
                        instruments += '"{}"{}>{}</option>\n'.format(
                            instrument[0], selected, instrument[1])
                    # Then get all categories created by the user
                    query = """SELECT id, name FROM categories
                    WHERE creator = %s"""
                    c.execute(query, (login_session['user_id'],))
                    result = c.fetchall()
                    # If no such category found, create input field for a new
                    # one
                    if len(result) == 0:
                        categories = '''<strong>Create Category: </strong>
                        <br />
                        <input type="text" name="category" value="" />'''
                    else:
                        # If there are already categories created by the user,
                        # create a select for them
                        categories = '''<strong>Category: </strong><br />
                        <select id="category">\n'''
                        for category in result:
                            categories += '''<option value="{}">{}</option>
                            \n'''.format(category[0], category[1])
                        categories += '''</select> '''
                        categories += '''<button class="add long" '''
                        categories += '''type="button" onclick="replacePart'''
                        categories += '''('cat_selector',0,0,0)">'''
                        categories += '''+ New category</button>'''
                    # Create form from template and append it to the AJAX
                    # response
                    html_text = render_template(
                        'addform.html',
                        instruments=instruments,
                        categories=categories,
                        login_session=login_session)
                    response.append(html_text)
            # If it's a category, get the ID by slicing the string:
            elif what[0:2] == 'c_':
                category = what[2:]
                # Get category name and add to the AJAX response
                with DBconn() as c:
                    query = "SELECT name FROM categories WHERE id = %s"
                    c.execute(query, (category,))
                    name = c.fetchone()
                    response.append(name[0])
            # If it's an instrument, get the ID by slicing the string:
            elif what[0:2] == 'i_':
                instrument = what[2:]
                # Get category name and add to the AJAX response
                with DBconn() as c:
                    query = "SELECT name FROM instruments WHERE url = %s"
                    c.execute(query, (instrument,))
                    name = c.fetchone()
                    response.append(name[0])
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Edit informations


@app.route('/edit', methods=['POST'])
def editInfo():
    action = request.args.get('action')
    what = request.args.get('what')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            if what == 'bio':
                # Edit biography if not cancelling
                if action != 'cancel':
                    # If it is the user's own bio, store it in the DB
                    text = request.args.get('text')
                    with DBconn() as c:
                        query = """UPDATE musicians
                        SET bio = %s
                        WHERE url = %s"""
                        c.execute(query, (text, login_session['user_id']))

                # Replace form with the stored bio
                with DBconn() as c:
                    query = """SELECT bio FROM musicians WHERE url = %s"""
                    c.execute(query, (login_session['user_id'],))
                    bio = c.fetchone()
                    if bio[0]:
                        response.append(nl2br(bio[0]))
                    else:
                        response.append('')

            elif what == 'contact':
                if action != 'cancel':
                    # Edit contact info if not cancelling
                    # If it is the user's own info, store it in the DB
                    phone = request.args.get('phone')
                    address = request.args.get('address')
                    with DBconn() as c:
                        query = """UPDATE musicians SET tel = %s, address = %s
                        WHERE url = %s"""
                        c.execute(query,
                                  (phone, address, login_session['user_id']))

                # Replace form with the stored contact info
                with DBconn() as c:
                    query = """SELECT tel,address FROM musicians
                    WHERE url = %s"""
                    c.execute(query, (login_session['user_id'],))
                    response.append(c.fetchone())

            elif what == 'email_privacy':
                with DBconn() as c:
                    # Check if email address is public
                    query = """SELECT public FROM musicians WHERE url = %s"""
                    c.execute(query, (login_session['user_id'],))
                    if c.fetchone()[0] == 0:
                        # If private, set it public and change button text
                        public = 1
                        button_text = "Set Private"
                    else:
                        # If public, set it private and change button text
                        public = 0
                        button_text = "Set Public"
                    query = """UPDATE musicians SET public = %s
                    WHERE url = %s"""
                    # Update email privacy in DB and return new button text
                    c.execute(query, (public, login_session['user_id']))
                    response.append(button_text)
            # If it's a category, get the ID by slicing the string:
            elif what[0:2] == 'c_':
                category = what[2:]
                name = request.args.get('name')
                with DBconn() as c:
                    if action != 'cancel':
                        # Update category name in DB
                        query = "UPDATE categories SET name = %s WHERE id = %s"
                        c.execute(query, (name, category))
                    works = listRepertoire(c, user)
                    html_text = render_template(
                        'repertoire.html',
                        works=works[1],
                        url=user,
                        login_session=login_session)
                    response_data = (works[0], html_text)
                    response.append(response_data)
            # If it's a instrument, get the ID by slicing the string:
            elif what[0:2] == 'i_':
                old_url = what[2:]
                name = request.args.get('name')
                with DBconn() as c:
                    # Define an error code for the cases when it is not
                    # permitted to change the instrument's name
                    err_code = 0
                    if action != 'cancel':
                        # Create new ID from name
                        new_url = slugify(name)
                        # Check if the new and the old ID are identical
                        num = 0
                        if new_url != old_url:
                            # If not, check if an instrument exists
                            # with the new ID
                            query = """SELECT COUNT(*) FROM instruments
                            WHERE url = %s"""
                            c.execute(query, (new_url,))
                            existing_instrument = c.fetchone()
                            num = existing_instrument[0]
                        if num == 0:
                            # Check if someone else lists the instrument
                            # in their repertoire
                            query = """SELECT COUNT (*) FROM works
                            WHERE instrument = %s AND creator != %s"""
                            c.execute(query, (old_url, user))
                            other_users = c.fetchone()
                            # Update instrument in DB only if no other user
                            # found
                            if other_users[0] == 0:
                                # Check if there is a repertoire entry at all
                                # and get instrument's place in the list
                                query = """SELECT COUNT(w.id), i.rank
                                FROM works w, instruments i
                                WHERE w.instrument = %s
                                AND i.url = w.instrument
                                GROUP BY w.instrument,i.rank"""
                                c.execute(query, (old_url,))
                                inst_result = c. fetchone()
                                # If there are works in the repertoire with
                                # this instrument, prevent IntegrityError
                                # caused by existing foreign key constraint
                                # by creating a new instrument, updating the
                                # works and deleting the old one
                                if inst_result[0] > 0:
                                    query = """INSERT INTO instruments
                                    (url,name,rank,creator)
                                    VALUES (%s,%s,%s,%s)"""
                                    c.execute(query, (new_url, name,
                                                      inst_result[1], user))
                                    query = """UPDATE works
                                    SET instrument = %s
                                    WHERE instrument = %s"""
                                    c.execute(query, (new_url, old_url))
                                    query = """DELETE FROM instruments
                                    WHERE url = %s AND creator = %s"""
                                    c.execute(query, (old_url, user))
                                # If no foreign key constraint present,
                                # just update the instrument
                                else:
                                    query = """UPDATE instruments
                                    SET url = %s, name = %s
                                    WHERE url = %s AND creator = %s"""
                                    c.execute(query,
                                              (new_url, name, old_url, user))
                            else:
                                err_code = 2
                        else:
                            err_code = 1
                    result = listInstruments(c)
                    html_text = render_template(
                        'instruments.html',
                        result=result, login_session=login_session)
                    response.append((html_text, err_code))
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Add work to repertoire


@app.route('/add_work', methods=['POST'])
def addWork():
    composer = request.args.get('composer')
    title = request.args.get('title')
    duration = request.args.get('duration')
    instrument = request.args.get('instrument')
    category = request.args.get('category')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Check if instrument exists or new instrument should be added
                # If it already exists, the argument 'instrument' will be the
                # slugified name and the next query will find it
                query = 'SELECT COUNT(*) FROM instruments WHERE url = %s'
                c.execute(query, (instrument,))
                num = c.fetchone()[0]
                if num == 0:
                    # If the instrument is not found in the DB, create a new
                    # entry for it. In this case the argument 'instrument' is
                    # a normal name. We have to slugify it for the instrument
                    # idand assign a rank to it
                    query = 'SELECT MAX(rank) FROM instruments'
                    c.execute(query)
                    rank = c.fetchone()[0] + 1
                    query = '''INSERT INTO instruments (url,name,rank,creator)
                    VALUES (%s,%s,%s,%s)'''
                    url = slugify(instrument)
                    c.execute(query, (url, instrument, rank, user))
                else:
                    # If found, use the instrument variable as instrument id
                    # for further queries
                    url = instrument
                # If the category variable is numeric, it is already in the DB,
                # the variable contains the category ID.
                # If not, create a new category in the database.
                if not category.isnumeric():
                    query = '''INSERT INTO categories (name,creator)
                    VALUES (%s,%s)'''
                    c.execute(query, (category, user))
                    # After inserting, use the ID of the new record as category
                    # ID
                    query = 'SELECT id FROM categories WHERE name = %s'
                    c.execute(query, (category,))
                    category = c.fetchone()[0]
                # If no work ID passed, a new work must be added to the DB
                if not request.args.get('work'):
                    # Create the new Work entry using all data.
                    query = '''INSERT INTO
                    works (composer,title,duration,instrument,creator,category)
                    VALUES (%s,%s,%s,%s,%s,%s)'''
                    c.execute(
                        query,
                        (composer, title, duration, url, user, category))
                # If there is a work ID, update an existing work
                else:
                    work = request.args.get('work')
                    query = '''UPDATE works
                    SET composer = %s, title = %s, duration = %s,
                    instrument = %s, creator = %s, category = %s
                    WHERE id = %s'''
                    c.execute(
                        query,
                        (composer, title, duration, url, user, category, work))
                # Finally generate the repertoire list with the new element
                works = listRepertoire(c, user)
                html_text = render_template(
                    'repertoire.html',
                    works=works[1],
                    url=user,
                    login_session=login_session)
                response_data = (works[0], html_text)
                response.append(response_data)
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Delete work from repertoire


@app.route('/del_work', methods=['POST'])
def delWork():
    work = request.args.get('work')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Delete work from the repertoire by its ID
                query = 'DELETE FROM works WHERE id = %s'
                c.execute(query, (work,))
                # Finally generate the repertoire list with the new element
                works = listRepertoire(c, user)
                html_text = render_template(
                    'repertoire.html',
                    works=works[1],
                    url=user,
                    login_session=login_session)
                response_data = (works[0], html_text)
                response.append(response_data)
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Create form to edit work in repertoire


@app.route('/worktoedit', methods=['POST'])
def workToEdit():
    work = request.args.get('work')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Get the selected work's data to fill out the form
                query = '''SELECT w.composer, w.title, w.duration,
                i.url, c.id FROM works w, instruments i, categories c
                WHERE w.id = %s AND i.url = w.instrument
                AND w.category = c.id'''
                c.execute(query, (work,))
                work_data = c.fetchone()
                # Define variables for dropdown lists
                instruments = ''
                categories = ''
                # Get options for selects: first get all instruments
                # and create <option> tags.
                # Mark the work's instrument as selected.
                query = "SELECT url, name FROM instruments ORDER BY rank"
                c.execute(query)
                for instrument in c.fetchall():
                    if instrument[0] == work_data[3]:
                        selected = ' selected="selected"'
                    else:
                        selected = ''
                    instruments += '<option value="{}"{}>{}</option>\n'.format(
                        instrument[0], selected, instrument[1])
                # Then get all categories created by the user
                query = """SELECT id, name FROM categories
                WHERE creator = %s"""
                c.execute(query, (login_session['user_id'],))
                result = c.fetchall()
                # and create a dropdown list from them.
                # Mark the work's category as selected.
                categories = '''<strong>Category: </strong><br />
                <select id="category">\n'''
                for category in result:
                    if category[0] == work_data[4]:
                        selected = ' selected="selected"'
                    else:
                        selected = ''
                    categories += '''<option value="{}"{}>{}</option>
                    \n'''.format(category[0], selected, category[1])
                categories += '''</select> '''
                categories += '''<button class="add long" type="button" '''
                categories += '''onclick="replacePart'''
                categories += '''('cat_selector',0,0,0)">'''
                categories += '''+ New category</button>'''
                # Create form from template and append it to the AJAX response
                html_text = render_template(
                    'editform.html',
                    work=work,
                    instruments=instruments,
                    categories=categories,
                    work_data=work_data,
                    login_session=login_session)
                response.append(html_text)
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Delete category


@app.route('/del_cat', methods=['POST'])
def delCat():
    category = request.args.get('category')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Delete all works from repertoire with this category ID
                query = 'DELETE FROM works WHERE category = %s'
                c.execute(query, (category,))
                # Delete the category itself
                query = 'DELETE FROM categories WHERE id = %s'
                c.execute(query, (category,))
                # Finally generate the repertoire list with the new element
                works = listRepertoire(c, user)
                html_text = render_template(
                    'repertoire.html',
                    works=works[1],
                    url=user,
                    login_session=login_session)
                response_data = (works[0], html_text)
                response.append(response_data)
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Delete instrument


@app.route('/del_instr', methods=['POST'])
def delInstr():
    instrument = request.args.get('instrument')
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Check if there are works with this instrument in repertoires
                query = "SELECT COUNT(*) FROM works WHERE instrument = %s"
                c.execute(query, (instrument,))
                num = c.fetchone()
                print(num[0])
                # If nothing found, delete the instrument
                if num[0] == 0:
                    query = "DELETE FROM instruments WHERE url = %s"
                    c.execute(query, (instrument,))
                # Reload the instrument list
                result = listInstruments(c)
                html_text = render_template('instruments.html', result=result,
                                            login_session=login_session)
                response.append(html_text)
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)

# Delete user profile


@app.route('/del_profile', methods=['POST'])
def delProfile():
    user = request.args.get('id')
    response = []
    # If the user logged in is the owner of the profile, the first part of the
    # response will be 1, otherwise 0. The second part will contain the data.
    if 'user_id' in login_session:
        if user == login_session['user_id']:
            response.append(1)
            with DBconn() as c:
                # Delete all works from repertoire with this user ID
                query = 'DELETE FROM works WHERE creator = %s'
                c.execute(query, (user,))
                # Delete categories created by the user
                query = 'DELETE FROM categories WHERE creator = %s'
                c.execute(query, (user,))
                # Delete the creator field from instruments created by the user
                query = """UPDATE instruments SET creator = ''
                WHERE creator = %s"""
                c.execute(query, (user,))
                # Delete the profile itself
                query = 'DELETE FROM musicians WHERE url = %s'
                c.execute(query, (user,))
                disconnect(1)
                response.append(1)
                flash("Profile successfully deleted!")
        else:
            response.append(0)
            flash("You are not authorized to perform this operation!")
    else:
        response.append(0)
        flash("You are not logged in!")
    return json.dumps(response)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
