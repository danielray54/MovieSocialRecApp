# Import libraries
from py2neo import Graph, Node, Relationship, NodeMatcher
from passlib.hash import bcrypt
from datetime import date, datetime, timedelta
import time
import uuid

# init graph object
graph = Graph()
# init matcher object
matcher = NodeMatcher(graph)


# user class containing user functions
class User:
    # Function: Constructor Function
    # Inputs: Self -  reference to the instance being constructed, username
    # Output: None
    # Process: constructs instance of user based on username which is unique
    def __init__(self, username):
        self.username = username

    # Function: Find User
    # Inputs: Self
    # Output: user node
    # Process: Uses the matcher object to find a user node based on the username
    def find(self):
        # user matcher object to match user on username returning first instance
        user = matcher.match("User", username=self.username).first()
        # return whole user node
        return user

    # Function: Find User
    # Inputs: Self
    # Output: user node
    # Process: Uses the matcher object to find a user node based on the username
    def get_userid(username):
        # user matcher object to match user on username returning first instance
        query = """
        MATCH (user:User)
        WHERE user.username = {username}
        RETURN user.userid as userid
        """
        # return whole user node
        return graph.run(query, username=username).data()

    # Function: Register User
    # Inputs: Self, Password
    # Output: True or False
    # Process: finds user, if doesnt exist -finds the last id used and adds 1.
    # if does exist run bcrypt verify function on stored password
    # then creates user with userid username and password inputted
    # which is encrypted by bcrypt
    def register(self, password):
        # if the user doesnt exist - find on username
        if not self.find():
            # search for the highest userId
            query = """
            MATCH (u:User) RETURN u.userid
            ORDER BY u.userid DESC
            LIMIT 1;
            """
            # store query result in variable
            lastid = graph.evaluate(query)
            # add one to the id
            userId = int(lastid) + 1
            # create node with relevant properties
            user = Node("User", userid=userId, username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            # if user created return true
            return True
        # if user found return false
        return False

    # Function: Verify Password
    # Inputs: Self, Password
    # Output: True or False
    # Process: finds user, if doesnt exist - return false.
    # if does exist run bcrypt verify function on stored password
    # and inputted password - returns either true or false
    def verify_password(self, password):
        # find  user and store in variable
        user = self.find()
        # if user doesnt exist
        if not user:
            # return false
            return False
        # else, verify password with bcrypt lib which returns true or false
        return bcrypt.verify(password, user["password"])

    # Function: Add Post
    # Inputs: Title, Tags, Rating, Text, MovieID
    # Output: N/A
    # Process: finds user and adds post node related to user.
    # Tags are then stripped to list of words and added to
    # tag node
    def add_post(self, title, tags, rating, text, movid):
        # find user and store in variable
        user = self.find()
        movid = int(movid)
        movie = Movie.find_film(movid)
        # create post node with form inputs
        post = Node(
            "Post",
            postid=str(uuid.uuid4()),
            title=title,
            rating=rating,
            text=text,
            movid=movid,
            timestamp=int(datetime.now().strftime("%s")),
            date=datetime.now().strftime("%F")
        )
        # create the "published" relationship between user and post
        rel = Relationship(user, "PUBLISHED", post)
        graph.create(rel)
        # create the "published" relationship between user and post
        rel = Relationship(post, "REVIEWED", movie)
        graph.create(rel)
        # create the "rated" relationship between user and movie
        rel = Relationship(user, "RATED", movie, rating=rating)
        graph.create(rel)
        # store stripped and lower cased tags into list
        tags = [x.strip() for x in tags.lower().split(",")]
        # for each distinct tag
        for name in set(tags):
            # merge tag, so that only one node represents each unique tag
            tag = Node('Tag', name=name)
            graph.merge(tag, 'Tag', 'name')
            # create relationship between tag and post
            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)

    # Function: Like Post
    # Inputs: Post_id
    # Output: None
    # Process: user who is viewing post is stored in variable,
    # finds the post using post_id and the matcher object
    # then creates relationship between the two
    def like_post(self, postid):
        # store user viewing post in variable
        user = self.find()
        # finds post using matcher object
        post = matcher.match("Post", postid=postid).first()
        # creates relationship between user and post
        rel = Relationship(user, 'LIKES', post)
        # merges it so that only one relationship can be created
        graph.merge(rel)

    # Function: Recent post
    # Inputs:Self, number of posts
    # Output: result of query
    # Process: runs cypher query to return n recent posts from username
    def recent_posts(self, n):
        # find posts that user has posted, on the username
        # returns the whole post, and the tags in a list
        # ordered by date of post
        query = """
        MATCH (user:User)-[:PUBLISHED]->(post:Post)
        Where user.username = {username}
        OPTIONAL MATCH (post:Post)<-[:TAGGED]-(tag:Tag)
        OPTIONAL MATCH (post)-[:REVIEWED]->(movie:Movie)
        RETURN user.username as username, post, COLLECT(COALESCE(tag.name)) as tags,
        movie.title as movTitle
        ORDER BY post.date DESC
        Limit {n}
        """
        # returns the result of the query
        return graph.run(query, username=self.username, n=n)

    # Function: Get Similar Users
    # Inputs: Self
    # Output: result of query
    # Process: runs cypher query to return n similar using tags
    def get_similar_users(self):
        # get user's posts with tags, where username is the username of logged in user
        # and the logged in user isnt the same as the other user
        # get the other user and the tags which are similar
        # order by the amount of similar tags and limit to 3
        # return the user and the tags
        query = '''
            MATCH (you:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
                  (they:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
            WHERE you.username = {username} AND you <> they
            WITH they, COLLECT(DISTINCT tag.name) AS tags
            ORDER BY SIZE(tags) DESC LIMIT 5
            RETURN they.username AS similar_user, tags
            '''
        # return the result of the query
        return graph.run(query, username=self.username)

# user class containing user functions
class Movie:
    # Function: Constructor Function
    # Inputs: Self -  reference to the instance being constructed, username
    # Output: None
    # Process: constructs instance of user based on username which is unique
    def __init__(self, mov_id):
        self.mov_id = mov_id

    def find_film(mov_id):
        movie = matcher.match("Movie", movieID=mov_id).first()
        return movie

    def get_film_data(mov_id):
        query = """
        MATCH (m:Movie)-[:KEYWORD]-(t:Tag)
        WHERE m.movieID = {mov_id}
        RETURN m.budget as budget, m.featcrew as featcrew, 
        COLLECT(COALESCE(t.name)) as keywords, m.lang as lang, m.movieID as movieID,
        m.overview as overview, m.poster as poster, m.revenue as revenue, 
        m.runtime as runtime, m.title as title, m.year as year, m.ytlink as ytlink
        """
        return graph.run(query, mov_id = mov_id).data()

    def get_film_genres(mov_id):
        query = """
        MATCH (m:Movie)-[:HAS_GENRE]->(g:Genre)
        WHERE m.movieID = {mov_id}
        RETURN COLLECT(COALESCE(g.name)) as genres
        """
        return graph.run(query, mov_id = mov_id).data()


    def movie_recent_posts(n, movid):
        # find posts that were published with date the same as today,
        # return post ordered by time
        query = """
        MATCH(post:Post)-[:REVIEWED]->(movie:Movie)
        Where movie.movieID = {movid}
        OPTIONAL MATCH (post:Post)<-[:TAGGED]-(tag:Tag)
        OPTIONAL MATCH (user:User)-[:PUBLISHED]->(post:Post)
        RETURN user.username as username, post, COLLECT(COALESCE(tag.name)) as tags,
        movie.title as movTitle
        ORDER BY post.date DESC
        Limit {n}
        """
        return graph.run(query, movid=movid, n=n)

    def rated_films(opt):
        # find posts that were published with date the same as today,
        # return post ordered by time
        if opt == "top":
            query = """
            MATCH (post:Post)-[:REVIEWED]->(movie:Movie)
            WITH movie, SUM(toInteger(post.rating)) AS a
            RETURN movie.title as title, movie.movieID as movieID, movie.poster as poster
            ORDER BY a DESC
            LIMIT 10
            """
            return graph.run(query)
        elif opt == "trending":
            query = """
            MATCH (post:Post)-[:REVIEWED]->(movie:Movie)
            WITH movie, post, AVG(toInteger(post.timestamp))/{today} as b, movie.movieID as e
            ORDER BY b DESC
            MATCH (post)-[:REVIEWED]->(movie)
            WHERE movie.movieID = e
            RETURN distinct movie.title as title,  movie.movieID as movieID, movie.poster as poster
            LIMIT 10
            """
            today = int(datetime.now().strftime("%s"))
            return graph.run(query, today=today)

    def recommend_films(user_id):
            query = """
            MATCH (u1:User)-[:RATED]->(m3:Movie)
            WHERE u1.userid = {user_id}
            WITH [i in m3.movieID | i] as movies
            MATCH (u1)-[r:RATED]->(m1:Movie)-[s:SIMILAR]->(mo:Movie)
            WHERE u1.userid = {user_id} and r.rating > 3 and not mo.movieID in movies
            RETURN mo.title as title, mo.movieID as movieID, mo.poster as poster
            LIMIT 10
            """
            return graph.run(query, user_id= user_id).data()

    def recommend_recent_films(user_id):
        today = date.today()
        first = today.replace(day=1)
        lastMonth = first - timedelta(days=1)
        s = lastMonth.replace(day=1).strftime('%d/%m/%Y')
        timestamp = time.mktime(datetime.strptime(s, "%d/%m/%Y").timetuple())
        query = """
            MATCH (u1:User)-[:PUBLISHED]->(post:Post)-[:REVIEWED]->(m3:Movie) 
            WHERE u1.userid = {user_id} and post.timestamp > {timestamp}
            WITH [i in m3.movieID | i] as movies
            MATCH (u1)-[r:RATED]->(m1:Movie)-[s:SIMILAR]->(mo:Movie)
            WHERE u1.userid = {user_id} and not mo.movieID in movies
            RETURN mo.title as title, mo.movieID as movieID, mo.poster as poster
            LIMIT 10
            """
        return graph.run(query, user_id= user_id, timestamp=timestamp ).data()


    def get_similar_films(mov_id):
        query = """
        MATCH (t:Tag)-[:KEYWORD]-(m:Movie)-[:HAS_GENRE]->(g:Genre),
        (t)-[:KEYWORD]-(m2:Movie)-[:HAS_GENRE]->(g)
        WHERE m.movieID = {mov_id} AND m <> m2
        WITH m2, COLLECT(DISTINCT t.name) AS tags, COLLECT(DISTINCT g.name) AS genres
        order by SIZE(genres) DESC, SIZE(tags) DESC
        limit 10
        RETURN distinct m2.title as title, m2.movieID as movieID,m2.poster as poster
        """
        return graph.run(query, mov_id= mov_id).data()

# Function: Todays Recent Postss
# Inputs: number of posts
# Output: result of query
# Process: find most n most recent posts
# return post node as well as tags and username ordered by time
def todays_recent_posts(n):
    # find posts that were published with date the same as today,
    # return post ordered by time
    query = """
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    MATCH (post:Post)-[:REVIEWED]->(movie:Movie) 
    RETURN user.username as username, post, COLLECT(COALESCE(tag.name)) as tags,
    movie.title as movTitle
    ORDER BY post.timestamp DESC LIMIT {n}
    """
    # store todays date in variable
    today = datetime.now().strftime("%F")
    return graph.run(query, n=n)

# Function: Todays Recent Posts
# Inputs: number of posts
# Output: result of query
# Process: find most n most recent posts
# return post node as well as tags and username ordered by time
def query_search(obj, text):
    # find posts that were published with date the same as today,
    # return post ordered by time
    if obj == "User":
        query = """
            MATCH(m:User)
            WHERE LOWER(m.username) CONTAINS {text}
            RETURN m.username as username, m.userid as userid
            LIMIT 20
         """
    elif obj == "Movie":
        query = """
            MATCH(m:Movie)
            WHERE LOWER(m.title) CONTAINS {text}
            RETURN m.title as title, m.year as year, m.overview as text, m.movieID as movieID
            LIMIT 20
         """
    return graph.run(query, text=text)
