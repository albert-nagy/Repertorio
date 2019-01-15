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

app = Flask(__name__)

# CLIENT_ID = json.loads(
#     open('client_secret_945722933121-lbkncbgj0sht96it5lnmhktbsns74l3s.apps.googleusercontent.com.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "Restaurant Menu Application"

dbname = 'rep_catalog'

state = ''

def makeState():
	if 'username' not in login_session:
		state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
		login_session['state'] = state

@app.route('/')
def showIndex():
	makeState()
	db = psycopg2.connect(dbname=dbname)
	c = db.cursor()
	query = "SELECT name, url FROM instruments ORDER BY rank"
	c.execute(query)
	result = c.fetchall()
	db.close()
	return render_template('start.html', result=result, STATE = state)




if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)