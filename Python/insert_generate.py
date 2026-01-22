import random
from dataclasses import dataclass
from typing import List, Tuple
from tqdm import tqdm

from neo4j import GraphDatabase
import mysql.connector

# ---------------- CONFIG ----------------
SEED = 42
random.seed(SEED)

# Dimensiuni dataset (începe cu astea, apoi crești)
N_USERS = 20000
N_MOVIES = 5000
N_GENRES = 20

AVG_FRIENDS = 10          # prieteni medii per user (neorientat)
RATINGS_PER_USER = 10     # câte filme evaluează în medie un user


BATCH = 5000

N_PEOPLE = 8000
ACTORS_PER_MOVIE_MIN = 2
ACTORS_PER_MOVIE_MAX = 6


# Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "parola23"

# MySQL
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASS = "bubucaru23"
MYSQL_DB = "graph_project"

# ---------------- Helpers ----------------
def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

# ---------------- Generate synthetic data ----------------
def gen_users(n: int):
    cities = ["Bucharest", "Cluj", "Iasi", "Brasov", "Timisoara", "Constanta", "Oradea"]
    out = []
    for uid in range(1, n+1):
        out.append((uid, f"User{uid}", random.randint(18, 55), random.choice(cities)))
    return out

def gen_movies(n: int):
    out = []
    for mid in range(1, n+1):
        out.append((mid, f"Movie{mid}", random.randint(1980, 2024)))
    return out

def gen_genres(n: int):
    return [f"Genre{i}" for i in range(1, n+1)]

def gen_movie_genres(n_movies: int, genres: List[str]):
    out = []
    for mid in range(1, n_movies+1):
        # 1-3 genuri per film
        gs = random.sample(genres, k=random.randint(1, 3))
        for g in gs:
            out.append((mid, g))
    return out

def gen_friend_edges(n_users: int, avg_friends: int):
    # Generăm muchii neorientate ca perechi (a<b), apoi le duplicăm pentru (a->b) și (b->a)
    target_edges = n_users * avg_friends // 2
    edges = set()
    while len(edges) < target_edges:
        a = random.randint(1, n_users)
        b = random.randint(1, n_users)
        if a == b: 
            continue
        if a > b: 
            a, b = b, a
        edges.add((a, b))
    # dublare direcțională (exact ca schema SQL Friends bidirecțională și Neo4j FRIEND ambele sensuri)
    out = []
    for (a, b) in edges:
        since = random.randint(2015, 2025)
        out.append((a, b, since))
        out.append((b, a, since))
    return out

def gen_ratings(n_users: int, n_movies: int, ratings_per_user: int):
    out = []
    for uid in range(1, n_users+1):
        # evităm duplicate (uid, movieId)
        movies = random.sample(range(1, n_movies+1), k=ratings_per_user)
        for mid in movies:
            rating = random.choice([1,2,3,4,5])  # discret, simplu
            out.append((uid, mid, float(rating)))
    return out

def gen_people(n: int):
    out = []
    for pid in range(1, n + 1):
        out.append((pid, f"Person{pid}"))
    return out

def gen_acted_in(n_movies: int, n_people: int):
    out = []
    for mid in range(1, n_movies + 1):
        k = random.randint(ACTORS_PER_MOVIE_MIN, ACTORS_PER_MOVIE_MAX)
        actors = random.sample(range(1, n_people + 1), k)
        for pid in actors:
            out.append((pid, mid))
    return out

def gen_directed(n_movies: int, n_people: int):
    out = []
    for mid in range(1, n_movies + 1):
        director = random.randint(1, n_people)
        out.append((director, mid))
    return out


# ---------------- MySQL load ----------------
def mysql_connect():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASS,
        database=MYSQL_DB, autocommit=False
    )

def mysql_reset(cur):
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in ["Directed","ActedIn","MovieGenres","Ratings","Friends","People","Genres","Movies","Users"]:
        cur.execute(f"TRUNCATE TABLE {t}")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")


def load_mysql(users, movies, genres, movie_genres, friends, ratings, people, acted_in, directed):

    conn = mysql_connect()
    cur = conn.cursor()

    print("MySQL: reset...")
    mysql_reset(cur)
    conn.commit()

    print("MySQL: insert Users...")
    for batch in tqdm(list(chunked(users, BATCH))):
        cur.executemany("INSERT INTO Users(userId,name,age,city) VALUES(%s,%s,%s,%s)", batch)
    conn.commit()

    print("MySQL: insert Movies...")
    for batch in tqdm(list(chunked(movies, BATCH))):
        cur.executemany("INSERT INTO Movies(movieId,title,year) VALUES(%s,%s,%s)", batch)
    conn.commit()
    
    print("MySQL: insert People...")
    for batch in tqdm(list(chunked(people, BATCH))):
        cur.executemany("INSERT INTO People(personId,name) VALUES(%s,%s)", batch)
    conn.commit()


    print("MySQL: insert Genres...")
    cur.executemany("INSERT INTO Genres(name) VALUES(%s)", [(g,) for g in genres])
    conn.commit()

    print("MySQL: insert MovieGenres...")
    for batch in tqdm(list(chunked(movie_genres, BATCH))):
        cur.executemany("INSERT INTO MovieGenres(movieId,genre) VALUES(%s,%s)", batch)
    conn.commit()

    print("MySQL: insert ActedIn...")
    for batch in tqdm(list(chunked(acted_in, BATCH))):
        cur.executemany("INSERT INTO ActedIn(personId,movieId) VALUES(%s,%s)", batch)
    conn.commit()

    print("MySQL: insert Directed...")
    for batch in tqdm(list(chunked(directed, BATCH))):
        cur.executemany("INSERT INTO Directed(personId,movieId) VALUES(%s,%s)", batch)
    conn.commit()

    
    print("MySQL: insert Friends...")
    for batch in tqdm(list(chunked(friends, BATCH))):
        cur.executemany("INSERT INTO Friends(userId1,userId2,since_year) VALUES(%s,%s,%s)", batch)
    conn.commit()

    print("MySQL: insert Ratings...")
    for batch in tqdm(list(chunked(ratings, BATCH))):
        cur.executemany("INSERT INTO Ratings(userId,movieId,rating) VALUES(%s,%s,%s)", batch)
    conn.commit()

    cur.close()
    conn.close()

# ---------------- Neo4j load ----------------
def load_neo4j(users, movies, genres, movie_genres, friends, ratings, people, acted_in, directed):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as s:
        print("Neo4j: reset...")
        s.run("""
        MATCH (n)
        CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS
        """).consume()

        # constraints
        s.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.userId IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT movie_id IF NOT EXISTS FOR (m:Movie) REQUIRE m.movieId IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.personId IS UNIQUE").consume()


        print("Neo4j: insert Users...")
        q_users = """
        UNWIND $rows AS r
        MERGE (u:User {userId: r.userId})
        SET u.name=r.name, u.age=r.age, u.city=r.city
        """
        for batch in tqdm(list(chunked(
            [{"userId":u[0],"name":u[1],"age":u[2],"city":u[3]} for u in users], 2000
        ))):
            s.run(q_users, rows=batch).consume()

        print("Neo4j: insert Movies...")
        q_movies = """
        UNWIND $rows AS r
        MERGE (m:Movie {movieId: r.movieId})
        SET m.title=r.title, m.year=r.year
        """
        for batch in tqdm(list(chunked(
            [{"movieId":m[0],"title":m[1],"year":m[2]} for m in movies], 2000
        ))):
            s.run(q_movies, rows=batch).consume()
            
        print("Neo4j: insert People...")
        q_people = """
        UNWIND $rows AS r
        MERGE (p:Person {personId: r.personId})
        SET p.name = r.name
        """
        for batch in tqdm(list(chunked(
            [{"personId":p[0], "name":p[1]} for p in people], 2000
        ))):
            s.run(q_people, rows=batch).consume()


        print("Neo4j: insert Genres...")
        q_genres = "UNWIND $rows AS g MERGE (:Genre {name: g})"
        for batch in tqdm(list(chunked(genres, 5000))):
            s.run(q_genres, rows=batch).consume()

        print("Neo4j: insert MovieGenres...")
        q_mg = """
        UNWIND $rows AS r
        MATCH (m:Movie {movieId:r.movieId})
        MATCH (g:Genre {name:r.genre})
        MERGE (m)-[:IN_GENRE]->(g)
        """
        for batch in tqdm(list(chunked(
            [{"movieId":mg[0],"genre":mg[1]} for mg in movie_genres], 5000
        ))):
            s.run(q_mg, rows=batch).consume()

        print("Neo4j: insert ActedIn...")
        q_act = """
        UNWIND $rows AS r
        MATCH (p:Person {personId:r.personId})
        MATCH (m:Movie {movieId:r.movieId})
        MERGE (p)-[:ACTED_IN]->(m)
        """
        for batch in tqdm(list(chunked(
            [{"personId":a[0], "movieId":a[1]} for a in acted_in], 5000
        ))):
            s.run(q_act, rows=batch).consume()

        print("Neo4j: insert Directed...")
        q_dir = """
        UNWIND $rows AS r
        MATCH (p:Person {personId:r.personId})
        MATCH (m:Movie {movieId:r.movieId})
        MERGE (p)-[:DIRECTED]->(m)
        """
        for batch in tqdm(list(chunked(
            [{"personId":d[0], "movieId":d[1]} for d in directed], 5000
        ))):
            s.run(q_dir, rows=batch).consume()


        print("Neo4j: insert Friends...")
        q_f = """
        UNWIND $rows AS r
        MATCH (a:User {userId:r.a})
        MATCH (b:User {userId:r.b})
        MERGE (a)-[rel:FRIEND]->(b)
        SET rel.since_year = r.since
        """
        for batch in tqdm(list(chunked(
            [{"a":f[0],"b":f[1],"since":f[2]} for f in friends], 5000
        ))):
            s.run(q_f, rows=batch).consume()

        print("Neo4j: insert Ratings...")
        q_r = """
        UNWIND $rows AS r
        MATCH (u:User {userId:r.userId})
        MATCH (m:Movie {movieId:r.movieId})
        MERGE (u)-[rel:RATED]->(m)
        SET rel.rating = r.rating
        """
        for batch in tqdm(list(chunked(
            [{"userId":r[0],"movieId":r[1],"rating":r[2]} for r in ratings], 5000
        ))):
            s.run(q_r, rows=batch).consume()

    driver.close()

def main():
    print("Generating data...")

    users = gen_users(N_USERS)
    movies = gen_movies(N_MOVIES)
    genres = gen_genres(N_GENRES)
    movie_genres = gen_movie_genres(N_MOVIES, genres)

    friends = gen_friend_edges(N_USERS, AVG_FRIENDS)
    ratings = gen_ratings(N_USERS, N_MOVIES, RATINGS_PER_USER)

    people = gen_people(N_PEOPLE)
    acted_in = gen_acted_in(N_MOVIES, N_PEOPLE)
    directed = gen_directed(N_MOVIES, N_PEOPLE)

    print(
        f"Users={len(users)} "
        f"Movies={len(movies)} "
        f"Genres={len(genres)} "
        f"MovieGenres={len(movie_genres)} "
        f"Friends(dir)={len(friends)} "
        f"Ratings={len(ratings)} "
        f"People={len(people)} "
        f"ActedIn={len(acted_in)} "
        f"Directed={len(directed)}"
    )

    print("\nLoading MySQL...")
    load_mysql(
        users,
        movies,
        genres,
        movie_genres,
        friends,
        ratings,
        people,
        acted_in,
        directed
    )

    print("\nLoading Neo4j...")
    load_neo4j(
        users,
        movies,
        genres,
        movie_genres,
        friends,
        ratings,
        people,
        acted_in,
        directed
    )

    print("\nDone.")
    
if __name__ == "__main__":
    main()

