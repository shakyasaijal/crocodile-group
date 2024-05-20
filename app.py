from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import config

# Create flask app
app = Flask(__name__)

# Load all config files
app.config.from_object(config)

# Create MongoDB Client
client = MongoClient(app.config['MONGO_URI'])

# Database Name
db = client['notes_db']

# Collections
users_collection = db['users']
notes_collection = db['notes']

# Initialize Login Manager from Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


# Custom unauthorized handler
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("You must be logged in to access this page.", "error")
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(str(user["_id"]), user["username"])
    return None


# Function for registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Search if username already exists
        user = users_collection.find_one({"username": username})
        if user:
            flash("You already have an account. Please login.", "error")
            return redirect(url_for('login'))
        else:
            # Encrypt Password
            hashed_password = generate_password_hash(password)

            # Inserting in mongodb
            users_collection.insert_one({"username": username, "password": hashed_password})
            flash('Registration successful. Please log in.', "success")
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Search user with username
        user = users_collection.find_one({"username": username})

        # Validate Password
        if user and check_password_hash(user['password'], password):
            login_user(User(str(user['_id']), user['username']))
            flash("You are logged in successfully.", "success")
            return redirect(url_for('index'))
        flash('Invalid username or password.', "error")
    return render_template('login.html')


# Logout user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    # Get all data based on user id
    notes = notes_collection.find({"user_id": current_user.id})
    return render_template('Crud/notes.html', notes=notes)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        # Get tags from the form and convert it to an array
        tags = request.form.get('tags', '').split(',')
        current_time = datetime.now()
        post = {
            'user_id': current_user.id,
            'title': title,
            'content': content,
            'tags': tags,
            'created_at': current_time,
            'updated_at': current_time
            }
        
        # insert into mongodb
        notes_collection.insert_one(post)
        flash("New note has been created successfully.", "success")
        return redirect(url_for('index'))
    return render_template('Crud/create.html')


@app.route('/view/<post_id>')
@login_required
def view_post(post_id):
    # Get post from user id and object id
    notes = notes_collection.find_one({"_id": ObjectId(post_id), "user_id": current_user.id})
    if not notes:
        return redirect(url_for('index'))
    return render_template('Crud/view_note.html', notes=notes)


@app.route('/edit/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_note(post_id):
    # Find post first
    post = notes_collection.find_one({"_id": ObjectId(post_id), "user_id": current_user.id})
    if not post:
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Get all data from update form
        title = request.form['title']
        content = request.form['content']
        tags = request.form.get('tags', '').split(',')
        current_time = datetime.now()

        # Update the note using object id
        notes_collection.update_one({'_id': ObjectId(post_id)}, {'$set': {'title': title, 'content': content, 'tags': tags, 'updated_at': current_time}})
        flash(f"{title} has been successfully updated.", "success")
        return redirect(url_for('index'))

    return render_template('Crud/edit_note.html', post=post)


# Deleting a note
@app.route('/delete/<post_id>')
@login_required
def delete_note(post_id):
    notes_collection.delete_one({'_id': ObjectId(post_id), "user_id": current_user.id})
    flash("Note has been successfully deleted.", "success")
    return redirect(url_for('index'))


@app.route('/search', methods=['POST'])
@login_required
def search():
    if request.method == 'POST':
        # get tags from search field
        search_tag = request.form['search']

        # match tags using regular expression
        notes = notes_collection.find({'tags': {'$regex': search_tag, '$options': 'i'}})
        return render_template('search_results.html', notes=notes, search_name=request.form['search'])
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
