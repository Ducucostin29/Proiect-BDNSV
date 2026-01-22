-- 1)cel mai scurt drum intre 2 persoane

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



-- 2Friends of friends
SELECT DISTINCT u2.userId AS id, u2.name
FROM Friends f1
JOIN Friends f2
  ON f1.userId2 = f2.userId1
JOIN Users u2
  ON u2.userId = f2.userId2
LEFT JOIN Friends direct
  ON direct.userId1 = f1.userId1
 AND direct.userId2 = f2.userId2
WHERE f1.userId1 = 1
  AND f2.userId2 <> 1
  AND direct.userId2 IS NULL
LIMIT 20;

-- 3) recomandari friends of friends
SELECT
  m.title,
  m.year,
  AVG(r.rating) AS score,
  COUNT(*) AS votes
FROM Friends f1
JOIN Friends f2
  ON f1.userId2 = f2.userId1           -- friend-of-friend
JOIN Ratings r
  ON r.userId = f2.userId2             -- x rated movie
JOIN Movies m
  ON m.movieId = r.movieId
LEFT JOIN Ratings my
  ON my.userId = 1 AND my.movieId = r.movieId   -- exclude movies already rated by u
WHERE f1.userId1 = 1
  AND f2.userId2 <> 1
  AND r.rating >= 4
  AND my.movieId IS NULL
GROUP BY m.movieId, m.title, m.year
ORDER BY score DESC, votes DESC
LIMIT 10;


-- 4) utilizatori similari dupa genuri comune
SELECT
  v.userId AS id,
  v.name,
  COUNT(DISTINCT mg2.genre) AS commonGenres
FROM Users v
JOIN Ratings r2
  ON r2.userId = v.userId
JOIN MovieGenres mg2
  ON mg2.movieId = r2.movieId
WHERE v.userId <> 1
  AND mg2.genre IN (
    SELECT DISTINCT mg.genre
    FROM Ratings r
    JOIN MovieGenres mg
      ON mg.movieId = r.movieId
    WHERE r.userId = 1
  )
GROUP BY v.userId, v.name
ORDER BY commonGenres DESC
LIMIT 10;

-- utilizatori dupa genuri comune
SELECT
  v.userId AS id,
  v.name,
  COUNT(DISTINCT r2.movieId) AS common
FROM Users v
JOIN Ratings r2
  ON r2.userId = v.userId
WHERE v.userId <> 1
  AND r2.movieId IN (
    SELECT r.movieId
    FROM Ratings r
    WHERE r.userId = 1
  )
GROUP BY v.userId, v.name
ORDER BY common DESC
LIMIT 10;

-- 6) recomandări din utilizatori similari
WITH neighbors AS (
  SELECT
    r2.userId AS neighbor_id,
    COUNT(DISTINCT r2.movieId) AS commonCount
  FROM Ratings r1
  JOIN Ratings r2
    ON r1.movieId = r2.movieId
  WHERE r1.userId = 1
    AND r2.userId <> 1
  GROUP BY r2.userId
  HAVING commonCount >= 1
)
SELECT
  m.title,
  m.year,
  AVG(r.rating) AS score,
  COUNT(*) AS votes
FROM neighbors n
JOIN Ratings r
  ON r.userId = n.neighbor_id
JOIN Movies m
  ON m.movieId = r.movieId
LEFT JOIN Ratings my
  ON my.userId = 1 AND my.movieId = r.movieId
WHERE r.rating >= 4
  AND my.movieId IS NULL
GROUP BY m.movieId, m.title, m.year
ORDER BY score DESC, votes DESC
LIMIT 10;

-- 7) perechi de actori care au jucat împreună (număr de filme comune)
SELECT
  p1.name AS actor1,
  p2.name AS actor2,
  COUNT(DISTINCT a1.movieId) AS together
FROM ActedIn a1
JOIN ActedIn a2
  ON a1.movieId = a2.movieId
 AND a1.personId < a2.personId        -- evită duplicate (A,B) și (B,A)
JOIN People p1 ON p1.personId = a1.personId
JOIN People p2 ON p2.personId = a2.personId
GROUP BY p1.name, p2.name
ORDER BY together DESC, actor1, actor2
LIMIT 20;


