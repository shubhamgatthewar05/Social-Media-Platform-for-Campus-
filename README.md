# Social-Media-Platform-for-Campus-



# Campus Social Media Website

This project is a social media website for campus use, built using Flask, MongoDB, and Bootstrap. It allows users to register, log in, post content, comment on posts, and manage their profile photos.

## Features

- User Registration and Login
- Posting Content with Images
- Commenting on Posts
- Liking Comments
- Profile Management with Photo Upload
- Search for Users and Posts

## Requirements

- Python 3.8+
- Flask
- Flask-Login
- pymongo
- bson
- Bootstrap (included in templates)

## Installation

### Clone the Repository

Download or clone the repository to your local machine.

```bash
git clone <repository_url>
cd campus-social-media
```

### Set Up the Virtual Environment

Create a virtual environment to manage dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### Install Dependencies

Install the required Python packages:

```bash
pip install flask flask-login pymongo
```

### Set Up MongoDB

Make sure MongoDB is installed and running on your machine. You can download and install MongoDB from [here](https://www.mongodb.com/try/download/community).

Create the necessary database and collections:

1. Connect to the MongoDB server:

    ```bash
    mongo
    ```

2. Create the database and collections:

    ```javascript
    use social
    db.createCollection("newpost")
    db.createCollection("users")
    db.createCollection("comments")
    ```

### Configure the Application

Set your secret key and MongoDB URI in the `main.py` file:

```python
app.secret_key = "your_secret_key"
client = MongoClient('mongodb://localhost:27017/')
```

You can change `your_secret_key` to any random string of your choice.

### Upload Folder

Ensure that the `uploads` folder exists:

```bash
mkdir uploads
```

## Running the Application

Run the Flask application:

```bash
python main.py
```

The application will be available at `http://127.0.0.1:5000`.

## Usage

1. Open the registration page at `http://127.0.0.1:5000/` and create a new account.
2. Log in with your credentials.
3. Use the navigation bar to add posts, comment on posts, and manage your profile.
4. Search for users and view their profiles and posts.

## Project Structure

```
campus-social-media/
│
├── main.py
├── uploads/
│   ├── (uploaded images)
├── templates/
│   ├── base.html
│   ├── register.html
│   ├── post.html
│   ├── profile.html
│   ├── visit.html
│   ├── post_login.html
├── static/
│   ├── pp.jpg (default profile picture)
```

- `main.py`: The main application file containing routes and logic.
- `uploads/`: Directory for storing uploaded images.
- `templates/`: HTML templates for rendering web pages.
- `static/`: Directory for static files such as the default profile picture.

## Contributing

Feel free to make suggestions or improvements to the project. For major changes, please open an issue first to discuss what you would like to change.


This `README.md` should cover the basics of your project and help others set it up and use it effectively.
