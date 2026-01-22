from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase
import sys


# ----------------------------
# CONFIG
# ----------------------------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "parola23"


# ----------------------------
# QUERIES
# ----------------------------
NEO4J_QUERIES: Dict[str, str] = {
    "Q1_FOF": """
    MATCH (u:User {userId: $uid})-[:FRIEND]->(:User)-[:FRIEND]->(fof:User)
    WHERE u <> fof AND NOT (u)-[:FRIEND]->(fof)
    RETURN DISTINCT fof.userId AS id, fof.name AS name
    LIMIT $limit
    """,

    "Q2_SHORTEST": """
    MATCH (a:User {userId: $uid}), (b:User {userId: $uid2})
    MATCH p = shortestPath((a)-[:FRIEND*..$maxHops]->(b))
    RETURN length(p) AS hops, [n IN nodes(p) | n.userId] AS path
    """,

    "Q3_FOF_RECS": """
    MATCH (u:User {userId: $uid})-[:FRIEND]->(:User)-[:FRIEND]->(x:User)-[r:RATED]->(m:Movie)
    WHERE r.rating >= $minRating
      AND NOT (u)-[:RATED]->(m)
      AND u <> x
    RETURN m.title AS title, m.year AS year, avg(r.rating) AS score, count(*) AS votes
    ORDER BY score DESC, votes DESC
    LIMIT $limit
    """,

    "Q4_GENRE_SIM": """
    MATCH (u:User {userId: $uid})-[:RATED]->(:Movie)-[:IN_GENRE]->(g:Genre)
    WITH u, collect(DISTINCT g) AS myGenres

    MATCH (v:User)-[:RATED]->(:Movie)-[:IN_GENRE]->(g2:Genre)
    WHERE v <> u AND g2 IN myGenres
    RETURN v.userId AS id, v.name AS name, count(DISTINCT g2) AS commonGenres
    ORDER BY commonGenres DESC
    LIMIT $limit
    """,

    "Q5_MOVIE_SIM": """
    MATCH (u:User {userId: $uid})-[:RATED]->(m:Movie)
    WITH u, collect(DISTINCT m) AS myMovies

    MATCH (v:User)-[:RATED]->(m2:Movie)
    WHERE v <> u AND m2 IN myMovies
    RETURN v.userId AS id, v.name AS name, count(DISTINCT m2) AS common
    ORDER BY common DESC
    LIMIT $limit
    """,

    "Q6_COLLAB_RECS": """
    MATCH (u:User {userId: $uid})-[:RATED]->(m:Movie)
    MATCH (v:User)-[:RATED]->(m)
    WHERE v <> u
    WITH u, v, count(DISTINCT m) AS commonCount
    WHERE commonCount >= $minCommon

    MATCH (v)-[r:RATED]->(rec:Movie)
    WHERE r.rating >= $minRating
      AND NOT (u)-[:RATED]->(rec)
    RETURN rec.title AS title, rec.year AS year, avg(r.rating) AS score, count(*) AS votes
    ORDER BY score DESC, votes DESC
    LIMIT $limit
    """,

    "Q7_COACTORS": """
    MATCH (p1:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person)
    WHERE p1.personId < p2.personId
    RETURN p1.name AS actor1, p2.name AS actor2, count(DISTINCT m) AS together
    ORDER BY together DESC, actor1, actor2
    LIMIT $limit
    """
}


# ----------------------------
# INPUT HELPERS
# ----------------------------
def ask_int(prompt: str, default: Optional[int] = None) -> int:
    while True:
        s = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not s and default is not None:
            return default
        try:
            return int(s)
        except ValueError:
            print("Please enter an integer.")


def ask_float(prompt: str, default: Optional[float] = None) -> float:
    while True:
        s = input(f"{prompt}" + (f" [{default}]" if default is not None else "") + ": ").strip()
        if not s and default is not None:
            return default
        try:
            return float(s)
        except ValueError:
            print("Please enter a number.")


def print_table(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("No results.")
        return

    keys = list(rows[0].keys())
    widths = {k: len(k) for k in keys}
    for r in rows:
        for k in keys:
            widths[k] = max(widths[k], len(str(r[k])))

    header = " | ".join(k.ljust(widths[k]) for k in keys)
    sep = "-+-".join("-" * widths[k] for k in keys)
    print(header)
    print(sep)

    for r in rows:
        print(" | ".join(str(r[k]).ljust(widths[k]) for k in keys))


# ----------------------------
# MENU
# ----------------------------
def menu() -> str:
    print("\nNeo4j Query Menu")
    print("1. Q1_FOF - Friends of friends")
    print("2. Q2_SHORTEST - Shortest path")
    print("3. Q3_FOF_RECS - FOF recommendations")
    print("4. Q4_GENRE_SIM - Genre similarity")
    print("5. Q5_MOVIE_SIM - Movie similarity")
    print("6. Q6_COLLAB_RECS - Collaborative filtering")
    print("7. Q7_COACTORS - Co-actors")
    print("0. Exit")
    return input("Choose option: ").strip()


# ----------------------------
# MAIN
# ----------------------------
def main():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as s:
            s.run("RETURN 1").single()
    except Exception as e:
        print("Could not connect to Neo4j.")
        print(e)
        sys.exit(1)

    print("Connected to Neo4j")

    mapping = {
        "1": "Q1_FOF",
        "2": "Q2_SHORTEST",
        "3": "Q3_FOF_RECS",
        "4": "Q4_GENRE_SIM",
        "5": "Q5_MOVIE_SIM",
        "6": "Q6_COLLAB_RECS",
        "7": "Q7_COACTORS",
    }

    while True:
        choice = menu()
        if choice == "0":
            break
        if choice not in mapping:
            print("Invalid option.")
            continue

        qid = mapping[choice]
        params: Dict[str, Any] = {}

        if qid in ("Q1_FOF", "Q3_FOF_RECS", "Q4_GENRE_SIM", "Q5_MOVIE_SIM", "Q6_COLLAB_RECS"):
            params["uid"] = ask_int("User ID", 1)

        if qid == "Q2_SHORTEST":
            params["uid"] = ask_int("Start user ID", 1)
            params["uid2"] = ask_int("Target user ID", 2)
            params["maxHops"] = ask_int("Max hops", 10)

        if qid != "Q2_SHORTEST":
            params["limit"] = ask_int("Limit", 20)

        if qid in ("Q3_FOF_RECS", "Q6_COLLAB_RECS"):
            params["minRating"] = ask_float("Min rating", 4.0)

        if qid == "Q6_COLLAB_RECS":
            params["minCommon"] = ask_int("Min common movies", 1)

        with driver.session() as session:
            result = session.run(NEO4J_QUERIES[qid], params)
            rows = [dict(r) for r in result]

        print("\nResults:")
        print_table(rows)

    driver.close()
    print("Program finished.")


if __name__ == "__main__":
    main()
