from flask import Flask, request, jsonify
from flask_cors import CORS
import os 
from flask_pymongo import PyMongo
from bson import ObjectId
import bson
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app)
load_dotenv()
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 10800
jwt = JWTManager(app)

# MongoDB Database
# PyMongo - MongoDB driver for synchronous Python app
mongo = PyMongo(app)
users = mongo.db.users
dreams = mongo.db.dreams

# Check connection
if mongo.cx.server_info():
    print("Successfully connected to MongoDB!")
else:
    print("Failed to connect to MongoDB.")

# Create user 
@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    #PyMongo use dictionaries to represent documents
    user = {
        "username": username, 
        "email": email, 
        "password":generate_password_hash(password)
        }
    
    result = users.insert_one(user)
    new_user_id = str(result.inserted_id)

    return jsonify({"id": new_user_id}), 201

# Login 
@app.route("/api/users/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    # username = data.get("username")
    password = data.get("password")

    user = users.find_one({"email": email})
    # user = users.find_one({"username": username})
    if not user:
        return jsonify({"error": "Invalid username"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid password"}), 401
    
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)   

# Create Post
@app.route("/api/posts/create", methods=["POST"])
@jwt_required()
def create_post():
        data = request.get_json()
        title = data.get("title")
        body = data.get("body")
        type = data.get("type")
        quality = data.get("quality")
        date = data.get("date")
        is_public = data.get("isPublic")

        # Identify the user that created the post 
        current_user_email = get_jwt_identity()
        current_user = users.find_one({"email": current_user_email})

        post = {
            "title": title, 
            "body": body, 
            "type": type,
            "quality": quality,
            "date": date, 
            # Add created user ID and email to Dream collection
            "user": {"_id": current_user["_id"], "email": current_user["email"]},
            "is_public": is_public
            }
        
        result = dreams.insert_one(post)

        if result.inserted_id:
         response = ({"id": str(result.inserted_id)})
         return jsonify(response)

        return jsonify({"error": "Failed to create post."})

# Show public post
@app.route("/api/posts/public", methods=["GET"])
def get_public_posts():

    # Exclude user and comments field from the result 
    public_posts = dreams.find({"is_public": True}, {"user": 0, "comments": 0}) \
                        .sort("date", -1)
    posts = []
    for post in public_posts:
        post["_id"] = str(post["_id"])
        posts.append(post)
    return jsonify(posts)

# View all posts
@app.route("/api/posts", methods=["GET"])
@jwt_required()
def get_user_posts():
  
    current_user_email = get_jwt_identity()
    user_dreams = dreams.find({"user.email": current_user_email}, {"comments": 0}).sort("date", -1)

    # Loop through Dream and append them to the list
    all_dreams = []
    for dream in user_dreams:
        dream["_id"] = str(dream["_id"])
        dream["user"]["_id"] = str(dream["user"]["_id"])
        all_dreams.append(dream)
    return jsonify(all_dreams)

# Read a specific post
@app.route("/api/posts/<id>", methods=["GET"])
@jwt_required()
def show_post(id):

    # print(f"ID value: {id}")
    # Projection - exclude user and comments
    post = dreams.find_one({"_id": ObjectId(id)}, {"user": 0, "comments": 0})
    # print(f"Post value: {post}")
    if post:
        post["_id"] = str(post["_id"])
        # remove user object
        # post.pop("user", None)
        return jsonify (post)
    else:
        return jsonify({"message": "Post not found"})
    
# Update post
@app.route("/api/posts/<id>", methods=["PUT"])
@jwt_required()
def edit_post(id):

    json = request.json
    post = dreams.find_one({"_id": ObjectId(id)})
    if post:
        post["title"] = json.get("title", post["title"])
        post["body"] = json.get("body", post["body"])
        post["type"] = json.get("type", post["type"])
        post["quality"] = json.get("quality", post["quality"])
        post["date"] = json.get("date", post["date"])
        post["is_public"] = json.get("is_public", post["is_public"])

        # MongoDB update operator
        dreams.update_one({"_id": ObjectId(id)}, {"$set": post})
        post["_id"] = str(post["_id"])
        post.pop("user", None)
        return jsonify(post)
    else:
        return jsonify({"message": "Post not found"})

# Delete post
@app.route("/api/posts/<id>", methods=["DELETE"])
def delete_post(id):

    result = dreams.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return jsonify({"success": "Post deleted successfully."})
    else:
        return jsonify({"error": "Failed to delete post."})
    
# Add comment
@app.route("/api/posts/<id>/comments", methods=["POST"])
@jwt_required()
def create_comment(id):
        data = request.get_json()
        comment = data.get("comment")

        current_user_email = get_jwt_identity()
        current_user = users.find_one({"email": current_user_email})

        # Find the dream by its ID and update its comments field
        result = dreams.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"comments": {"comment": comment, "user": current_user["email"]}}}
    )

        if result.modified_count:
            response = {"id": str(id)}
            return jsonify(response)

        return jsonify({"error": "Failed to create comment."})

# View all comments 
@app.route("/api/posts/<id>/comments", methods=["GET"])
def view_comments(id):
    post = dreams.find_one({"_id": ObjectId(id)})
    if post:
        comments = post.get("comments", [])
        return jsonify(comments)
    return jsonify({"error": "Post not found."})

@app.route("/api/dreams", methods=["GET"])
@jwt_required()
def get_dreams_data():
    
    current_user_email = get_jwt_identity()
    user_dreams = list(dreams.find({"user.email": current_user_email}))
    total_dreams = len(list(user_dreams))
    return jsonify({"totalDreams": total_dreams})

if __name__ == "__main__":
    app.run()