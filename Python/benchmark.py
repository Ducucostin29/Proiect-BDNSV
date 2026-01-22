import time
import statistics as stats
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Any

import pandas as pd
from neo4j import GraphDatabase
import mysql.connector


# ---------- CONFIG ----------
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "parola23"   # schimba cu parola ta

MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_USER = "root"       # schimba daca e cazul
MYSQL_PASS = "bubucaru23"       # schimba daca e cazul
MYSQL_DB = "graph_project"

WARMUP = 8
RUNS = 30

@dataclass
class BenchResult:
    db: str
    query_id: str
    run: int
    ms: float
    records: int          # câte rânduri / records
    nodes_returned: int   # câte "noduri" în payload (estimare)


def time_it(fn: Callable[[], Tuple[int, Any]]) -> Tuple[float, int]:
    """Return (ms, rows). fn trebuie sa execute query si sa consume rezultatele."""
    t0 = time.perf_counter()
    rows, _ = fn()
    t1 = time.perf_counter()
    return (t1 - t0) * 1000.0, rows


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["db", "query_id"])

    out = g.agg(
        median_ms=("ms", "median"),
        mean_ms=("ms", "mean"),
        p95_ms=("ms", lambda x: stats.quantiles(x, n=20)[18] if len(x) >= 20 else max(x)),
        min_ms=("ms", "min"),
        max_ms=("ms", "max"),
        runs=("ms", "count"),

        # NOU: rezultate returnate
        median_records=("records", "median"),
        mean_records=("records", "mean"),
        median_nodes_returned=("nodes_returned", "median"),
        mean_nodes_returned=("nodes_returned", "mean"),
    ).reset_index()

    # NOU: metri utili pt raport
    out["median_ms_per_record"] = out["median_ms"] / out["median_records"].replace(0, pd.NA)
    out["median_ms_per_node"] = out["median_ms"] / out["median_nodes_returned"].replace(0, pd.NA)

    return out.sort_values(["query_id", "db"])


# ---------- QUERIES ----------
# Parametri comuni
params = {"uid": 1, "uid2": 5}

# Neo4j Cypher (corelate cu ce ai in proiect)
NEO4J_QUERIES: Dict[str, str] = {
    "Q1_FOF": """
    MATCH (u:User {userId: $uid})-[:FRIEND]->(:User)-[:FRIEND]->(fof:User)
    WHERE u <> fof AND NOT (u)-[:FRIEND]->(fof)
    RETURN DISTINCT fof.userId AS id, fof.name AS name
    LIMIT 20
    """,
    "Q2_SHORTEST": """
    MATCH (a:User {userId: $uid}), (b:User {userId: $uid2})
    MATCH p = shortestPath((a)-[:FRIEND*..10]->(b))
    RETURN length(p) AS hops, [n IN nodes(p) | n.userId] AS path
    """,
    "Q3_FOF_RECS": """
    MATCH (u:User {userId: $uid})-[:FRIEND]->(:User)-[:FRIEND]->(x:User)-[r:RATED]->(m:Movie)
    WHERE r.rating >= 4 AND NOT (u)-[:RATED]->(m) AND u <> x
    RETURN m.title AS title, m.year AS year, avg(r.rating) AS score, count(*) AS votes
    ORDER BY score DESC, votes DESC
    LIMIT 10
    """,
    "Q4_GENRE_SIM": """
    MATCH (u:User {userId: $uid})-[:RATED]->(:Movie)-[:IN_GENRE]->(g:Genre)
    WITH u, collect(DISTINCT g) AS myGenres

    MATCH (v:User)-[:RATED]->(:Movie)-[:IN_GENRE]->(g2:Genre)
    WHERE v <> u AND g2 IN myGenres
    RETURN v.userId AS id, v.name AS name, count(DISTINCT g2) AS commonGenres
    ORDER BY commonGenres DESC
    LIMIT 10
    """,

    "Q5_MOVIE_SIM": """
    MATCH (u:User {userId: $uid})-[:RATED]->(m:Movie)
    WITH u, collect(DISTINCT m) AS myMovies

    MATCH (v:User)-[:RATED]->(m2:Movie)
    WHERE v <> u AND m2 IN myMovies
    RETURN v.userId AS id, v.name AS name, count(DISTINCT m2) AS common
    ORDER BY common DESC
    LIMIT 10
    """,

    "Q6_COLLAB_RECS": """
    MATCH (u:User {userId: $uid})-[:RATED]->(m:Movie)
    MATCH (v:User)-[:RATED]->(m)
    WHERE v <> u
    WITH u, v, count(DISTINCT m) AS commonCount
    WHERE commonCount >= 1

    MATCH (v)-[r:RATED]->(rec:Movie)
    WHERE r.rating >= 4 AND NOT (u)-[:RATED]->(rec)
    RETURN rec.title AS title, rec.year AS year, avg(r.rating) AS score, count(*) AS votes
    ORDER BY score DESC, votes DESC
    LIMIT 10
    """,

    "Q7_COACTORS": """
    MATCH (p1:Person)-[:ACTED_IN]->(m:Movie)<-[:ACTED_IN]-(p2:Person)
    WHERE p1.personId < p2.personId
    RETURN p1.name AS actor1, p2.name AS actor2, count(DISTINCT m) AS together
    ORDER BY together DESC, actor1, actor2
    LIMIT 20
    """
}

# MySQL echivalente (MySQL 8.0+)
MYSQL_QUERIES: Dict[str, str] = {
    "Q1_FOF": """
    SELECT DISTINCT u2.userId AS id, u2.name
    FROM Friends f1
    JOIN Friends f2 ON f1.userId2 = f2.userId1
    JOIN Users u2 ON u2.userId = f2.userId2
    LEFT JOIN Friends direct
      ON direct.userId1 = f1.userId1 AND direct.userId2 = f2.userId2
    WHERE f1.userId1 = %(uid)s
      AND f2.userId2 <> %(uid)s
      AND direct.userId2 IS NULL
    LIMIT 20;
    """,
    "Q2_SHORTEST": """
    WITH RECURSIVE bfs AS (
      SELECT
        %(uid)s AS start_id,
        %(uid)s AS node_id,
        CAST(%(uid)s AS CHAR(1000)) AS path,
        0 AS hops
      UNION ALL
      SELECT
        bfs.start_id,
        f.userId2 AS node_id,
        CONCAT(bfs.path, ',', f.userId2) AS path,
        bfs.hops + 1 AS hops
      FROM bfs
      JOIN Friends f ON f.userId1 = bfs.node_id
      WHERE bfs.hops < 5
        AND FIND_IN_SET(f.userId2, bfs.path) = 0
    )
    SELECT node_id AS target_id, hops, path
    FROM bfs
    WHERE node_id = %(uid2)s
    ORDER BY hops
    LIMIT 1;
    """,
    "Q3_FOF_RECS": """
    SELECT
      m.title,
      m.year,
      AVG(r.rating) AS score,
      COUNT(*) AS votes
    FROM Friends f1
    JOIN Friends f2 ON f1.userId2 = f2.userId1
    JOIN Ratings r ON r.userId = f2.userId2
    JOIN Movies m ON m.movieId = r.movieId
    LEFT JOIN Ratings my
      ON my.userId = %(uid)s AND my.movieId = r.movieId
    WHERE f1.userId1 = %(uid)s
      AND f2.userId2 <> %(uid)s
      AND r.rating >= 4
      AND my.movieId IS NULL
    GROUP BY m.movieId, m.title, m.year
    ORDER BY score DESC, votes DESC
    LIMIT 10;
    """,
    "Q4_GENRE_SIM": """
    SELECT
    v.userId AS id,
    v.name,
    COUNT(DISTINCT mg2.genre) AS commonGenres
    FROM Users v
    JOIN Ratings r2 ON r2.userId = v.userId
    JOIN MovieGenres mg2 ON mg2.movieId = r2.movieId
    WHERE v.userId <> %(uid)s
    AND mg2.genre IN (
        SELECT DISTINCT mg.genre
        FROM Ratings r
        JOIN MovieGenres mg ON mg.movieId = r.movieId
        WHERE r.userId = %(uid)s
    )
    GROUP BY v.userId, v.name
    ORDER BY commonGenres DESC
    LIMIT 10;
    """,

    "Q5_MOVIE_SIM": """
    SELECT
    v.userId AS id,
    v.name,
    COUNT(DISTINCT r2.movieId) AS common
    FROM Users v
    JOIN Ratings r2 ON r2.userId = v.userId
    WHERE v.userId <> %(uid)s
    AND r2.movieId IN (
        SELECT r.movieId
        FROM Ratings r
        WHERE r.userId = %(uid)s
    )
    GROUP BY v.userId, v.name
    ORDER BY common DESC
    LIMIT 10;
    """,

    "Q6_COLLAB_RECS": """
    WITH neighbors AS (
    SELECT
        r2.userId AS neighbor_id,
        COUNT(DISTINCT r2.movieId) AS commonCount
    FROM Ratings r1
    JOIN Ratings r2 ON r1.movieId = r2.movieId
    WHERE r1.userId = %(uid)s
        AND r2.userId <> %(uid)s
    GROUP BY r2.userId
    HAVING commonCount >= 1
    )
    SELECT
    m.title,
    m.year,
    AVG(r.rating) AS score,
    COUNT(*) AS votes
    FROM neighbors n
    JOIN Ratings r ON r.userId = n.neighbor_id
    JOIN Movies m ON m.movieId = r.movieId
    LEFT JOIN Ratings my
    ON my.userId = %(uid)s AND my.movieId = r.movieId
    WHERE r.rating >= 4
    AND my.movieId IS NULL
    GROUP BY m.movieId, m.title, m.year
    ORDER BY score DESC, votes DESC
    LIMIT 10;
    """,

    "Q7_COACTORS": """
    SELECT
      p1.name AS actor1,
      p2.name AS actor2,
      COUNT(DISTINCT a1.movieId) AS together
    FROM ActedIn a1
    JOIN ActedIn a2
      ON a1.movieId = a2.movieId AND a1.personId < a2.personId
    JOIN People p1 ON p1.personId = a1.personId
    JOIN People p2 ON p2.personId = a2.personId
    GROUP BY p1.name, p2.name
    ORDER BY together DESC, actor1, actor2
    LIMIT 20;
    """
}


def bench_neo4j() -> List[BenchResult]:
    results: List[BenchResult] = []
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    with driver.session() as session:
        for qid, cypher in NEO4J_QUERIES.items():
            # warmup
            for _ in range(WARMUP):
                session.run(cypher, params).consume()

            # measured
            for i in range(1, RUNS + 1):
                def run_once():
                    res = session.run(cypher, params)
                    records_list = list(res)   # consumăm
                    summary = res.consume()

                    records_count = len(records_list)

                    # nodes_returned:
                    if qid == "Q2_SHORTEST" and records_count > 0:
                        
                        path_list = records_list[0].get("path", [])
                        nodes_returned = len(path_list)
                    else:
                        nodes_returned = records_count

                    return records_count, nodes_returned, summary


                t0 = time.perf_counter()
                records_count, nodes_returned, _ = run_once()
                t1 = time.perf_counter()
                ms = (t1 - t0) * 1000.0
                results.append(BenchResult("neo4j", qid, i, ms, records_count, nodes_returned))

    driver.close()
    return results


def bench_mysql() -> List[BenchResult]:
    results: List[BenchResult] = []

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        autocommit=True,
    )

    cur = conn.cursor(dictionary=True)
    for qid, sql in MYSQL_QUERIES.items():
        # warmup
        for _ in range(WARMUP):
            cur.execute(sql, params)
            cur.fetchall()

        # measured
        for i in range(1, RUNS + 1):
            def run_once():
                cur.execute(sql, params)
                rows = cur.fetchall()
                records_count = len(rows)

                if qid == "Q2_SHORTEST" and records_count > 0:
                    path_str = rows[0].get("path", "")  # ex: "1,2,4,5"
                    nodes_returned = 0 if not path_str else len(path_str.split(","))
                else:
                    nodes_returned = records_count

                return records_count, nodes_returned


            t0 = time.perf_counter()
            records_count, nodes_returned = run_once()
            t1 = time.perf_counter()
            ms = (t1 - t0) * 1000.0
            results.append(BenchResult("mysql", qid, i, ms, records_count, nodes_returned))

    cur.close()
    conn.close()
    return results


def main():
    all_results: List[BenchResult] = []
    all_results.extend(bench_neo4j())
    all_results.extend(bench_mysql())

    df = pd.DataFrame([r.__dict__ for r in all_results])
    df.to_csv("benchmark_runs.csv", index=False)

    summary = summarize(df)
    summary.to_csv("benchmark_summary.csv", index=False)

    print("\n=== SUMMARY (ms) ===")
    print(summary.to_string(index=False))
    print("\nSaved: benchmark_runs.csv, benchmark_summary.csv")


if __name__ == "__main__":
    main()
