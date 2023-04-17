from flask import Flask, request, jsonify
import os 
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from markupsafe import escape
from pymongo import MongoClient

app = Flask(__name__)
load_dotenv()
app.config["MONGO_URI"] = os.environ.get("MONGODB_URI")
mongo = PyMongo(app)

users = mongo.db.users

if mongo.cx.server_info():
    print("Successfully connected to MongoDB!")
else:
    print("Failed to connect to MongoDB.")

@app.route("/")
def main():
    return "<p>Hello, World</p>"

@app.route("/holidays") #route "/" -> hello_world()
def hello_world():
    return "<p>Hello, Holidays!</p>"

@app.route('/hello')
def hello():
    return '{ name: "simon, age: 88}'

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'User {escape(username)}'

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    # Validate input
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    # Create user and add to data store
    user = {'name': name, 'email': email}
    result = users.insert_one(user)
    new_user_id = str(result.inserted_id)

    return jsonify({'id': new_user_id}), 201

if __name__ == "__main__":
    app.run()