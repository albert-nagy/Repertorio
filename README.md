# Repertorio

## Description

Repertorio is a web app where musicians can sign up and show their repertoire list along with their biography and contact info.
This app was created for Udacity's Full Stack Web Developer nanodegree's Items Catalog project.
It is a complex catalog system, where the users' data (works in their repertoire) is sorted into user-defined categories (genre and instruments) and the users themselves are categorized according to the instruments they list in their repertoire.

## Skills used to complete this project

- Python
- Flask
- Jinja2
- PostgreSQL
- AJAX
- JavaScript
- HTML
- CSS
- OAuth
- Google & Facebook Sign In

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

## Further possible developments

- Handle a large number of musicians: group them into blocks according to their initials
- Make it possible for a user to change the order of their categories in repertoire
- Add administrator role to make predefined instruments editable
- Change JavaScript alerts for more sophisticated alerting
- Change pop-up windows of third-party authentication for embedded auth windows
- Hide email addresses from spambots
- Polish design