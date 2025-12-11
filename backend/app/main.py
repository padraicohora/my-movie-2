from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from app.movies.tmdb_client import make_tmdb_request
import pprint
import json

app = FastAPI()

# connect to SQLite 
conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()

# create Tables
# user table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    username TEXT UNIQUE
)
""")

# ratings table
cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    rating REAL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# movies table
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    release_date TEXT,
    overview TEXT
)
""")

# commit changes to database
conn.commit()

# Pydantic models
class User(BaseModel):
    username: str

class Rating(BaseModel):
    user_id: int
    movie_id: int
    rating: float


url = "/movie/now_playing?language=en-US&page=1"

response = make_tmdb_request(url)
data = response.json()


for movie in data['results']:
    cursor.execute(
        "INSERT OR IGNORE INTO movies (id, title, release_date, overview) VALUES (?, ?, ?, ?)", 
        (movie["id"], movie["title"], movie["release_date"], movie["overview"])
    )

conn.commit()  # Commit all inserts at once

# API endpoints
@app.post("/users/")
def create_user(user: User):
    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (user.username,))
        conn.commit()
        return {
            "message": "User created successfully", 
            "id": cursor.lastrowid,
            "username": user.username
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.get("/users/{user_id}")
def get_user(user_id: int):
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user[0], 
        "username": user[1]
    }

@app.post("/ratings")
def add_rating(rating: Rating):
    cursor.execute(
        "INSERT INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)",
        (rating.user_id, rating.movie_id, rating.rating)
    )
    conn.commit()
    return {
        "message": "Rating added successfully", 
        "status":"success", 
        "rating_id": cursor.lastrowid
    }

@app.get("/ratings/{user_id}")
def get_ratings(user_id: int):
    cursor.execute("SELECT movie_id, rating FROM ratings WHERE user_id=?", (user_id,))
    ratings = cursor.fetchall()
    if not ratings:
        raise HTTPException(status_code=404, detail="No ratings found for this user")
    return {
        "user_id": user_id, 
        "ratings": [{
            "movie_id": r[0], 
            "rating": r[1]
            } for r in ratings]
    }

@app.get("/movies/")
def get_movies():
    cursor.execute("SELECT id, title, release_date, overview FROM movies")
    movies = cursor.fetchall()
    return [{
        "id": m[0],
        "title": m[1],
        "release_date": m[2],
        "overview": m[3]
    } for m in movies]

movies = get_movies()

print(json.dumps(movies, indent=2))