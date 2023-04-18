from flask import Flask, request, jsonify
from flask_cors import CORS
import os 
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

from flask_jwt_extended import create_access_token
# from flask_jwt_extended import get_jwt_identity
# from flask_jwt_extended import jwt_required
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
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    user = {"name": name, "email": email, "password":generate_password_hash(password)}
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
        return jsonify({"error": "Invalid email or password"})

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"})
    
    access_token = create_access_token(identity=email)
    return jsonify(access_token=access_token)

if __name__ == "__main__":
    app.run()