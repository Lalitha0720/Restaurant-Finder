from flask import Flask, render_template, request, session
from pymongo import MongoClient
import numpy as np

app = Flask(__name__)

app.config['SECRET_KEY'] = 'AnjanaKollipara'
app.config['MONGO_URI'] = 'http://127.0.0.1:5000/'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Create a database
db = client['infs740']

# Create collections
restaurants_table = db['restaurant']
users_table = db['users']
reviews_table = db['reviews']

# Rendering the Login Page
@app.route('/')
def index():
  return render_template('login_page.html')

# Rendering the Sign-Up Page
@app.route('/signup_page.html')
def signup_page():
  return render_template('signup_page.html')

# Rendering the Restaurant Page
@app.route('/restaurant_page.html')
def res_page():
  all_restaurants = restaurants_table.find()
  return render_template('restaurant_page.html', all_restaurants = all_restaurants)

# Rendering the User Information Page
@app.route('/account_details.html')
def acc_page():
  # Getting the username of the user currently logged in
  user_data = users_table.find({'username' : session['username']})
  # Give an error if the user is not present in the database
  if not user_data:
    error = "Username doesn't exist."
    return render_template('account_details.html', error = error)
  return render_template('account_details.html', user = user_data)

# Deleting an Account
@app.route('/delete-account', methods = ['POST', 'GET'])
def delete_account():
  if request.method == 'POST':
    # Delete the restaurant from the MongoDB collection
    result = users_table.delete_one({'username': session['username']})
    # Check if the deletion was successful
    if result.deleted_count > 0:
      error = "Account Deletion Successful"
      return render_template('login_page.html', error = error)
    else:
      error = "Account Deletion Unsuccessful"
      return render_template('account_details.html', error = error)
  # Render the account_details page if the method is GET
  return render_template('account_details.html')

# Updating the Account Information
@app.route('/update-account', methods = ['GET', 'POST'])
def update_account():
  if request.method == 'POST':
    # Fetch restaurant details from the collection
    user_details = users_table.find_one({'username': session['username']})
    # Render the add_restaurant page to perform updates
    return render_template('update_account.html', user_details = user_details)
  # Render the restaurant_page if it is a GET method
  return render_template('account_details.html')

# Updating the Account Information
@app.route('/update_acc', methods = ['GET', 'POST'])
def update_acc():
  if request.method == 'POST':
    username = session['username']
    # Checking if an user with the username exists
    flag = users_table.find_one({'username' : username})
    if flag:
      # Setting the update query
      update_query = {'$set': {'firstname': request.form['firstname'],
                               'lastname' : request.form['lastname'],
                               'email' : request.form['email'],
                               'password' : request.form['password'] 
                              }}
      # Update the document based on the restaurant name
      users_table.update_one({'username': username}, update_query)
    # Getting the user data after updation
    user_data = users_table.find({'username' : username})
    # Rendering the account_details page with the new user information
    return render_template('account_details.html', user = user_data)
  # Render the account_details page if GET method
  return render_template('account_details.html')

# Rendering the Add New Restaurant Page
@app.route('/add_restaurant.html')
def add_page():
  return render_template('add_restaurant.html')

# Rendering the Add New Review Page
@app.route('/add_review.html')
def add_rev():
  return render_template('add_review.html')

# Rendering the Review Page
@app.route('/review_page.html')
def rev_page():
  # Pipeline for grouping the reviews based on the restaurant name
  # Pipeline also calculates the average rating for the restaurant
  pipeline = [{ '$group' : {'_id': '$restaurant_name',
                              'reviews': {'$push': '$review'},
                              'average_rating': {'$avg': '$rating'}
                             }},
                  ]
  # Aggregating the reviews_table with pipeline
  all_reviews = reviews_table.aggregate(pipeline)
  # Rendering the review page
  return render_template('review_page.html', all_reviews = all_reviews)

# Rendering the Data Visualisation Page
@app.route('/data_visualisation.html')
def data_vis():
  # Pipeline for getting the number of restaurants that serve the same cuisine type
  pipeline = [{ '$group': {
                '_id': '$cuisine_type',
                'count': {'$sum': 1}}
              }]
  result = list(restaurants_table.aggregate(pipeline))
  cuisine_types = [item['_id'] for item in result]
  counts = [item['count'] for item in result]
  # Pipeline for grouping the reviews based on the restaurant name
  # Pipeline also calculates the average rating for the restaurant
  pipeline = [{ '$group' : {'_id': '$restaurant_name',
                              'reviews': {'$push': '$review'},
                              'average_rating': {'$avg': '$rating'}
                             }},
                  ]
  result1 = list(reviews_table.aggregate(pipeline))
  restaurant_names = [item['_id'] for item in result1]
  ratings = [item['average_rating'] for item in result1]
  # Rendering the data_visualisation page
  return render_template('data_visualisation.html', cuisine_types = cuisine_types, counts = counts, restaurant_names = restaurant_names, ratings = ratings)

# Collecting user information
@app.route('/signup', methods = ['GET','POST'])
def signup():
  # Get the data from the Sign-Up Form
  if request.method == 'POST':
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    # Check if the user already exists
    if users_table.find_one({'username' : username}):
      error = "Username already exists. Please Login."
      return render_template('signup_page.html', error = error)
    # If the username doesn't exist
    session['username'] = username
    users_table.insert_one({'firstname' : firstname,
                            'lastname' : lastname,
                            'username' : username,
                            'email' : email,
                            'password': password})
    all_restaurants = restaurants_table.find()
    # Rendering the restaurants page with the list of all restaurants
    return render_template('restaurant_page.html', all_restaurants = all_restaurants)
  # If the method is not POST, send back to the Sign-Up Page
  return render_template('signup_page.html')

# Logging-In if the username and password are correct
@app.route('/login', methods = ['GET', 'POST'])
def login():
  # Get the data from the Login Form
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    session['username'] = username
    # Check if the given username exists in the users_table
    user = users_table.find_one({'username' : username})
    # If the username doesn't exist, ask the user to sign-up
    if not user:
      error = "The username doesn not exist. Please Sign-Up."
      return render_template('signup_page.html', error = error)
    # If the username exists, check whether the password is correct
    if user['password'] != password:
      error = "Incorrect password"
      return render_template('login_page.html', error = error)
    # If the username and password match, redirect the user to the Restaurant Page
    all_restaurants = restaurants_table.find()
    # Rendering the restaurants page with the list of all restaurants
    return render_template('restaurant_page.html', all_restaurants = all_restaurants)
  # If the method is not POST, send back to the Login Page
  return render_template('login_page.html')

# Adding a new Restaurant
@app.route('/new_restaurant', methods = ['GET', 'POST'])
def new_res():
  # Get the data from the New Restaurant Form
  if request.method == 'POST':
    restaurant_name = request.form['restaurant_name']
    cuisine_type = request.form['cuisine_type']
    address = request.form['address']
    phone_number = request.form['phone_number']
    price_range = request.form['price_range']
    flag = restaurants_table.find_one({'restaurant_name' : restaurant_name})
    if flag:
      # Setting the update query
      update_query = {'$set': {'cuisine_type': request.form['cuisine_type'],
                               'address' : request.form['address'],
                               'phone_number' : request.form['phone_number'],
                               'price_range' : request.form['price_range'] 
                              }}
      # Update the document based on the restaurant name
      restaurants_table.update_one({'restaurant_name': restaurant_name}, update_query)
    else:
      # Insert into the restaurant collection
      restaurants_table.insert_one({'restaurant_name' : restaurant_name, 
                                    'cuisine_type' : cuisine_type,
                                    'address' : address,
                                    'phone_number' : phone_number,
                                    'price_range' : price_range})
    all_restaurants = restaurants_table.find()
    # Rendering the restaurants page with the list of all restaurants
    return render_template('restaurant_page.html', all_restaurants = all_restaurants)
  # Rendering the add_restaurant page if the method is GET
  return render_template('add_restaurant.html')

# Deleting a Restaurant
@app.route('/delete_restaurant', methods = ['GET', 'POST'])
def delete_restaurant():
  if request.method == 'POST':
    # Get the restaurant name from the form submission
    restaurant_name = request.form['restaurant_name']
    # Delete the restaurant from the MongoDB collection
    result = restaurants_table.delete_one({'restaurant_name': restaurant_name})
    result1 = reviews_table.delete_many({'restaurant_name' : restaurant_name})
    all_restaurants = restaurants_table.find()
    # Rendering the restaurants page with the list of all restaurants
    return render_template('restaurant_page.html', all_restaurants = all_restaurants)
  return render_template('restaurant_page.html')

# Updating the Restaurant Information
@app.route('/update_restaurant', methods = ['GET', 'POST'])
def update_restaurant():
  if request.method == 'POST':
    # Get the restaurant name from the form submission
    restaurant_name = request.form['restaurant_name']
    # Fetch restaurant details from the collection
    restaurant_details = restaurants_table.find_one({'restaurant_name': restaurant_name})
    # Render the add_restaurant page to perform updates
    return render_template('add_restaurant.html', restaurant_details = restaurant_details)
  # Render the restaurant_page if it is a GET method
  return render_template('restaurant_page.html')

# Adding Review and Rating to the Restaurant
@app.route('/insert_review', methods = ['GET', 'POST'])
def add_review():
  if request.method == 'POST':
    # Getting the information from the form
    restaurant_name = request.form['restaurant_name']
    review = session['username'] + " : " + request.form['review'] 
    rating = float(request.form['rating'])
    # Getting the restuarnt information
    flag = restaurants_table.find_one({'restaurant_name' : restaurant_name})
    if flag:
      # Add the review if the restaurant exists
      reviews_table.insert_one({'restaurant_name' : restaurant_name, 'review' : review, 'rating' : rating})
      # Grouping the reviews for same restaurants
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      all_reviews = reviews_table.aggregate(pipeline)
      # Render the review_page to display all the reviews
      return render_template('review_page.html', all_reviews = all_reviews)
    else:
      # Alert the user with an error if the restaurant doesn't exist
      error = "Restaurant not found."
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      all_reviews = reviews_table.aggregate(pipeline)
      return render_template('review_page.html', all_reviews = all_reviews, error = error)
  # Render the add_review page if the method is GET
  return render_template('add_review.html')

# Deleting a Review
@app.route('/delete_review', methods = ['GET', 'POST'])
def delete_review():
  if request.method == 'POST':
    # Getting the information from the form
    restaurant_name = request.form['restaurant_name']
    review = request.form['review']
    # Deleting the review
    result = reviews_table.delete_one({'restaurant_name' : restaurant_name,'review' : review})
    # Applying the pipeline after the deletion
    pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
    all_reviews = reviews_table.aggregate(pipeline)
    # Rendering the review_page without the deleted review
    return render_template('review_page.html', all_reviews = all_reviews)
  # Render the review_page if GET method
  return render_template('review_page.html')

# Updating a Review
@app.route('/update_review', methods = ['GET', 'POST'])
def update_review():
  if request.method == 'POST':
    # Get the restaurant name from the form
    restaurant_name = request.form['restaurant_name']
    review = request.form['review']
    # Fetch restaurant details from the collection
    review_details = reviews_table.find_one({'restaurant_name': restaurant_name, 'review' : review})
    # Render the add_restaurant page to perform updates
    return render_template('/update_review.html', review_details = review_details)
  # Render the restaurant_page if it is a GET method
  return render_template('review_page.html')
    
# Updating the Review
@app.route('/update_rev', methods = ['GET', 'POST'])
def update_rev():
  if request.method == 'POST':
    # Get the restaurant name from the form
    restaurant_name = request.form['restaurant_name']
    flag = restaurants_table.find_one({'restaurant_name' : restaurant_name})
    # Proceed with the updation if the restaurant is present in the data base
    if flag:
      update_query = {'$set': {'review': request.form['review']}}
      # Update the document based on the restaurant name
      reviews_table.update_one({'restaurant_name': restaurant_name}, update_query)
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      all_reviews = reviews_table.aggregate(pipeline)
      # Render the review_page with updated review
      return render_template('review_page.html', all_reviews = all_reviews)
  # Render the review_page if the method is GET
  return render_template('review_page.html')

# Search functionality
@app.route('/search', methods = ['GET', 'POST'])
def search():
  if request.method == 'POST':
    # Search using the restaurant's name
    search = ""
    search = request.form['search']
    floating_range = np.arange(0.0, 6.0, 0.1)
    if ' ' in search:
      all_restaurants = restaurants_table.find({'restaurant_name' : search})
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      all_reviews = list(reviews_table.aggregate(pipeline))
      for item in all_reviews:
        if item['_id'] == search:
          reviews = item['reviews']
          average_rating = item['average_rating']
          break
      return render_template('search_name.html', all_restaurants = all_restaurants, all_reviews = reviews, average_rating = average_rating)
    
    # Search using the cuisine type
    elif search[0] in ['I', 'M', 'T', 'V', 'C']:
      all_restaurants = restaurants_table.find({'cuisine_type' : search})
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      all_reviews = list(reviews_table.aggregate(pipeline))
      return render_template('search_rating.html', all_restaurants = all_restaurants, all_reviews = all_reviews)
    
    # Search by username
    elif search[0] in ['a','c','m','j','p','r']:
      all_reviews = reviews_table.find({'review' : {"$regex": f"^{search}"}})
      return render_template('review.html', all_reviews = all_reviews, search = search)
    
    # Search using rating
    elif float(search) in floating_range:
      buf = float(search)
      pipeline = [{ '$group' : {'_id': '$restaurant_name',
                                'reviews': {'$push': '$review'},
                                'average_rating': {'$avg': '$rating'}
                              }},
                    ]
      reviews = list(reviews_table.aggregate(pipeline))
      restaurants = []
      for review in reviews:
        if review['average_rating'] >= buf:
          restaurants.append(review['_id'])
      all_restaurants = []
      for restaurant in restaurants:
        all_restaurants.append(restaurants_table.find_one({'restaurant_name' : restaurant}))
      return render_template('search_rating.html', all_restaurants = all_restaurants, all_reviews = reviews)
  # Render the restaurant page if the method is GET
  return render_template('restaurant_page.html')

if __name__ == '__main__':
  app.run(debug = True)