import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from slugify import slugify

dbname = 'rep_catalog'

def setupDB(db,c):
	# Create tables
	c.execute("""CREATE TABLE musicians(url TEXT PRIMARY KEY, name TEXT,
	bio TEXT, email TEXT, tel TEXT, address TEXT)""")

	c.execute("""CREATE TABLE instruments(url TEXT PRIMARY KEY, name TEXT,
	rank INT, creator TEXT)""")

	c.execute("""CREATE TABLE categories(id SERIAL PRIMARY KEY, name TEXT,
	creator TEXT REFERENCES musicians(url))""")

	c.execute("""CREATE TABLE works(id SERIAL PRIMARY KEY, composer TEXT,
	title TEXT, duration INT, instrument TEXT REFERENCES instruments(url),
	creator TEXT REFERENCES musicians(url),
	category INT REFERENCES categories(id))""")

	# Fill instruments table with some predefined instruments
	instruments = ['Violin','Viola','Cello', 'Double Bass', 'Harp', 'Flute',
	'Oboe',	'Clarinet', 'Bassoon', 'Horn', 'Trumpet', 'Trombone', 'Tuba',
	'Timpani', 'Percussion', 'Piano', 'Conductor']

	for instrument in instruments:
		data = (slugify(instrument), instrument)
		query = "INSERT INTO instruments (url,name) VALUES (%s,%s)"
		c.execute(query,data)
	db.commit()

	query = "SELECT COUNT(*) FROM instruments"
	c.execute(query)
	result = c.fetchone()
	return result[0]

# Check if database exists
try:
	db = psycopg2.connect(dbname=dbname)
	c = db.cursor()
	# If yes, populate it!
	setupDB(db,c)
	db.close()
except psycopg2.OperationalError:
	# If not, create database
	db = psycopg2.connect(dbname='vagrant')
	db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
	c = db.cursor()
	c.execute('CREATE DATABASE ' + dbname)
	db.commit()
	db.close()
	db = psycopg2.connect(dbname=dbname)
	c = db.cursor()
	# Populate new DB and report number of initial inserts
	num = setupDB(db,c)
	print("{} instruments added".format(num))
	db.close()

