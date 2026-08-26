import os
import random
import sqlite3
import requests
from flask import Flask, Response, g, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, loginRequired

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = os.path.join(os.path.dirname(__file__), "main.db") 

"""Control parameters"""
MAX_WRONG = 6
SYNOPSIS_AT = 3
IMAGE_AT = 5
API_TRIES = 10
TOP = 100
"""------------------"""

JIKAN_URL = "https://api.jikan.moe/v4/top/anime"
KITSU_URL = "https://kitsu.io/api/edge/anime"


def animeWord(title: str) -> str:
    """Convert the anime title to a word suitable for the hangman game."""
    newChars = []

    title_upper = title.upper()
    
    #keep A-Z letters and spaces only
    for char in title_upper:
        if "A" <= char <= "Z":
            newChars.append(char)
        else:
            newChars.append(" ")
            
    newString = "".join(newChars)

    return " ".join(newString.split())

def animeDetails(title: str, image_url: str, synopsis: str) -> dict:
    """Return a dictionary containing the anime details."""
    return {
        "title": title,
        "word": animeWord(title),
        "image_url": image_url,
        "synopsis": synopsis or "",
    }


def maskCapitalizedWords(synopsis: str) -> str:
    """Turns each capitalized word in the description to dashes to prevent showing the answer"""
    words = synopsis.split(" ")
    masked_words = []

    for word in words:
        # Check if the word starts with a capital letter
        if word and word[0].isupper():
            masked_words.append("-" * len(word))
        else:
            masked_words.append(word)

    return " ".join(masked_words)


def loadAnime() -> list:
    """Load a random anime from the Jikan or Kitsu API incase one fails"""
    headers = {"User-Agent": "AnimeHangman/1.0", "Accept": "application/json"}
    try:
        response = requests.get(JIKAN_URL, params={"limit": 1}, headers=headers, timeout=5)
        response.raise_for_status()
        total = TOP #or response.json()["pagination"]["items"]["total"]
        for _ in range(API_TRIES):
            number = random.randint(1, total)
            response = requests.get(
                JIKAN_URL,
                params={"page": number, "limit": 1},
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            a = response.json().get("data", [{}])[0]
            title = a.get("title_english")
            image_url = a.get("images", {}).get("jpg", {}).get("image_url")
            word = animeWord(title or "")
            if title and image_url and len(word) >= 4:
                return [animeDetails(title, image_url, a.get("synopsis"))]
            
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass

    try:
        kitsu_headers = {"User-Agent": "AnimeHangman/1.0", "Accept": "application/vnd.api+json"}
        response = requests.get(
            KITSU_URL,
            params={"page[limit]": 1, "sort": "-userCount"},
            headers=kitsu_headers,
            timeout=5,
        )
        response.raise_for_status()
        total = TOP #or response.json()["meta"]["count"]
        for _ in range(API_TRIES):
            number = random.randint(1, total)
            response = requests.get(
                KITSU_URL,
                params={
                    "page[limit]": 1,
                    "page[offset]": number - 1,
                    "sort": "-userCount",
                },
                headers=kitsu_headers,
                timeout=5,
            )
            response.raise_for_status()
            a = response.json().get("data", [{}])[0].get("attributes", {})
            title = a.get("titles", {}).get("en")
            image = a.get("posterImage") or {}
            image_url = image.get("large") or image.get("original")
            word = animeWord(title or "")
            if title and image_url and len(word) >= 4:
                return [animeDetails(title, image_url, a.get("synopsis"))]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass

    return apology("Failed to load anime catalog. Please try again later.", 500)




def getDb() -> sqlite3.Connection:
    """Get a database connection, creating the scores table if it doesn't exist."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            """
            CREATE TABLE IF NOT EXISTS hangman_scores (
                user_id INTEGER PRIMARY KEY,
                score INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        g.db.commit()
    return g.db

@app.teardown_appcontext
def closeDb(error: Exception):
    """Close the database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.after_request
def afterRequest(response: Response):
    """Doesn't cache responses so they cant go back to the previous page after logout"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

""" MAIN FLASK APPLICATION ROUTES """

@app.route("/")
def home() -> Response:
    """Redirects to login if not logged in, otherwise redirects to hangman game."""
    if session.get("user_id") is None:
        return redirect("/login")
    return redirect("/hangman")

@app.route("/login", methods=["GET", "POST"])
def login() -> Response:
    """Log user in"""
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    if not username:
        return apology("must provide username", 403)
    if not password:
        return apology("must provide password", 403)

    rows = getDb().execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchall()
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        return apology("invalid username or password", 403)

    session["user_id"] = rows[0]["id"]
    return redirect("/hangman")


@app.route("/logout")
def logout() -> Response:
    """Log user out"""
    session.clear()
    return redirect("/")


@app.route("/hangman", methods=["GET", "POST"])
@loginRequired
def hangman() -> Response:
    """Main hangman game route"""
    db = getDb()
    user_id = session["user_id"]
    db.execute("INSERT OR IGNORE INTO hangman_scores (user_id) VALUES (?)", (user_id,))
    db.commit()

    if request.method == "POST" and request.form.get("action") == "new":
        session.pop("hangman", None)

    game = session.get("hangman")
    if not game or not game.get("image_url"):
        anime = loadAnime()[0]
        game = {
            "title": anime["title"],
            "word": animeWord(anime["title"]),
            "image_url": anime["image_url"],
            "synopsis": anime.get("synopsis", ""),
            "guessed": [],
            "wrong": 0,
            "status": "playing",
        }
    else:
        game["word"] = animeWord(game["title"])

    game.setdefault("synopsis", "")

    message = None
    if request.method == "POST" and request.form.get("action") == "guess":
        letter = request.form.get("letter", "").strip().upper()
        if game["status"] != "playing":
            message = "Start a new round to keep playing."
        elif len(letter) != 1 or not letter.isalpha():
            message = "Enter one letter."
        elif letter in game["guessed"]:
            message = "You already guessed that letter."
        else:
            game["guessed"].append(letter)
            if letter not in game["word"]:
                game["wrong"] += 1
                message = "That letter is not in the title."
            if all(
                character == " " or character in game["guessed"]
                for character in game["word"]
            ):
                game["status"] = "won"
                db.execute(
                    "UPDATE hangman_scores SET score = score + 1 WHERE user_id = ?",
                    (user_id,),
                )
                db.commit()
                message = "You guessed the anime title!"
            elif game["wrong"] >= MAX_WRONG:
                game["status"] = "lost"
                message = f"The title was {game['word']}."

    session["hangman"] = game
    score = db.execute("SELECT score FROM hangman_scores WHERE user_id = ?", (user_id,)).fetchone()["score"]
    wordReveal = []

    for character in game["word"]:
        # Always reveal spaces
        if character == " ":
            wordReveal.append(" ")
        # Reveal character if already guessed
        elif character in game["guessed"]:
            wordReveal.append(character)
        # Reveal full word if player lost
        elif game["status"] == "lost":
            wordReveal.append(character)
        # Hide un-guessed characters
        else:
            wordReveal.append("_")

        displayedWord = "".join(wordReveal)

    return render_template(
        "hangman.html",
        displayed_word=displayedWord,
        guessed=sorted(game["guessed"]),
        wrong=game["wrong"],
        max_wrong=MAX_WRONG,
        image_threshold=IMAGE_AT,
        synopsis_threshold=SYNOPSIS_AT,
        guess_count=len(game["guessed"]),
        image_url=game["image_url"],
        synopsis=(
            game["synopsis"]
            if game["status"] != "playing"
            else maskCapitalizedWords(game["synopsis"])
        ),
        title=game["title"],
        status=game["status"],
        message=message,
        score=score,
    )

@app.route("/register", methods=["GET", "POST"])
def register() -> Response:
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    if not username:
        return apology("No Username")
    if not password:
        return apology("No Password")
    if not confirmation:
        return apology("No confirmation password")
    if password != confirmation:
        return apology("Passwords do not match!")

    try:
        db = getDb()
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return apology("Username exists")
    return redirect("/login")

if __name__ == '__main__':
    app.run(debug=True)