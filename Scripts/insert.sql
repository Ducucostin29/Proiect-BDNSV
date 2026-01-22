USE graph_project;


DELETE FROM Directed;
DELETE FROM ActedIn;
DELETE FROM MovieGenres;
DELETE FROM Ratings;
DELETE FROM Friends;
DELETE FROM People;
DELETE FROM Genres;
DELETE FROM Movies;
DELETE FROM Users;


INSERT INTO Users (userId, name, age, city) VALUES
(1, 'Ana',    23, 'Bucharest'),
(2, 'Mihai',  25, 'Cluj'),
(3, 'Ioana',  22, 'Iasi'),
(4, 'Andrei', 30, 'Brasov'),
(5, 'Elena',  27, 'Bucharest');


INSERT INTO Movies (movieId, title, year) VALUES
(1, 'Inception', 2010),
(2, 'Interstellar', 2014),
(3, 'The Matrix', 1999),
(4, 'Avatar', 2009),
(5, 'The Departed', 2006),
(6, 'The Revenant', 2015),
(7, 'The Wolf of Wall Street', 2013),
(8, 'Catch Me If You Can', 2002),
(9, 'Titanic', 1997);


INSERT INTO Genres (name) VALUES
('Sci-Fi'),
('Action'),
('Drama'),
('Crime'),
('Romance'),
('Adventure'),
('Biography');


INSERT INTO MovieGenres (movieId, genre) VALUES
(1, 'Sci-Fi'),
(1, 'Action'),
(2, 'Sci-Fi'),
(2, 'Drama'),
(3, 'Sci-Fi'),
(3, 'Action'),
(4, 'Sci-Fi'),
(4, 'Adventure'),
(5, 'Crime'),
(5, 'Drama'),
(6, 'Drama'),
(6, 'Adventure'),
(7, 'Biography'),
(7, 'Drama'),
(8, 'Crime'),
(8, 'Drama'),
(9, 'Romance'),
(9, 'Drama');


INSERT INTO Friends (userId1, userId2, since_year) VALUES
(1, 2, 2022), (2, 1, 2022),
(2, 3, 2021), (3, 2, 2021),
(3, 4, 2020), (4, 3, 2020),
(4, 5, 2019), (5, 4, 2019);


INSERT INTO Ratings (userId, movieId, rating, ts) VALUES
(1, 1, 5.0,  '2024-01-01 10:00:00'),
(1, 2, 4.5,  '2024-01-02 10:00:00'),
(2, 1, 4.0,  '2024-01-03 10:00:00'),
(2, 3, 5.0,  '2024-01-04 10:00:00'),
(3, 2, 4.0,  '2024-01-05 10:00:00'),
(4, 4, 5.0,  '2024-01-06 10:00:00'),

(2, 5, 4.5,  '2024-01-07 10:00:00'),
(3, 3, 4.5,  '2024-01-08 10:00:00'),
(4, 1, 4.0,  '2024-01-09 10:00:00'),
(5, 2, 4.5,  '2024-01-10 10:00:00'),
(5, 9, 5.0,  '2024-01-11 10:00:00');

-
INSERT INTO People (personId, name) VALUES
(1, 'Leonardo DiCaprio'),
(2, 'Matthew McConaughey'),
(3, 'Keanu Reeves'),
(4, 'Joseph Gordon-Levitt'),
(5, 'Elliot Page'),
(6, 'Tom Hardy'),
(7, 'Kate Winslet'),
(8, 'Matt Damon'),
(9, 'Jonah Hill'),
(10,'Christopher Nolan');


INSERT INTO ActedIn (personId, movieId) VALUES
-- Inception: Leo + JGL + Elliot
(1, 1), (4, 1), (5, 1),
-- Interstellar: Matthew
(2, 2),
-- The Matrix: Keanu
(3, 3),
-- The Departed: Leo + Matt Damon
(1, 5), (8, 5),
-- The Revenant: Leo + Tom Hardy
(1, 6), (6, 6),
-- The Wolf of Wall Street: Leo + Jonah Hill
(1, 7), (9, 7),
-- Catch Me If You Can: Leo + Tom Hardy 
(1, 8), (6, 8),
-- Titanic: Leo + Kate Winslet
(1, 9), (7, 9);


INSERT INTO Directed (personId, movieId) VALUES
(10, 1),
(10, 2);

COMMIT;




