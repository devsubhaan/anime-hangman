# Anime Hangman
---

## 📝 Description
* This is a project made with Flask and Python.

### Brief Overview
* It uses two databases of animes to give a random selected anime from the top 100 animes (This can be changed in the code).
* After 3 guesses the description is given with parts dashed out with '-' (as they might give too much away about the anime).
* After 5 guesses the image of the anime is shown but blurred to make it easier to identify the anime.
* If you are unable to guess it in the amount of tries, the image is unblurred and the text is shown, you do not gain score from losing.
* There is a log-in system which holds a hashed password, username and the score of the account.
* Score increases when you successfully guess an anime.

---

## 🏗️ Structure
* There is a `templates` folder which holds every single page of the application: The login screen, register screen and the hangman screen.
* The `layout.html` file is used to add the same theme to every page, it uses Jinja.
* Flask is used in `app.py` to link the pages and redirect users. There's `/login`, `/register`, `/hangman` and `/logout`.
* `helpers.py` is used for the error messages that send you to an error page along with showing an error message and a gif which can be changed.
* Bootstrap is used to create the navigation bar which holds the play, login, register buttons or a logout button. This depends if the user is signed in or not.
* `requirements.txt` holds all the needed modules to run this.
* `main.db` is the database which holds the hashed passwords, usernames and the score of every user.
* The CSS is mainly used for the navigation bar, but also for the error message and gif.
* The gif error message can be changed by going to `apology.html` and swapping the url. Make sure to keep the `.gif` at the end or it will not work. This is only tested on Giphy.

---

## ⚙️ Sub-routines

Most of them are explained within the code but here is a breakdown:

### `animeWord()`
Converts the title into characters that can be guessed. For example if the title contained any character other than A-Z and a space it would be treated as a space and ignored. This makes those parts of the title actually guessable.

### `animeDetails()`
Converts the parameters into a dictionary. This is needed since to grab data like the anime title, it must be in dictionary format. It also makes it a lot more simple and readable than doing it in place.

### `maskCapitalizedWords()`
Converts capitalized words into dashes. Both of the APIs show a description of the anime but it can contain lots of info about it. 

This is an example of what a hidden description looks like (it makes it harder for it to give the answer):
![Hidden Description Example](image.png)

Now this is what it looks like when not hidden—it reveals a lot and sometimes some anime descriptions have the title in the name:
![Unhidden Description Example](image-1.png)

This is all to make it harder for the answer to get spoiled.

### `loadAnime()`
Uses Jikan or Kitsu to generate a random anime. To save resources it calculates a random number from the top X then searches for that top anime. This prevents unnecessary calls to the API.

Usually Jikan fails after a few responses so I added Kitsu along with it in case it crashes with a `TypeError`. All this function does is find that anime, gets the description (synopsis), title, and image, and passes it onto the `animeWord()` and `animeDetails()` sub-routines. In case of an error it returns an error message (`apology.html`).

### `getDb()`
Simply gets the sqlite3 database and returns the connection. If the database does not exist it creates a new one.

### `closeDb()`
Just closes the database connection. This is called when the program terminates via the decorator `@app.teardown_appcontext`.

### `afterRequest()`
Prevents going back to previous pages. If you log out then go back a page, it would make you log back in automatically which has security vulnerabilities.

*(The rest are the Flask pages which are self-explanatory).*