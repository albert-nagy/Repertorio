import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from slugify import slugify

# Substitute 'vagrant' in next line with the name of your default database
DEFAULT_DB = 'vagrant'
#This will be the name of the new database:
dbname = 'rep_catalog'

def setupDB(db,c):
	# Create tables
	c.execute("""CREATE TABLE musicians(url TEXT PRIMARY KEY, name TEXT,
	picture TEXT, bio TEXT, email TEXT, public INT, tel TEXT, address TEXT)""")

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

	i=1
	for instrument in instruments:
		data = (slugify(instrument), instrument, i)
		query = "INSERT INTO instruments (url,name,rank) VALUES (%s,%s,%s)"
		c.execute(query,data)
		i += 1
	db.commit()

	query = "SELECT COUNT(*) FROM instruments"
	c.execute(query)
	result = c.fetchone()
	return result[0]

# Check if database exists
try:
	db = psycopg2.connect(dbname=dbname) 
except psycopg2.OperationalError:
	# If not, create database
	db = psycopg2.connect(dbname=DEFAULT_DB)
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

