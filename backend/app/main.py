from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# connect to SQLite 
conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()

# create Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    username TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    movie_id INTEGER,
    rating REAL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY,
    title TEXT,
    release_date TEXT,
    overview TEXT
)
""")

conn.commit()

# Pydantic models
class User(BaseModel):
    username: str

class Rating(BaseModel):
    user_id: int
    movie_id: int
    rating: float


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