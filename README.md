# Repertor &bull; io

## Description

Repertor &bull; io is a web app where musicians can sign up and show their repertoire list along with their biography and contact info.
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

Create a database called 'catalog' with role 'catalog' and a custom password.
Create a Python file called 'dbpass.py' and add a variable called 'db_password' containing the password.

```bash
touch dbpass.py
```

```python
db_password = 'DATABASE_PASSWORD'
```
Install the Psycopg2-binary and Slugify modules, then run database_setup.py to create the required database with tables and some predefined data. The database setup will require the CSV files to populate the DB with demo data.

```bash
pip3 install psycopg2-binary python-slugify

python3 database_setup.py
```
Install flask, oauth2client and markdown modules, then run application.py to start server.

```bash
pip3 install flask oauth2client markdown

python3 application.py
```
## Usage

1. Access the start page at `http://localhost:8000/` 

2. Sign in using the Google / Facebook Sign In buttons at the top of the page to create your profile. After login you will get to your profile page where you can start to fill in your contact info and biography.

3. You can access your profile page anytime using the "My Profile" button at the top of the page.

4. Return to the start page by clicking on "Repertor &bull; io".

5. Using the "Add work to your repertoire" button, populate your repertoire, selecting or creating instruments and categories. Once you have works in your repertoire, your profile goes public: it will be accessible from the start and instrument pages.

6. Your profile will be associated with the instruments you list in your repertoire.

7. You may create, edit and delete works in your repertoire, assign them to a different instrument or a different category.

8. You may create, edit or delete your categories. In latter case all works associated with the deleted category will be deleted as well.

9. You may create a new instrument, edit it if no other user lists it in their repertoire and delete them if no repertoire entry is associated with it. You may edit or delete only those instruments you created. You can find the instrument Edit / Delete button on the start page.

10. Log out using the Logout button at the top of the page.

11. From your profile page you have the possibility to delete your whole profile together with all your categories and repertoire entries. The instruments you created will persist, but no longer associated with your deleted profile.

## HTML endpoints

`/`

The left pane on the start page lists all instruments in the database with the number of users listing them in their repertoire. If somebody plays the instrument, a link will point to the respective instrument page.
The right pane lists all musicians (users with a repertoire) with their picture, the instruments they play and a link to their profile page. 

`/instruments/<instrument>`

The page of a specific instrument lists all musicians who have works for this instrument with their picture and a link pointing to their profile page.

`/musicians/<musician_id>`

The profile page of a musician shows name, picture, contact info and biography of the user, and their repertoire below, sorted by instruments and categories. The profile owner can create, edit and modify their info from this page via AJAX calls.

## JSON endpoints

`/api/`

This endpoint lists all instruments with name and ID and the musicians who play them (name, ID).

`/api/instruments/<instrument>`

The JSON endpoint of a specific instrument lists all musicians who play it (id, name, profile picture) and their repertoire for this instrument, sorted by categories.

`/musicians/<musician_id>`

The JSON endpoint of a musician lists the user's all info with their repertoire, sorted by instruments and categories.

## Known issues

- Auto-incremented IDs in the table may cause problems on a possible backup

## Further possible developments

- Handle a large number of musicians: group them into blocks according to their initials, use columns to distribute them on the page
- Make it possible for a user to change the order of their categories in repertoire
- Make works and categories accessible and selectable for all users
- Add administrator role to make predefined instruments editable
- Change JavaScript alerts for more sophisticated alerting
- Change pop-up windows of third-party authentication for embedded auth windows
- Hide email addresses from spambots
- Extend form validation
- Responsive design