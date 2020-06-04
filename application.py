import os
import requests

from flask import Flask, session, request, render_template, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)

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


@app.route("/", methods=["GET", "POST"])
def index():

    # Check if user exists and password matches
    if request.method == 'POST':
        user_name = request.form.get("username")
        password = request.form.get("password")

        # Check for empty input fields
        if not user_name:
            return render_template('error.html', message='Please enter a username.')
        if not password:
            return render_template('error.html', message='Please enter a password.')           

        if db.execute("SELECT * FROM users WHERE username LIKE :username", {"username":user_name}).rowcount < 1:
            return render_template('error.html', message='Username not found.')
        if db.execute("SELECT * FROM users WHERE password LIKE :password", {"password":password}).rowcount < 1:
            return render_template('error.html', message='Password incorrect.')

        name_fetch = db.execute("SELECT * FROM users WHERE username = :username", {"username": user_name}).fetchone()
        session["user_name"] = name_fetch.username

        # Takes user to search page
        return render_template('search.html')            

    return render_template('index.html')

@app.route("/register") 
def register():
    return render_template('register.html')

@app.route("/create", methods=["GET", "POST"])  
def create():

    if request.method == 'POST':       

        # Check if user exists
        user = request.form.get("user-name")
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": user}).rowcount > 0:
            return render_template('error.html', message='User already exists.')
    
        # Create new user
        user_name = request.form.get("user-name")
        password = request.form.get("password")

        if not user_name:
            return render_template('error.html', message='Please enter a username.')
        if not password:
            return render_template('error.html', message='Please enter a password.')           
    
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": user_name, "password": password})
        db.commit()

        return render_template('success.html')

@app.route("/search", methods=["GET", "POST"])
def search():

    if request.method == "GET":

        return render_template('search.html')
    
    if request.method == "POST":

        query = request.form.get("search")

        query = "%"+query+"%"
        
        result = db.execute("SELECT * FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search OR year LIKE :search", {"search":query}).fetchall() 
        
    return render_template('search.html', result=result)

@app.route("/book/<isbn>", methods=["GET", "POST"])
def book(isbn):

    if request.method == "GET":

        # Get information on book
        book_info = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn", {"isbn": isbn})
        book_id = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        session["book_id"] = book_id.isbn

        # Get Goodreads data
        good_reads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "NVlsKWe7lx1wXlcROWxQQ", "isbns": isbn})
        good_reads = good_reads.json()
        avg_rating = good_reads['books'][0]['average_rating']
        review_count = good_reads['books'][0]['work_ratings_count']

        # Get information on existing reviews
        review_data = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": session["book_id"]})
        
        return render_template('book.html', book_info=book_info, review_data=review_data, avg_rating=avg_rating, review_count=review_count)

@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):

    # Get book data from database
    book_data = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book_data is None:
        return jsonify ({"error": "Invalid isbn"}), 422

    # Get book data from Goodreads
    good_reads = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "NVlsKWe7lx1wXlcROWxQQ", "isbns": isbn})
    good_reads = good_reads.json()
    avg_rating = good_reads['books'][0]['average_rating']
    review_count = good_reads['books'][0]['work_ratings_count']

    # Serves JSON response
    return jsonify({
        "title": book_data.title,
        "author": book_data.author,
        "year": book_data.year,
        "isbn": book_data.isbn,
        "review_count": review_count,
        "average_score": avg_rating
    })    

@app.route("/review", methods=["POST"])
def review():
       
    # Check if user has already made a review 
    if db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn", {"username": session["user_name"], "isbn": session["book_id"]}).rowcount < 1:

        # Get review data from form
        rating = request.form.get("rating")    
        review_text = request.form.get("review-text")
        isbn = session["book_id"]

        # Add review to database
        db.execute("INSERT INTO reviews (rating, review, isbn, username) VALUES (:rating, :review, :isbn, :username)", {"rating": rating, "review": review_text, "isbn": session["book_id"], "username": session["user_name"]})
        db.commit()
        
        return render_template('result.html', isbn=isbn, message="Success! Your Review has been submitted.")       

    else:
        isbn = session["book_id"]
        return render_template('result.html', isbn=isbn, message="You have already submitted a review.")    

@app.route("/logout")
def logout():

    # Forget session id
    session.pop('user_name')

    return render_template('logout.html')        