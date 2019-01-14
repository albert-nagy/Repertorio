import psycopg2
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

app = Flask(__name__)

dbname = 'rep_catalog'

@app.route('/')
def showIndex():
	db = psycopg2.connect(dbname=dbname)
	c = db.cursor()
	query = "SELECT name, url FROM instruments ORDER BY rank"
	c.execute(query)
	result = c.fetchall()
	db.close()
	return render_template('start.html', result=result)




if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)