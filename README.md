# Graph Databases vs Relational Databases
## Comparative Study using Neo4j and MySQL

---

## Project Overview

This project presents a comparative analysis between **graph databases** and **relational databases**, focusing on their ability to model, query, and analyze highly connected data.

The study is conducted using:
- **Neo4j** (graph database)
- **MySQL 8.0.44** (relational database)
- **Python** for data generation, integration, and benchmarking

 ## Python Libraries Used

The following Python libraries were used throughout the project:

- **neo4j** — used to connect to the Neo4j database and execute Cypher queries via the Bolt protocol  
- **mysql-connector-python** — used to connect to MySQL and execute SQL queries programmatically  
- **random** — used for synthetic data generation  
- **dataclasses** — used for structured storage of benchmark results  
- **time** — used for measuring query execution time  
- **statistics** — used for computing performance metrics (median, mean, percentiles)  
- **csv** — used to export benchmark results to CSV files

## AI tools usage
ChatGPT has been used for the following tasks:
- generating the code for the sql tables, after being given their description
- generating the initial data for both databases
- generating parts of the python code (especially for the randomly generated data for inserting in the database)
- generating a chart for data in the .csv files

The main objective is to evaluate **query expressiveness**, **readability**, and **performance**, especially for graph-oriented operations such as traversal and shortest path queries.

---
## Data Model

### Graph Model (Neo4j)

**Node types:**
- User
- Movie
- Genre
- Person

**Relationship types:**
- FRIEND
- RATED
- IN_GENRE
- ACTED_IN
- DIRECTED

  
<img width="850" height="644" alt="sql_erd" src="https://github.com/user-attachments/assets/5e94e965-bc31-46fd-827f-a01ce7007032" />

  The script used for creating the nodes, the relationships and the initial data can be found in the Scripts folder: [createNeo4j.txt](Scripts/createNeo4j.txt)

  ---

### Relational Model (MySQL)

**Core tables:**
- Users
- Movies
- Genres
- People

**Relationship tables:**
- Friends
- Ratings
- MovieGenres
- ActedIn
- Directed

<img width="685" height="622" alt="visualisation" src="https://github.com/user-attachments/assets/ffcf2ff9-1e99-4c44-bd60-297c838fe85e" />

The relational schema mirrors the graph structure using foreign keys and join tables.

The script used for creating the table is [create.sql](Scripts/create.sql)

---
## Implemented Queries

The following queries were implemented in both databases:

1. Friends-of-Friends (FOF)
2. Shortest Path between users
3. Friends-of-Friends movie recommendations
4. Genre-based user similarity
5. Movie-based user similarity
6. Collaborative filtering recommendations
7. Co-actors detection

  The SQL queries can be found in [queries.sql](Scripts/queries.sql).  
  The Neo4j queries can be found in [queriesNeo4.txt](Scripts/queriesNeo4j.txt).

  # Example of an sql query compared to the equivalent Neo4j query:
  
  Shortest Path between users

SQL:
  ```sql
WITH RECURSIVE bfs AS (
  -- nivel 0: start (nodul 1)
  SELECT
    2 AS start_id,
    2 AS node_id,
    CAST('2' AS CHAR(1000)) AS path,
    0 AS hops
  UNION ALL

  -- extindere BFS
  SELECT
    bfs.start_id,
    f.userId2 AS node_id,
    CONCAT(bfs.path, ',', f.userId2) AS path,
    bfs.hops + 1 AS hops
  FROM bfs
  JOIN Friends f
    ON f.userId1 = bfs.node_id
  WHERE bfs.hops < 5
    AND FIND_IN_SET(f.userId2, bfs.path) = 0   
)
SELECT node_id AS target_id, hops, path
FROM bfs
WHERE node_id = 4
ORDER BY hops
LIMIT 1;

```


CYPHER:
```cypher
MATCH (a:User {userId: 1}), (b:User {userId: 5})
MATCH p = shortestPath((a)-[:FRIEND*..10]->(b))
RETURN p, length(p) AS hops;

```
The SQL solution requires complex recursive logic to compute the shortest path, while Neo4j provides a clear and concise query using native graph traversal.

## Performance Comparison

To evaluate the performance of relational and graph databases, a benchmark was conducted using a Python-based testing framework.  
Each query was executed 30 times, and the following metrics were collected:

- median execution time (ms)
- mean execution time (ms)
- number of returned records
- execution cost per returned node

Two datasets were used:
- **Small dataset** – used for functional validation
- **Large dataset** – used to analyze scalability and traversal cost

---

## Dataset Generation

The datasets used in this benchmark were generated using a Python script : [benchmark.py](Python/benchmark.py).  
The generator creates users, movies, genres, people (actors and directors), and their relationships using randomized but controlled distributions in order to simulate realistic social and movie-recommendation scenarios.

The same generated data is inserted into both MySQL and Neo4j, ensuring a fair and consistent comparison between the two database systems.

The data generation and insertion logic can be found in the following script:

[insert_generate.py](Python/insert_generate.py)

### Small Dataset Results

| Query | Database | Median Time (ms) | Mean Time (ms) | Returned Records |
|------|----------|------------------|----------------|------------------|
| Q1 – Friends of Friends | MySQL | 0.30 | 0.31 | 20 |
| Q1 – Friends of Friends | Neo4j | 1.22 | 1.26 | 20 |
| Q2 – Shortest Path | MySQL | 0.34 | 0.36 | 1 |
| Q2 – Shortest Path | Neo4j | 1.93 | 1.91 | 1 |
| Q3 – FOF Recommendations | MySQL | 0.36 | 0.37 | 10 |
| Q3 – FOF Recommendations | Neo4j | 1.59 | 1.64 | 10 |
| Q4 – Genre Similarity | MySQL | 0.54 | 0.54 | 10 |
| Q4 – Genre Similarity | Neo4j | 1.76 | 1.92 | 10 |
| Q5 – Movie Similarity | MySQL | 0.37 | 0.39 | 10 |
| Q5 – Movie Similarity | Neo4j | 1.29 | 1.27 | 10 |
| Q6 – Collaborative Recommendations | MySQL | 0.53 | 0.56 | 10 |
| Q6 – Collaborative Recommendations | Neo4j | 1.78 | 1.87 | 10 |
| Q7 – Co-actors | MySQL | 0.40 | 0.40 | 20 |
| Q7 – Co-actors | Neo4j | 1.71 | 1.78 | 20 |

---

### Large Dataset Results

| Query | Database | Median Time (ms) | Mean Time (ms) | Returned Records |
|------|----------|------------------|----------------|------------------|
| Q1 – Friends of Friends | MySQL | 0.54 | 0.56 | 20 |
| Q1 – Friends of Friends | Neo4j | 2.46 | 2.56 | 20 |
| Q2 – Shortest Path | MySQL | 255.22 | 258.15 | 1 |
| Q2 – Shortest Path | Neo4j | 2.81 | 2.80 | 1 |
| Q3 – FOF Recommendations | MySQL | 2.01 | 2.03 | 10 |
| Q3 – FOF Recommendations | Neo4j | 4.37 | 4.37 | 10 |
| Q4 – Genre Similarity | MySQL | 662.14 | 663.42 | 10 |
| Q4 – Genre Similarity | Neo4j | 340.12 | 343.03 | 10 |
| Q5 – Movie Similarity | MySQL | 1.15 | 1.12 | 10 |
| Q5 – Movie Similarity | Neo4j | 3.77 | 4.02 | 10 |
| Q6 – Collaborative Recommendations | MySQL | 6.72 | 7.56 | 10 |
| Q6 – Collaborative Recommendations | Neo4j | 11.82 | 12.80 | 10 |
| Q7 – Co-actors | MySQL | 167.41 | 166.99 | 20 |
| Q7 – Co-actors | Neo4j | 91.02 | 88.45 | 20 |

### Large Dataset Characteristics

The large dataset used for performance evaluation contains the following approximate sizes:

- 20,000 users  
- 5,000 movies  
- 20 genres  
- 8,000 people (actors and directors)  
- ~200,000 friendship relationships  
- ~200,000 movie ratings  
- ~20,000 ACTED_IN relationships  
- 5,000 DIRECTED relationships  

---

### Interpretation

The benchmark results highlight clear performance differences depending on query type.

- MySQL performs better for simple join-based queries and shallow relationships.
- Neo4j significantly outperforms MySQL for graph traversal operations, especially shortest path queries.
- As dataset size increases, recursive SQL queries become considerably more expensive.
- Graph databases scale better with relationship depth and connectivity.
- Query structure and relationship traversal have a stronger impact on performance than raw data volume.

These results confirm that graph databases are better suited for highly connected data, while relational databases remain efficient for structured and local queries.

### Graph Query Interface

A command-line interface was implemented in Python to allow interactive execution of Neo4j queries.  
The interface enables users to select predefined graph queries from a menu, provide input node identifiers at runtime, and visualize the query results directly in the terminal.

This component demonstrates the integration of Neo4j with an external programming API and allows dynamic exploration of the graph database without using the Neo4j Browser.

The implementation of the interface can be found here:

[neo4j_cli.py](Python/neo4j_cli.py)

A video demonstration of the Neo4j database, of the Mysql database, and of the Python interface can be found here:
https://youtu.be/YUyrAiChB9A
