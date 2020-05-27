import os

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
        user_name = request.form.get("user-name")
        password = request.form.get("password")
        if db.execute("SELECT * FROM users WHERE username = :username", {"username":user_name}).rowcount == 0:
            return render_template('error.html', message='Username not found.')
        if db.execute("SELECT password FROM users WHERE username = :username", {"username":user_name}) != password:
            return render_template('error.html', message='Password incorrect.')

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

@app.route("/search")
def search():
    
    return render_template('search.html')




