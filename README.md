# Repertorio

## Description

Repertorio is a web app where musicians can sign up and show their repertoire list along with their biography and contact info.
This app is created for Udacity's Full Stack Web Developer nanodegree.

## Installation

The application  was created under Python 3.5. 
Install the Psycopg2-binary and Slugify modules, then run database_setup.py to create the required database with tables and some predefined data.

```bash
pip3 install psycopg2-binary python-slugify

python3 database_setup.py
```
Install flask and oauth2client modules, then run application.py to start server.

```bash
pip3 install flask oauth2client markdown

python3 application.py
```