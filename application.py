import os
import requests

from flask import Flask, session, render_template, request, flash, url_for, jsonify
from flask_session import Session
from pip._vendor import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.utils import redirect

app = Flask(__name__)
# key key: N0xLf5XzDxR3CZjAzHpK7g

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


#@app.route("/")
#def func():
#   return "PROJECT1- Book Review Website"


@app.route("/register", methods=["POST", "GET"])
def register():
    # Register new user
    if request.method == "POST":
        name = request.form.get("user")
        passwrd = request.form.get("pass")

        if db.execute("SELECT * FROM users where username= :name", {"name": name}).rowcount == 1:
            return render_template("register_error.html", error_message="Username taken.")

        db.execute("INSERT INTO users(username,password) VALUES(:name ,:passwrd)", {"name": name, "passwrd": passwrd})
        db.commit()
        flash('Successfully Registered. Please Log in!')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route("/login", methods=["POST", "GET"])
def index():
    # Login
    session.clear()
    if request.method == "POST":
        name = request.form.get("user")
        passwrd = request.form.get("pass")

        if db.execute("SELECT * FROM users where username= :name AND password = :passwrd",
                      {"name": name, "passwrd": passwrd}).rowcount == 0:
            return render_template("login_error.html", error_message="Username/Password is Invalid.")
        session["loggedin_user"] = name
        flash('Successfully Logged in')
        return redirect(url_for('book'))

    return render_template('index.html')


@app.route("/booksearch")
def book():
    return render_template('booksearch.html')


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("username", None)
    return redirect(url_for('index'))


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        isbn = "%" + request.form.get("isbn") + "%"
        title = "%" + request.form.get("title") + "%"
        author = "%" + request.form.get("author") + "%"

        if len(author) > 2:
            a = db.execute("SELECT num, title FROM books WHERE lower(author) LIKE lower (:a)"
                           , {"a": author}).fetchall()
            if len(a) == 0:
                return render_template("error.html", error_message="No Such Author Found ")

            return render_template("result.html", res=a)


        elif len(title) > 2:
            t = db.execute("SELECT num, title FROM books WHERE lower(title) LIKE lower (:ti)"
                           , {"ti": title}).fetchall()
            if len(t) == 0:
                return render_template("error.html", error_message="No Such Title Found ")

            return render_template("result.html", res=t)

        elif len(isbn) > 2:
            isn = db.execute("SELECT num, title FROM books WHERE num LIKE (:i)"
                             , {"i": isbn}).fetchall()
            if len(isn) == 0:
                return render_template("error.html", error_message="No Such ISBN Found")

            return render_template("result.html", res=isn)


        else:
            return render_template('booksearch.html')


@app.route("/result", methods=["POST", "GET"])
def result():
    return render_template('result.html')


@app.route("/review/<book_id>/", methods=["POST", "GET"])
def review(book_id):
    book_details = db.execute("SELECT num,title,author,year FROM books where num =:id", {"id": book_id}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "N0xLf5XzDxR3CZjAzHpK7g", "isbns": book_id})
    avg_rating = res.json()['books'][0]['average_rating']
    rating_count = res.json()['books'][0]['work_ratings_count']
    review = db.execute("SELECT username, review FROM b_review WHERE isbn = :isb", {"isb": book_id}).fetchall()

    return render_template("review.html", b_d=book_details, reviews=review, avg=avg_rating, work=rating_count)


@app.route("/reviewsubmit/<string:book_id>", methods=["GET", "POST"])
def reviewsubmit(book_id):
    rev = request.form.get("writereview")
    rating = request.form.get("rate")
    current_user = session["loggedin_user"]

    if db.execute("SELECT isbn FROM b_review WHERE isbn= :id AND username =:u",
                  {"id": book_id, "u": current_user}).rowcount > 0:
        return render_template("error.html", error_message="You have already submitted review for this book")

    else:
        db.execute("INSERT INTO b_review (isbn, username,review,rating) VALUES (:isbn, :name, :rev, :rating)",
                   {"isbn": book_id, "name": current_user, "rev": rev, "rating": rating})
        db.commit()
        return render_template('booksearch.html')


@app.route("/api/<string:isbn>")
def api(isbn):
    jsonobj = {"title": "", "author": "", "year": 0, "isbn": isbn, "review_count": 0, "average_score": 0.0}

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "N0xLf5XzDxR3CZjAzHpK7g", "isbns": isbn})

    jsonobj["average_score"] = res.json()['books'][0]['average_rating']
    jsonobj["review_count"] = res.json()['books'][0]['work_ratings_count']

    data = db.execute("SELECT title, author, year FROM books WHERE num = :isbn", {"isbn": isbn}).fetchone()
    jsonobj["title"] = data.title
    jsonobj["author"] = data.author
    jsonobj["year"] = data.year

    return jsonify(jsonobj)
