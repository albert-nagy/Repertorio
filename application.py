import psycopg2
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

from flask import session as login_session
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

CLIENT_ID = json.loads(
    open('google_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Repertorio App"

dbname = 'rep_catalog'

# Database connection for all methods using WITH
class DBconn:
	def __enter__(self):
		self.db = psycopg2.connect(dbname=dbname)
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
		query = "INSERT INTO musicians (url,name,email,picture,public) VALUES (%s,%s,%s,%s,%s)"
		c.execute(query,data)
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
        oauth_flow = flow_from_clientsecrets('google_secret.json', scope='')
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
        response = make_response(json.dumps('Current user is already connected.'), 200)
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

    output = "you are now logged in as {}".format(login_session['username'])
    flash(output)
    return output

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data.decode()
   
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    result = result.decode()
    
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v3.2/me"
    
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v3.2/me?access_token=%s&fields=name,id,email' % token
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
    url = 'https://graph.facebook.com/v3.2/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result.decode())

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = "Now logged in as {}".format(login_session['username'])
    flash(output)
    return output

app.route('/gdisconnect')
def gdisconnect():
	access_token = login_session.get('access_token')
	if access_token:	
	
		url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
		h = httplib2.Http()
		result = h.request(url, 'GET')[0]
		
		if result['status'] == '200':
			response = make_response(json.dumps('Successfully disconnected.'), 200)
			response.headers['Content-Type'] = 'application/json'
			return response
		else:
			response = make_response(json.dumps('Failed to revoke token for given user.', 400))
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
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/disconnect')
def disconnect():
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
    flash(response)
    return response

@app.route('/')
def showIndex():
	with DBconn() as c:
		query = "SELECT name, url FROM instruments ORDER BY rank"
		c.execute(query)
		result = c.fetchall()
		return render_template('start.html', result=result, STATE=makeState(),
			login_session=login_session)

@app.route('/musicians/<musician_id>')
def showProfile(musician_id):
	with DBconn() as c:
		query = """SELECT name, picture, bio, email, public, tel, address
		FROM musicians WHERE url = %s"""
		c.execute(query, (musician_id,))
		personal_data = c.fetchone()
		return render_template('profile.html', personal_data=personal_data,
			url=musician_id, STATE=makeState(), login_session=login_session)

@app.route('/infotoedit', methods=['POST'])
def createForm():
	# Fill edit form with stored data
	what = request.args.get('what')
	user = request.args.get('id')
	if user == login_session['user_id']:
		if what == 'bio':
			with DBconn() as c:
				query = """SELECT bio FROM musicians WHERE url = %s"""
				c.execute(query, (login_session['user_id'],))
				bio = c.fetchone()
				if bio[0]:
					return bio[0]
				return ''
		elif what == 'contact':
			with DBconn() as c:
				query = """SELECT tel,address FROM musicians WHERE url = %s"""
				c.execute(query, (login_session['user_id'],))
				contact_info = c.fetchone()
				return json.dumps(contact_info)

@app.route('/edit', methods=['POST'])
def editInfo():
	action = request.args.get('action')
	what = request.args.get('what')

	if what == 'bio':
		# Edit biography if not cancelling
		if action != 'cancel':
			user = request.args.get('id')
			# If it is the user's own bio, store it in the DB
			if user == login_session['user_id']:
				text = request.args.get('text')
				with DBconn() as c:
					query = """UPDATE musicians SET bio = %s WHERE url = %s"""
					c.execute(query, (text,login_session['user_id']))
		# Replace form with the stored bio 	
		with DBconn() as c:
			query = """SELECT bio FROM musicians WHERE url = %s"""
			c.execute(query, (login_session['user_id'],))
			bio = c.fetchone()
			if bio[0]:
				return nl2br(bio[0])
			return ''

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)