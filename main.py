# main.py
import os
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, make_response, \
    send_from_directory, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
import io
from bson import ObjectId
from bson.binary import Binary
import base64
import mimetypes

app = Flask(__name__, static_url_path='', static_folder='uploads')
app.secret_key = "your_secret_key" 
login_manager = LoginManager()
login_manager.init_app(app)

client = MongoClient('mongodb://localhost:27017/')
db = client['social']
collection = db['newpost']
users_collection = db['users']
comment_collection = db['comments']  

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class User(UserMixin):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def get_id(self):
        return self.username


@login_manager.user_loader
def load_user(username):
    user_data = users_collection.find_one({'username': username})
    if user_data:
        return User(user_data['username'], user_data['password'])
    return None


@app.route('/index')
def index():
    posts = collection.find()
    all_posts = []
    for post in posts:
        comments = []
        for comment in comment_collection.find({'post_id': str(post['_id'])}):
            user_data = users_collection.find_one({'username': comment['user_name']})
            if user_data:
                comment['user_name'] = user_data['username']  
             
                comments.append(comment)
        post['comments'] = comments
        all_posts.append(post)

        user = users_collection.find_one({'username': current_user.username})
    return render_template('post.html', posts=all_posts, user=current_user)


@app.route('/search', methods=['POST'])
@login_required
def search():
    username = request.form['search_input']
    print("Search Query:", username)  # Add this line to check if the search query is reaching the server
    if username:
        user = users_collection.find_one({'username': username})
        print("User:", user)  # Add this line to check if the user is being retrieved correctly
        if user:
            posts = collection.find({'author': username})
            filtered_posts = []
            for post in posts:
                comments = []
                for comment in comment_collection.find({'post_id': str(post['_id'])}):
                    user_data = users_collection.find_one({'username': comment['user_name']})
                    if user_data:
                        comment['user_name'] = user_data['username']
                        comments.append(comment)
                post['comments'] = comments
                filtered_posts.append(post)
            print("Filtered Posts:", filtered_posts)  # Add this line to check if the filtered posts are correct
            return render_template('post.html', posts=filtered_posts, user=current_user)
        else:
            flash("User not found")
            return render_template('post.html', posts=[], user=current_user)
    else:
        flash("No username provided")
        return redirect(url_for('index'))


@app.route('/')
def register_form():
    return render_template('register.html')


@app.route('/profile/<username>')
def profile(username):
    user = users_collection.find_one({'username': username})
    if user:
        # Access the image data from the nested structure and decode it
        image_data = user.get('image', '')  # Assuming image is stored as string
        user['image'] = image_data
        return render_template('profile.html', user=user)
    else:
        return "User not found."


@app.route('/user/<username>')
def user_profile(username):
    user = users_collection.find_one({'username': username})
    if user:
        # Retrieve posts authored by the user
        posts = collection.find({'author': username})

        user_info = {
            'username': user['username'],
            'email': user['email'], 
           
        }
        return render_template('visit.html', user=user_info, posts=posts)
    else:
        flash("User not found")
        return redirect(url_for('index'))


@app.route('/edit_profile_photo', methods=['POST'])
@login_required
def edit_profile_photo():
    if 'new_photo' in request.files:
        new_photo = request.files['new_photo']
        if new_photo.filename != '':
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_photo.filename)
            new_photo.save(image_path)
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            image_data = encoded_string
            # Update the user's profile photo in the database
            users_collection.update_one({'username': current_user.username}, {'$set': {'image': image_data}})
            flash('Profile photo updated successfully!', 'success')
        else:
            flash('No photo uploaded!', 'error')
    else:
        flash('No photo uploaded!', 'error')
    return redirect(url_for('profile', username=current_user.username))

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    existing_user = users_collection.find_one({'username': username})
    if existing_user:
        return jsonify({'error': 'Username already exists'})

    if 'image' in request.files:
        image = request.files['image']
        if image.filename != '':
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(image_path)
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            image_data = encoded_string
        else:
            image_data = None
    else:
        image_data = None

    user_data = {
        'username': username,
        'email': email,
        'password': password,
        'image': image_data
    }

    user_id = users_collection.insert_one(user_data).inserted_id

    # Redirect to login page after successful registration
    return redirect(url_for('login'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = users_collection.find_one({'username': username, 'password': password})
        if user_data:
            user = User(username, user_data['password'])  # Change _id to username
            login_user(user)
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Invalid username or password'})
    return render_template('post_login.html')


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success') #flash message

    # Prevent caching of the page by setting cache control headers
    response = make_response(redirect(url_for('login')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response


@app.route('/add_post', methods=['POST'])
@login_required
def add_post():
    post_content = request.form['post_content']
    post_image = request.files['post_image']
    if post_image:
        image_data = post_image.read()
        post = {'content': post_content, 'image': image_data, 'author': current_user.username, 'comments': []}
        collection.insert_one(post)
        return jsonify({'message': 'Post added successfully!'})
    else:
        return jsonify({'error': 'No image uploaded!'})


@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    data = request.json
    post_id = data['postId']
    content = data['content']
    comment = {'post_id': post_id, 'user_name': current_user.username, 'content': content}
    comment_id = comment_collection.insert_one(comment).inserted_id
    return jsonify({'success': True, 'userName': current_user.username, 'commentId': str(comment_id)})


@app.route('/image/<post_id>')
def get_image(post_id):
    post = collection.find_one({'_id': ObjectId(post_id)})
    if post and 'image' in post:
        return send_file(io.BytesIO(post['image']),
                         mimetype='image',
                         as_attachment=False)
    else:
        return 'Image not found'


@app.route('/user_image/<username>')
def get_user_image(username):
  
    user_data = users_collection.find_one({'username': username})
    if user_data and 'image' in user_data:
        image_data = user_data['image']
        # Return the image data as a response with the appropriate mimetype
        return send_file(io.BytesIO(base64.b64decode(image_data)),
                         mimetype='image/jpeg')
    else:
        # If user data or image not found, return the default image from the static folder
        default_image_path = os.path.join(app.static_folder, 'pp.jpg')
        return send_file(default_image_path, mimetype='image/jpeg')


@app.route('/like_comment', methods=['POST'])
def like_comment():
    data = request.json
    comment_id = data.get('commentId')  # Get the comment ID from the request data


    comment = comment_collection.find_one_and_update(
        {'_id': ObjectId(comment_id)},
        {'$inc': {'likes': 1}}, 
        return_document=True
    )

    if comment:
        # Return a success response
        return jsonify({'success': True})
    else:
        # Return an error response if the comment is not found
        return jsonify({'success': False, 'error': 'Comment not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
