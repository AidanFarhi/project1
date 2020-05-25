import os

from flask import Flask, session, request, render_template, url_for
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


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register") 
def register():
    return render_template('register.html')

@app.route("/create", methods=["GET", "POST"])  
def create():
    if request.method == 'POST':
        user_count = 0        
        # Check if user exists
        user = request.form.get("user-name")
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": user}) == user:
            return render_template('error.html', message='User already exists.')
    
        # Create new user
        user_name = request.form.get("user-name")
        password = request.form.get("password")
        user_count += 1
    
        db.execute("INSERT INTO users (id, username, password) VALUES (:id, :username, :password)", {"id": user_count, "username": user_name, "password": password})
        db.commit()

        return render_template('success.html')

@app.route("/search")
def search():
    pass




