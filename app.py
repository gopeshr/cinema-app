from flask import Flask, render_template, request, g, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='styles')

DATABASE = 'films.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_request
def initialize_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_name TEXT NOT NULL,
            release_year INTEGER,
            watched_time TEXT,
            rating REAL,
            review TEXT
        )
    ''')
    db.commit()
    cursor.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        film_name = request.form['film_name']
        release_year = request.form['release_year']
        
        new_watched_time = request.form.get('new_watched_time').replace('T', ' ')
        watched_time = new_watched_time or datetime.now().replace(second=0).strftime("%Y-%m-%d %H:%M")
        
        rating = request.form['rating']
        review = request.form['review']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO films (film_name, release_year, watched_time, rating, review) VALUES (?, ?, ?, ?, ?)",
                       (film_name, release_year, watched_time, rating, review))
        db.commit()
        #flash('Film loaded successfully!')
        cursor.close()

    return render_template('index.html')

@app.route('/edit/<int:film_id>', methods=['GET', 'POST'])
def edit(film_id):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        film_name = request.form['film_name']
        release_year = request.form['release_year']
        watched_time = request.form['watched_time']
        rating = request.form['rating']
        review = request.form['review']

        cursor.execute('''
            UPDATE films
            SET film_name=?, release_year=?, watched_time=?, rating=?, review=?
            WHERE id=?
        ''', (film_name, release_year, watched_time, rating, review, film_id))
        db.commit()
        cursor.close()
        return redirect(url_for('saved_list'))

    cursor.execute("SELECT * FROM films WHERE id=?", (film_id,))
    film = cursor.fetchone()
    cursor.close()

    return render_template('edit.html', film=film)

@app.route('/delete/<int:film_id>', methods=['GET'])
def delete(film_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM films WHERE id=?", (film_id,))
    db.commit()
    cursor.close()

    return redirect(url_for('saved_list'))

@app.route('/film/<int:film_id>')
def film_details(film_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM films WHERE id=?", (film_id,))
    film = cursor.fetchone()
    cursor.close()

    return render_template('film_details.html', film=film)

@app.route('/saved_list', methods=['GET', 'POST'])
def saved_list():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        # Fetch filter criteria from the form
        film_name = request.form.get('film_name')
        release_year = request.form.get('release_year')
        watched_year = request.form.get('watched_year')
        rating_operator = request.form.get('rating_operator')
        rating_value = request.form.get('rating_value')

        # Build the SQL query based on the provided filter criteria
        query = "SELECT * FROM films WHERE 1=1"
        params = []

        if film_name:
            query += " AND LOWER(film_name) LIKE ?"
            params.append(f'%{film_name.lower()}%')
        
        if release_year:
            query += " AND release_year = ?"
            params.append(release_year)

        if watched_year:
            query += " AND strftime('%Y', watched_time) = ?"
            params.append(watched_year)        

        if rating_value is not None:
            if rating_operator == '!':
                query += " AND (rating = '' OR rating IS NULL)"
            else:
                try:
                    rating_value = float(rating_value)
                    if rating_operator == '>':
                        query += " AND rating > ? AND rating <> '' AND rating IS NOT NULL"
                    elif rating_operator == '<':
                        query += " AND rating < ? AND rating <> '' AND rating IS NOT NULL"
                    else:
                        query += " AND rating = ?"
                    params.append(rating_value)
                except ValueError:
                    pass




        cursor.execute(query, tuple(params))
        films = cursor.fetchall()
    else:
        # If no filters are applied, fetch all films
        cursor.execute("SELECT * FROM films")
        films = cursor.fetchall()

    cursor.close()
    return render_template('saved_list.html', films=films)


if __name__ == '__main__':
    app.run(debug=True)
