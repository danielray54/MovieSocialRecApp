#import necessary libraries
from flask import Flask, request, session, redirect, url_for, render_template, flash
from .models import User, todays_recent_posts, Movie, query_search
from pandas import DataFrame
import ast

#store Flask constructor in app variable
app = Flask(__name__)

# index decorator used to associate index functions to url
@app.route("/")
def index():
    # store the 5 most recent posts in variable
    posts = todays_recent_posts(5)
    toprated = Movie.rated_films("top")
    trending = Movie.rated_films("trending")

    # return the rendered index template passing posts variable to webpage
    return render_template("index.html", posts=posts, toprated=toprated, trending=trending)

# register decorator used to associate register functions to url,
#using both get and post methods
@app.route("/register", methods=["GET", "POST"])
def register():
    #if the req meth is post
    if request.method == "POST":
        #store the user inputted username and password into variables
        username = request.form["username"]
        password = request.form["password"]
        #init user node with username and store in variable
        user = User(username)
        #if the register function returns false
        if not user.register(password):
            # print message to tell user the username already exists
            flash("A user with that username already exists.")
        #if the register function returns True
        else:
            #show confirmation message
            flash("Successfully Registered.")
            #take user to login page
            return redirect(url_for("login"))
    #render the register page
    return render_template("register.html")

# login decorator used to associate login functions to url
@app.route("/login", methods=["GET", "POST"])
def login():
    #if the req meth is post
    if request.method == "POST":
        #store the user inputted username and password in variables
        username = request.form["username"]
        password = request.form["password"]
        #init user node with username and store in variable
        user = User(username)
        #if verify password funct returns false
        if not user.verify_password(password):
            #show invalid login message
            flash("Invalid login.")
        #if verify password funct returns true
        else:
            #show confirmation message
            flash("Successfully logged in.")
            #save the username in the session, to keep track of whos logged in
            session["username"] = user.username
            #send user to index page
            return redirect(url_for("index"))
    #render the login page
    return render_template("login.html")

# logout decorator used to associate logout functions to url
@app.route("/logout")
def logout():
    #pop the username off the session
    session.pop("username")
    #confirmation message
    flash("Logged Out")
    #take user to index page
    return redirect(url_for("index"))

# add_post decorator used to associate add_post functions to url
@app.route("/add_post", methods=["POST"])
def add_post():
    #store form inputs into variables
    title = request.form['title']
    tags = request.form['tags']
    rating = request.form['rating']
    text = request.form['text']
    movid = request.form['movieID']
    #store logged in username in variable
    user = User(session["username"])
    #if the user didnt enter any of the inputs
    if not title or not tags or not rating:
        #tell them
        flash('you must fill the form out correctly')
    else:
        #confirmation message
        flash('post added')
        #use the add post function using the form inputs as parameters
        user.add_post(title, tags, rating, text, movid)
    #take the user to the index page
    return redirect(request.referrer)

# like_post decorator used to associate like_post functions to url
@app.route("/like_post/<postid>")
def like_post(postid):
    #store logged in username into variable
    username = session.get('username')
    #if the variable is empty
    if not username:
        #,message to tell user they have to be logged in
        flash("You must be logged in to like a post")
        #take the not logged in user to the login page
        return redirect(url_for('login'))
    #call like post function on username and postid
    User(username).like_post(postid)
    #confirmation message
    flash("Liked Post!")
    #take the user back to where they were
    return redirect(request.referrer)

# profile decorator used to associate profile functions to url
@app.route("/profile/<username>")
def profile(username):
    #store logged in username into variable
    logged_in_username = session.get('username')
    userid = DataFrame(User.get_userid(str(username)))["userid"][0]
    trending = Movie.rated_films("trending")
    recs = Movie.recommend_films(int(userid))
    #store the username of the profile being viewed into variable
    user_being_viewed_username = username
    #store user node of of the profile being viewed into variable
    user_being_viewed = User(user_being_viewed_username)
    #get the five most recent posts of the user and store in variable
    posts = user_being_viewed.recent_posts(5)
    #init list for similar users
    similar = []
    #if the user is logged in
    if logged_in_username:
        #store the user node into a variable
        logged_in_user = User(logged_in_username)
        #if the profile being viewed is that of the user whos logged in
        if logged_in_user.username == user_being_viewed.username:
            #store the similar users into the similar list
            similar = logged_in_user.get_similar_users()
    #return the profile page, taking username, recent posts and similar users as
    #parameters
    return render_template(
        'profile.html',
        username=username,
        posts=posts,
        similar=similar,
        recs=recs, trending=trending
    )

@app.route("/movie/<movie_id>")
def movie(movie_id):
    mov = Movie.get_film_data(int(movie_id))
    if not mov:
        flash("Film isn't in database")
        return redirect(url_for('index'))
    else:
        posts = Movie.movie_recent_posts(5, int(movie_id))
        sim_films = Movie.get_similar_films(int(movie_id))
        genres = DataFrame(Movie.get_film_genres(int(movie_id)))
        genres = str(genres['genres'][0]).replace("'", "").strip("[]")
        film = DataFrame(mov)
        title = film["title"][0]
        id = film["movieID"][0]
        year = film["year"][0]
        overview = film["overview"][0]
        poster = film["poster"][0]
        lang = film["lang"][0]
        ytlink = film["ytlink"][0].replace("watch?v=", "embed/")
        runtime = film["runtime"][0]
        budget = film["budget"][0]
        featcrew = film["featcrew"][0]
        if(featcrew == None):
            featcrew = ""
        else:
            featcrew = ast.literal_eval(film["featcrew"][0])
        revenue = film["revenue"][0]
        keywords = str(film["keywords"][0])
        keywords = keywords.replace("'", "").strip("[]")


    return render_template("movie.html", title=title, year=year, overview=overview,
                           poster=poster, lang=lang,
                           runtime=runtime, budget=budget,genres=genres,
                           revenue=revenue,keywords=keywords, ytlink=ytlink,
                           featcrew=featcrew, id=id, posts=posts, simfilms=sim_films)


@app.route("/results", methods=["POST"])
def results():
    if request.method == "POST":
        if not request.form['title']:
            flash("Please enter Text")
            return redirect(request.referrer)
        elif not request.form['searchobj']:
            flash("Please enter Search Query")
            return redirect(request.referrer)
        else:
            searchobj = request.form['searchobj']
            text = str(request.form['title']).lower()
            if request.form['searchobj'] == "User":
                queryresults = query_search("User", str(text))
            elif request.form['searchobj'] == "Movie":
                queryresults = query_search("Movie", str(text))
            return render_template("results.html", queryresults=queryresults, searchobj=searchobj)