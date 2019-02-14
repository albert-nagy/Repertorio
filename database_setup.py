import psycopg2
import csv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from slugify import slugify

# Substitute 'vagrant' in next line with the name of your default database
DEFAULT_DB = 'vagrant'
# This will be the name of the new database:
dbname = 'rep_catalog'


def setupDB(db, c):
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
    instruments = [
        'Violin',
        'Viola',
        'Cello',
        'Double Bass',
        'Harp',
        'Flute',
        'Oboe',
        'Clarinet',
        'Bassoon',
        'Horn',
        'Trumpet',
        'Trombone',
        'Tuba',
        'Timpani',
        'Percussion',
        'Piano',
        'Conductor']

    i = 1
    for instrument in instruments:
        data = (slugify(instrument), instrument, i)
        query = "INSERT INTO instruments (url,name,rank) VALUES (%s,%s,%s)"
        c.execute(query, data)
        i += 1
    db.commit()

    query = "SELECT COUNT(*) FROM instruments"
    c.execute(query)
    result = c.fetchone()
    return result[0]


def fillPresetData(db, c):
    with open('musicians.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            c.execute("""INSERT INTO musicians
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", row)

    with open('categories.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            c.execute("INSERT INTO categories (name,creator) VALUES (%s, %s)",
                      (row[1], row[2]))

    with open('works.csv', 'r') as f:
        reader = csv.reader(f)
        cat_ids = set()
        i = 0
        for row in reader:
            if row[6] not in cat_ids:
                i += 1
                cat_ids.add(row[6])
            query = """INSERT INTO works (composer,title,
            duration,instrument,creator,category)
            VALUES (%s, %s, %s, %s, %s, %s)"""
            c.execute(query,
                      (row[1], row[2], row[3], row[4], row[5], i))
    db.commit()

    result = []

    query = "SELECT COUNT(*) FROM musicians"
    c.execute(query)
    result.append(c.fetchone()[0])
    query = "SELECT COUNT(*) FROM categories"
    c.execute(query)
    result.append(c.fetchone()[0])
    query = "SELECT COUNT(*) FROM works"
    c.execute(query)
    result.append(c.fetchone()[0])
    return result


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
num = setupDB(db, c)

num_csv = fillPresetData(db, c)
print("{} instruments, {} musicians, {} categories and {} works added".format(
    num, num_csv[0], num_csv[1], num_csv[2]))
db.close()
