from flask import Flask, request, jsonify
from flask_cors import CORS
import os 
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


app = Flask(__name__)
CORS(app)
load_dotenv()
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 10800
jwt = JWTManager(app)
mongo = PyMongo(app)
users = mongo.db.users
post = mongo.db.posts

if mongo.cx.server_info():
    print("Successfully connected to MongoDB!")
else:
    print("Failed to connect to MongoDB.")

@app.route("/")
def main():
    return "<p>Hello, World</p>"

# Create user and add to data store
@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    user = {
        "username": username, 
        "email": email, 
        "password":generate_password_hash(password)
        }
    
    result = users.insert_one(user)
    new_user_id = str(result.inserted_id)

    return jsonify({"id": new_user_id}), 201

# Login - check if password and email are correct
@app.route("/api/users/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid password"}), 401
     
    return jsonify({"success": "Logged in successfully!"})
    
    # access_token = create_access_token(identity=email)
    # return jsonify(access_token=access_token)

@app.route("/api/posts/create", methods=["POST"])
# @jwt_required()
def create_post():
        data = request.get_json()
        title = data.get("title")
        body = data.get("body")
        date = data.get("date")
        is_public = data.get("isPublic")

        # current_user_email = get_jwt_identity()
        # current_user = users.find_one({"email": current_user_email})

        post = {
            "title": title, 
            "body": body, 
            "date": date, 
            # "user_id": current_user["_id"],
            "is_public": is_public
            }
        
        result = mongo.db.posts.insert_one(post)

        if result.inserted_id:
         return jsonify({"id": str(result.inserted_id)})

        return jsonify({"error": "Failed to create post."})

@app.route("/api/posts/public", methods=["GET"])
def get_public_posts():
    public_posts = mongo.db.posts.find({"is_public": True})
    posts = []
    for post in public_posts:
        post["_id"] = str(post["_id"])
        posts.append(post)
    return jsonify(posts)



if __name__ == "__main__":
    app.run()