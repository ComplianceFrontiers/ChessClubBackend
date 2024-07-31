from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1

app = Flask(__name__)
CORS(app)
load_dotenv()

# Get the MongoDB URI from the environment variable
mongo_uri = os.getenv('MONGO_URI')
# MongoDB setup
client = MongoClient(mongo_uri)
db = client.chessclub
users_collection = db.users

@app.route('/')
def home():
    return "Hello, Flask on Vercel!"

def time_now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/signup', methods=['POST'])
def signup():
    user_data = request.get_json()
    if user_data:
        parent_name = user_data.get('parentName')
        kidnames = [
            user_data.get('kidName1'),
            user_data.get('kidName2'),
            user_data.get('kidName3')
        ]
        email = user_data.get('email')
        phone = user_data.get('phone')
        
        # Check if email already exists
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'User already exists. Please login.'}), 400

        # Insert a record for each kid
        inserted_ids = []
        for kidname in kidnames:
            if kidname:
                new_user = {
                    'parentName': parent_name,
                    'kidName': kidname,
                    'email': email,
                    'phone':phone,
                 }
                result = users_collection.insert_one(new_user)
                inserted_ids.append(str(result.inserted_id))  # Convert ObjectId to string
        
        return jsonify({'success': True, 'insertedIds': inserted_ids}), 201
    else:
        return jsonify({'error': 'Invalid data format.'}), 400

@app.route('/signin', methods=['POST'])
def signin():
    user_data = request.get_json()
    if not user_data or 'email' not in user_data:
        return jsonify({'error': 'Email is required.'}), 400
    
    email = user_data.get('email')
    
    # Check if user exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        # Update the user's document with the current timestamp
        current_timestamp = datetime.now()
        formatted_timestamp = current_timestamp.isoformat()
        users_collection.update_one(
            {'email': email},
            {'$set': {'last_signin': formatted_timestamp}}
        )
        return jsonify({'success': True, 'message': 'Sign in successful.'}), 200
    else:
        return jsonify({'error': 'Email not registered. Please sign up.'}), 404
@app.route('/Club_users', methods=['GET'])
def get_users():
    try:
        # Fetch all records from the collection
        users = users_collection.find({}, {'_id': 0})  # Exclude the _id field
        # Convert MongoDB documents to a list of dictionaries
        users_list = list(users)
        return jsonify(users_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run()