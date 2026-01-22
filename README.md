# Graph Databases vs Relational Databases
## Comparative Study using Neo4j and MySQL

---

## Project Overview

This project presents a comparative analysis between **graph databases** and **relational databases**, focusing on their ability to model, query, and analyze highly connected data.

The study is conducted using:
- **Neo4j** (graph database)
- **MySQL 8.0** (relational database)
- **Python** for data generation, integration, and benchmarking

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

  The script used for creating the nodes, the relationships and the initial data can be found in the Scripts folder: createNeo4j.txt

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

The script used for creating the table is create.sql
