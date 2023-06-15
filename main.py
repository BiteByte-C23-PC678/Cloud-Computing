from flask import Flask, request, jsonify
import mysql.connector
import jwt
from google.cloud import storage
import os
import time
import numpy as np
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import pandas as pd

app = Flask(__name__)

# MySQL connection configuration
connection = mysql.connector.connect(
    host="34.101.225.147",
    user="bitebyte",
    password="coolgamer501",
    database="bitebyte"
)

# Connect to MySQL
if connection.is_connected():
    print('Connected to MySQL database.')
else:
    print('Error connecting to MySQL.')

# Google Cloud Storage configuration
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "keyfile.json"
storage_client = storage.Client()
bucket_name = "bitebytes.appspot.com"
bucket = storage_client.get_bucket(bucket_name)

# API endpoint for user registration
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    email = data["email"]
    password = data["password"]

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usersIdentity WHERE email = %s", (email,))
    results = cursor.fetchall()

    if len(results) > 0:
        return jsonify({"error": "User already exists."}), 409

    cursor.execute(
        "INSERT INTO usersIdentity (username, email, password) VALUES (%s, %s, %s)",
        (username, email, password)
    )
    connection.commit()

    return jsonify({"message": "User registered successfully."}), 200

# API endpoint for user login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM usersIdentity WHERE email = %s AND password = %s",
        (email, password)
    )
    results = cursor.fetchall()

    if len(results) == 0:
        return jsonify({"error": "Invalid email or password."}), 401

    user = results[0]
    user_id = user[0]
    token = jwt.encode({"userId": user_id}, "your-secret-key", algorithm="HS256")

    return jsonify({
        "message": "Login successful.",
        "token": token,
        "email": user[2],
        "username": user[1],
        "userId": user_id,
        "gender": results[0][4],
        "age": results[0][5],
        "height": results[0][6],
        "weight": results[0][7],
        "health_concern": results[0][8],
        "menu_type": results[0][9],
        "activity_type": results[0][10],
        "images": results[0][11]
    }), 200

# Middleware to verify JWT token
def authenticate_token(func):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token not provided."}), 401

        try:
            decoded = jwt.decode(token, "your-secret-key", algorithms=["HS256"])
            kwargs["user_id"] = decoded["userId"]
            return func(*args, **kwargs)
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 403

    wrapper.__name__ = func.__name__
    return wrapper

# API endpoint for adding user identity to the database
@app.route("/addUsersIdentity", methods=["POST"])
@authenticate_token
def add_users_identity(user_id):
    data = request.json
    age = data["age"]
    gender = data["gender"]
    weight = data["weight"]
    height = data["height"]
    health_concern = data["health_concern"]
    menu_type = data["menu_type"]
    activity_type = data["activity_type"]

    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usersIdentity SET age = %s, gender = %s, weight = %s, height = %s, health_concern = %s, menu_type = %s, activity_type = %s WHERE id = %s",
        (age, gender, weight, height, health_concern, menu_type, activity_type, user_id)
    )
    connection.commit()

    return jsonify({"message": "User information added successfully."}), 200

# API endpoint for changing the user's password, email, and username
@app.route("/usersIdentity/<int:user_id>", methods=["PUT"])
@authenticate_token
def update_users_identity(user_id):
    data = request.json
    current_password = data["currentPassword"]
    new_password = data["newPassword"]
    email = data["email"]
    username = data["username"]

    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM usersIdentity WHERE id = %s AND password = %s",
        (user_id, current_password)
    )
    results = cursor.fetchall()

    if len(results) == 0:
        return jsonify({"error": "Invalid current password."}), 401

    cursor.execute(
        "UPDATE usersIdentity SET password = %s, email = %s, username = %s WHERE id = %s",
        (new_password, email, username, user_id)
    )
    connection.commit()

    return jsonify({
        "message": "User data updated successfully.",
        "email": email,
        "username": username
    }), 200

# API endpoint for uploading an image to Google Cloud Storage
@app.route("/uploadImage/<int:user_id>", methods=["POST"])
@authenticate_token
def upload_image(user_id):
    file = request.files["image"]

    if not file:
        return jsonify({"error": "No file provided."}), 400

    timestamp = int(time.time() * 1000)
    filename = f"{user_id}-{timestamp}-{file.filename or 'image'}"

    blob = bucket.blob(filename)
    blob.upload_from_file(file)
    blob.make_public()

    image_url = blob.public_url

    cursor = connection.cursor()
    cursor.execute(
        "UPDATE usersIdentity SET images = %s WHERE id = %s",
        (image_url, user_id)
    )
    connection.commit()
    return jsonify({"imageUrl": image_url}), 200

def parse_array_fields(row):
    fields_to_parse = ['ingredients', 'tags', 'steps']  # Add other fields here if needed

    for field in fields_to_parse:
        if row[field]:
            if field == 'ingredients':
                row[field] = [item.strip() for item in row[field][1:-1].split(',')]
            else:
                row[field] = [item.strip() for item in row[field].split(',')]
        else:
            row[field] = []

    return row

@app.route("/getAllFoodData", methods=["GET"])
def get_all_food_data():
    cursor = connection.cursor()
    cursor.execute("SELECT name, id, minutes, tags, steps, description, ingredients, calories, total_fat, sugar, sodium, protein, saturated_fat, carbohydrates, vegetarian, fat, Non_Veg, Veg, images FROM food")
    columns = [desc[0] for desc in cursor.description]  # Get column names from cursor
    results = cursor.fetchall()

    if len(results) == 0:
        return jsonify({"error": "No food data found."}), 404

    food_data = []
    for row in results:
        parsed_row = parse_array_fields(dict(zip(columns, row)))  # Convert row tuple to dictionary
        food_data.append(parsed_row)

    response = {'result': food_data}

    return jsonify(response), 200

@app.route("/searchRecipeByName", methods=["GET"])
def search_recipe_by_name():
    name = request.args.get("name")

    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM food WHERE name LIKE %s",
        ("%" + name + "%",)
    )
    results = cursor.fetchall()

    if len(results) == 0:
        return jsonify({"error": "No recipes found with the given name."}), 404

    columns = [desc[0] for desc in cursor.description]  # Get column names from cursor
    recipe_data = []
    for row in results:
        parsed_row = parse_array_fields(dict(zip(columns, row)))  # Convert row tuple to dictionary and parse array fields
        recipe_data.append(parsed_row)

    return jsonify({'result':recipe_data}), 200


# Load and preprocess the recipe data
food_features = pd.read_csv('food_features.csv')
scaler = StandardScaler()
recipe_features_scaled = scaler.fit_transform(food_features)

# Load the trained model
model = tf.keras.models.load_model('recommendation_model.h5')  # Replace 'your_model_path' with the actual path to your trained model
@app.route("/<int:age>/<int:gender>/<int:height>/<int:weight>/<int:healthconcern>/<int:menutype>/<int:activity>", methods=['GET'])
def recommend_recipe(age,gender,height,weight,healthconcern,menutype,activity):
    # Preprocess user input
    if gender == 1:
        constants_gender = 655.1
        constants_weight = 9.563
        constants_height = 1.850
        constants_age = 4.676
    elif gender == 2:
        constants_gender = 66.47
        constants_weight = 13.75
        constants_height = 5.003
        constants_age =  6.755
    BMR = constants_gender + (constants_weight * weight) + (constants_height * height) - (constants_age * age)
    if activity == 1:
        constants_activity = 1.2
    elif activity == 2:
        constants_activity = 1.375
    elif activity == 3:
        constants_activity = 1.55
    elif activity == 4:
        constants_activity = 1.725
    elif activity == 5:
        constants_activity = 1.9
    calories = BMR * constants_activity
    carbohydrates = ((20/100) * calories /3)
    protein = ((40/100) * calories /3)
    fat = ((40/100) * calories /3)
    if menutype == 1:
        vegetarian = 0
    elif menutype == 2:
        vegetarian = 1
    # Handle invalid gender input (optional)
    constants_gender = 0.0  # or any other default value
    user_input_data = np.array([calories,protein,fat,carbohydrates,vegetarian])
    user_input_data = user_input_data.reshape(1, -1)
    user_input_data = scaler.transform(user_input_data)

    # Generate recipe predictions
    recipe_prediction = model.predict(user_input_data)

    # Calculate Euclidean distance between predicted features and each recipe in recipe_data
    distances = np.linalg.norm(recipe_features_scaled - recipe_prediction, axis=1)

    # Find the indices of the top 5 recipes with the smallest distances
    closest_recipe_indices = np.argsort(distances)

    food = pd.read_csv('food.csv')
    recipe_list = []
    # Retrieve the recipe details for the top 5 recommendations
    recipe_indices = []
    for recipe_index in closest_recipe_indices:
        recipe_details = food.iloc[recipe_index]
        
        # Check if the recipe is suitable for the user based on their vegetarian status
        if vegetarian == 1 and recipe_details['vegetarian'] == 1:
            recipe_indices.append(recipe_index)
        elif vegetarian == 0:
            recipe_indices.append(recipe_index)
        
        # Break the loop if we have collected enough recipe indices
        if len(recipe_indices) == 10:
            break

    recipe_list = []
    # Retrieve the recipe details for the selected recipe indices
    for recipe_index in recipe_indices:
        recipe_details = food.iloc[recipe_index]
        recipe_dict = recipe_details.to_dict()
        recipe_list.append(recipe_dict)

        recipe_dict['tags'] = eval(recipe_dict['tags'])
        recipe_dict['steps'] = eval(recipe_dict['steps'])
        recipe_dict['ingredients'] = eval(recipe_dict['ingredients'])
    # Return the recipe recommendations as JSON response
    return jsonify({'result': recipe_list})

# Start the server
if __name__ == "__main__":
    app.run(host='0.0.0.0',port='8080')
