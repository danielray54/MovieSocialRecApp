#TODO: COMMENT
from .views import app
from .models import graph
app.static_folder = 'static'
#Uniqueness Contraints
graph.run("CREATE CONSTRAINT ON (n:User) ASSERT n.username IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (m:Movie) ASSERT m.movieID IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (g:Genre) ASSERT g.genreID IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (p:Post) ASSERT p.postid IS UNIQUE")
graph.run("CREATE CONSTRAINT ON (t:Tag) ASSERT t.name IS UNIQUE")
graph.run("CREATE INDEX ON :Post(date)")
