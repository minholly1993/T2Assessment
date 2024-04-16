from flask import Flask, render_template, request, url_for, session, redirect
import sqlite3
import pymongo
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import os
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import geocoder
import requests
import json

# sql
def createUserTable():
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute('''CREATE TABLE IF NOT EXISTS Users(
    userid INTEGER PRIMARY KEY,
    username NOT NULL UNIQUE,
    password NOT NULL
  );''')
  conn.commit()
  conn.close()

def addUser(username, password):
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute("INSERT INTO Users(username, password) VALUES(?, ?)", (username, password))
  conn.commit()
  conn.close()

def findUser(username):
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute("SELECT * FROM Users WHERE username = ?", (username,))
  user = c.fetchall()
  conn.close()
  return user

def getUserID(username, password):
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute("SELECT userid FROM Users WHERE username = ? AND password = ?", (username, password))
  userid = c.fetchone()
  conn.close()
  return int(userid[0])

def getUsername(userid):
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute("SELECT username FROM Users WHERE userid = ? ", (userid,))
  username = c.fetchone()
  conn.close()
  return username[0]

def verifyUser(username, password):
  conn = sqlite3.connect("users.db")
  c = conn.cursor()
  c.execute("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
  user = c.fetchall()
  conn.close()
  return user

# mongodb
def connect():
  # uri = "mongodb+srv://bupingjin:minholly@t2assessment.uhyexsi.mongodb.net/?retryWrites=true&w=majority&appName=T2Assessment"
  uri ="mongodb+srv://dbuser:Asrjc534768@cluster0.qq3apxs.mongodb.net/?retryWrites=true&w=majority"
  # Create a new client and connect to the server
  client = MongoClient(uri, server_api=ServerApi('1'))
  # Send a ping to confirm a successful connection
  try:
      client.admin.command('ping')
      print("Pinged your deployment. You successfully connected to MongoDB!")
  except Exception as e:
      print(e)
  return client
    
def createUserInfo(userid, username):
  client = connect()
  print("test1")
  db = client["users"]
  print("test2")
  col = db[str(userid)]
  print("test3")
  budget = {"Income": 0, "Expenses": 0}
  profile = {"Name": username}
  data = {"budget": budget, "profile": profile}  
  col.insert_one(data)
  print("test4")

def addBudget(data, userid):
  client = connect()
  db = client["users"]
  col = db[str(userid)]
  budget = col["budget"]
  budget.insert_one(data)

def getBudget(userid):
  client = connect()
  db = client["users"]
  col = db[str(userid)]
  return col["budget"](sort=[("Income", -1), ("Expenses", -1)])

def updateBudget(userid, data):
  client = connect()
  db = client["users"]
  col = db[str(userid)]
  budget = col["budget"]
  budget.update_one({}, {"$set": data})

def addSpendingCategory(userid, category):
  client = connect()
  db = client["users"]
  col = db[str(userid)]
  budget = col["budget"]
  budget.update_one({}, {"$set": {f"Expenses.{category}": 0}})

# AI
def generate_default_budget():
  default_budget = {
    'Savings':{"amt": 500, "color": '#d1b582'},
    'Investments':{"amt": 100, "color": '#878cde'},
    'Groceries':{"amt": 300, "color": '#a5c1df'}, 
    'Rent':{"amt": 900, "color": '#9ccea8'}, 
    'Utilities':{"amt": 150, "color": '#e5d6a9'}, 
    'Transportation':{"amt": 200, "color": '#e1a8ad'}, 
    'Entertainment':{"amt": 100, "color": '#98a0e2'}
  }
  return default_budget

def train_model_and_predict_spending_categories(userid):
  # Connect to MongoDB
  client = connect()
  db = client["users"]
  col = db[str(userid)]

  # Check if the collection is empty
  if col.count_documents({}) == 1:
      return generate_default_budget()

  # Load spending data from MongoDB
  spending_data = pd.DataFrame(list(col.find()))

  # Feature engineering and preprocessing
  X = spending_data.drop(columns=['category'])
  y = spending_data['category']

  # Encode categorical labels
  label_encoder = LabelEncoder()
  y = label_encoder.fit_transform(y)

  # Split data into training and testing sets
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

  # Train a logistic regression model
  model = LogisticRegression()
  model.fit(X_train, y_train)

  # Make predictions
  predictions = model.predict(X_test)

  # Decode predicted labels
  predicted_categories = label_encoder.inverse_transform(predictions)

  # Create a dictionary of predicted spending categories
  predicted_categories_dict = {category: None for category in predicted_categories}

  return predicted_categories_dict

# misc
def sortData(budget_data):
  # Calculate total budget
  total_budget = sum(item["amt"] for item in budget_data.values())
  # Calculate the total percentage
  total_percentage = 100
  # Calculate the percentage of each category
  category_percentages = {category: (data['amt'] / total_budget) * 100 for category, data in budget_data.items()}
  # Create a dictionary of category colors
  category_colors = {category: data['color'] for category, data in budget_data.items()}

  max_amount = max(item["amt"] for item in budget_data.values())
  return total_budget, total_percentage, category_percentages, category_colors, max_amount

# Map Functions
# Function to fetch user's location
def get_user_location():
  # try:
  #   response = requests.get('https://freegeoip.app/json/')
  #   data = response.json()
  #   latitude = data.get('latitude')
  #   longitude = data.get('longitude')
  #   city = data.get('city')
  #   return [latitude, longitude, city]
  # except:
  #   return None
  g = geocoder.ip('me')
  if g.ok:
    return g.latlng
  

def get_locations(term, pricerange):
  # Define your Yelp Fusion API key
  API_KEY = "D_NtLvM4V8mzH8W4G5UHhRQPIMRhhcwwLIBioYX_iMqPW-AGfBaHkltwvfmUa9JZO6WSnUL5tlWFHcQbAXT-H4_mw7cYiJdpgZplmzHGitgfNeqH04aVgwr0dlwWZnYx"

  # Define the search parameters
  user_location = get_user_location()
  if user_location:
    # print("found location")
    params = {
        'term': term,
        'latitude': user_location[0],
        'longitude': user_location[1],
        'price': pricerange,
        'limit': 15,
        'radius': 7500,
    }
  else: # default location (Singapore)
    # print("no location")
    params = {
      'term': term,
      'location': 'Singapore',
      'price': pricerange,
      'limit': 15,
      'radius': 7500,
    }

  # Define the endpoint URL
  url = 'https://api.yelp.com/v3/businesses/search'

  # Set up the request headers with the API Key
  headers = {
      'Authorization': f'Bearer {API_KEY}'
  }

  # Send the GET request to the Yelp Fusion API
  response = requests.get(url, params=params, headers=headers)

  # Parse the JSON response
  data = response.json()

  return data

# main
createUserTable()
logged_in_user = None
# sample
budget_data = {
  'Groceries':{"amt": 200, "color": '#a5c1df'}, 
  'Rent':{"amt": 800, "color": '#9ccea8'}, 
  'Utilities':{"amt": 150, "color": '#e5d6a9'}, 
  'Transportation':{"amt": 100, "color": '#e1a8ad'}, 
  'Entertainment':{"amt": 100, "color": '#98a0e2'}
}

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
  global logged_in_user
  if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']
      user = verifyUser(username, password)
      userid = getUserID(username, password)
      if user:
          # Terminate session of the previous user if exists
          session.pop('userid', None)
          # Set the session username to the current user
          session['userid'] = userid
          # Set the logged-in user to the current user
          logged_in_user = userid
          return redirect(url_for('home'))
      else:
          return render_template("login.html", error="Invalid username or password")
  return render_template("login.html")

@app.route('/logout')
def logout():
    global logged_in_user
    session.pop('username', None)
    logged_in_user = None
    return redirect(url_for('login'))

@app.route('/signup', methods=["GET", "POST"])
def signup():
  global logged_in_user
  if request.method == "POST":
    username = request.form["username"]
    password = request.form["password"]
    repassword = request.form["repassword"]
    if password != repassword:
      return render_template("signup.html", error="Passwords do not match")
    elif findUser(username):
      return render_template("signup.html", error="Username already exists")
    else:
      # sql
      addUser(username, password)
      userid = getUserID(username, password)
      # mongodb
      createUserInfo(userid, username)
      # Terminate session of the previous user if exists
      session.pop('userid', None)
      # Set the session username to the current user
      session['userid'] = userid
      # Set the logged-in user to the current user
      logged_in_user = userid
      return redirect(url_for('home'))
  return render_template("signup.html")

@app.route('/home', methods=["GET", "POST"])
def home():
  global logged_in_user
  if logged_in_user:
    userid = logged_in_user
    username = getUsername(userid)
    return render_template("home.html", username=username)
  else:
    # return redirect(url_for('login'))
    return render_template("home.html")

@app.route('/map', methods=["GET", "POST"])
def map():
  # global logged_in_user
  logged_in_user = True
  if logged_in_user:
    userid = logged_in_user
    if request.method == "POST":
      term = request.form.get("term")
      # print(term)
      if term == '':  
        term = 'Any'
      price1 = request.form.get("$")
      price2 = request.form.get("$$")
      price3 = request.form.get("$$$")
      price4 = request.form.get("$$$$")
      price5 = request.form.get("$$$$$")
      pricerange = [price1, price2, price3, price4, price5]
      pricerange = [int(pricerange[x]) for x in range(len(pricerange))                       if pricerange[x] is not None]
      if pricerange == []:
        pricerange = [1]
      # print(pricerange)
      # print(term)
      locations = get_locations(term, pricerange)
      # print("locations")
      data = {'latitudes': [],
              'longitudes': [],
              'names': [],
              'categories': [],
              'ratings': [],
              'prices': [],
              'distances': []}
      # print(locations)
      if not locations:
        # print("no location")
        return render_template('map.html')
      else:
        # print("yes location")
        # print(locations)
        for location in locations['businesses']:
          if location['coordinates']['latitude'] is None:
            return render_template('map.html')
          else:
            data['latitudes'].append(location['coordinates']['latitude'])
            data['longitudes'].append(location['coordinates']['longitude'])
            data['names'].append(location['name'])
            categories = ''
            for category in location['categories']:
                # print(category)
                categories += category['title'] + ', '
            categories = categories[:-2]
            data['categories'].append(categories)
            data['ratings'].append(location['rating'])
            if 'price' in location.keys():
              data['prices'].append(location['price'])
            else:
              data['prices'].append('N/A')
            data['distances'].append(str(round(location['distance']/1000, 2)))
        # print(data)
        return render_template('maplocations.html', data=data)
    else:
      return render_template('map.html')
  else:
    return render_template('index.html')

@app.route('/budget', methods=["GET", "POST"])
def budget():
  global logged_in_user
  ### swapped to get from database
  global budget_data
  if logged_in_user:
      userid = logged_in_user
      ### swapped to get from database
      # budget_data = getBudget(userid)
      total_budget, total_percentage, category_percentages, category_colors, max_amount = sortData(budget_data)
      if request.method == "POST":
        try:
          ### suggested_budget = train_model_and_predict_spending_categories(userid)
          suggested_budget = generate_default_budget()
          suggested_total, suggested_total_percentage, suggested_percentages , suggested_colors, suggested_max = sortData(suggested_budget)
        except Exception as e:
          print(e)
          # return render_template(
          #     'budget.html',
          #     budget_data=budget_data,
          #     category_percentages=category_percentages,
          #     total_percentage=total_percentage,
          #     category_colors=category_colors,
          #     total_budget=total_budget,
          #     max_amount=max_amount,
          #     error=str(e)
          # )
        else: # for suggested budget data
          return render_template(
              'budget.html',
              budget_data=budget_data,
              category_percentages=category_percentages,
              total_percentage=total_percentage,
              category_colors=category_colors,
              total_budget=total_budget,
              max_amount=max_amount,
              suggested_budget=suggested_budget,
              suggested_total=suggested_total,
              suggested_colors=suggested_colors,
              suggested_percentages=suggested_percentages
          )
      return render_template( # for default budget data
        'budget.html',
        budget_data=budget_data,
        category_percentages=category_percentages,
        total_percentage=total_percentage,
        category_colors=category_colors,
        total_budget=total_budget,
        max_amount=max_amount
      )
  else: # for not logged in user
    # return redirect(url_for('login'))
    ### for holder
    # budget_data = getBudget(userid) 
    total_budget, total_percentage, category_percentages, category_colors, max_amount = sortData(budget_data)
    return render_template(
      'budget.html',
      budget_data=budget_data,
      category_percentages=category_percentages,
      total_percentage=total_percentage,
      category_colors=category_colors,
      total_budget=total_budget,
      max_amount=max_amount
    )

@app.route('/add_suggested_budget', methods=["POST"])
def add_suggested_budget():
  global logged_in_user
  ### swapped to get from database
  global budget_data
  if logged_in_user:
      userid = logged_in_user
    
  checked_categories = request.form.getlist('category')
  for category in checked_categories:
      amt = request.form.get('amt_' + category)  # Get the amount for this category
      color = request.form.get('color_' + category)  # Get the color for this category
      if category in budget_data:
          budget_data[category]['amt'] = int(amt)
      else:
          budget_data[category] = {"amt": int(amt), "color": color}
            
  total_budget, total_percentage, category_percentages, category_colors, max_amount = sortData(budget_data)
  return redirect(url_for(
    'budget', 
    budget_data=budget_data, 
    total_budget=total_budget, 
    total_percentage=total_percentage, 
    category_percentages=category_percentages, 
    category_colors=category_colors, 
    max_amount=max_amount))

# Function to add budget for a user
@app.route('/add_budget', methods=["POST"])
def add_budget():
    global logged_in_user
    ### swapped to get from database
    global budget_data
    if logged_in_user:
        userid = logged_in_user
        category = request.form['category']
        amount = float(request.form['amount'])
        # budget_data = getBudget(userid)
        category = budget_data[category]
        category['amt'] += amount
        # updateBudget(budget_data, userid)
        return redirect(url_for('budget'))
    else:
        return redirect(url_for('login'))

# Function to get budget for a user
# @app.route('/get_budget', methods=["GET"])
# def get_budget():
#     userid = logged_in_user  # Assuming user is logged in
#     budget_data = getBudget(userid)
#     return jsonify(budget_data), 200

# # Function to update budget for a user
# @app.route('/update_budget', methods=["PUT"])
# def update_budget():
#     userid = logged_in_user  # Assuming user is logged in
#     data = request.json  # Assuming JSON data with budget information
#     updateBudget(userid, data)
#     return jsonify({"message": "Budget updated successfully"}), 200

# Function to add a spending category for a user
@app.route('/add_spending_category', methods=["POST"])
def add_spending_category():
    global logged_in_user
    ### swapped to get from database
    global budget_data
    if logged_in_user:
        userid = logged_in_user
        new_category = request.form['newCategory']
        new_category_color = request.form['color']
        # budget_data = getBudget(userid)
        budget_data[new_category] = {"amt": 0, "color": new_category_color} 
        # updateBudget(budget_data, userid)
        return redirect(url_for('budget'))
    else:
        return redirect(url_for('login'))

    
if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5001)