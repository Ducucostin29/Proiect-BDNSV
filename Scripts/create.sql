








-



CREATE TABLE Users (
  userId INT PRIMARY KEY,
  name   VARCHAR(80) NOT NULL,
  age    INT,
  city   VARCHAR(80)
) ENGINE=InnoDB;

CREATE TABLE Movies (
  movieId INT PRIMARY KEY,
  title   VARCHAR(200) NOT NULL,
  year    INT
) ENGINE=InnoDB;

CREATE TABLE Genres (
  name VARCHAR(80) PRIMARY KEY
) ENGINE=InnoDB;

CREATE TABLE People (
  personId INT PRIMARY KEY,
  name     VARCHAR(120) NOT NULL
) ENGINE=InnoDB;

-- 3) Relații (join tables)

-- Prietenii 
CREATE TABLE Friends (
  userId1 INT NOT NULL,
  userId2 INT NOT NULL,
  since_year INT NULL,
  PRIMARY KEY (userId1, userId2),
  CONSTRAINT fk_friends_u1 FOREIGN KEY (userId1) REFERENCES Users(userId)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_friends_u2 FOREIGN KEY (userId2) REFERENCES Users(userId)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Ratinguri user->movie
CREATE TABLE Ratings (
  userId  INT NOT NULL,
  movieId INT NOT NULL,
  rating  FLOAT NOT NULL,
  ts      DATETIME NULL,
  PRIMARY KEY (userId, movieId),
  CONSTRAINT fk_ratings_user FOREIGN KEY (userId) REFERENCES Users(userId)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ratings_movie FOREIGN KEY (movieId) REFERENCES Movies(movieId)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Movie->Genre (un film poate avea mai multe genuri)
CREATE TABLE MovieGenres (
  movieId INT NOT NULL,
  genre   VARCHAR(80) NOT NULL,
  PRIMARY KEY (movieId, genre),
  CONSTRAINT fk_mg_movie FOREIGN KEY (movieId) REFERENCES Movies(movieId)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_mg_genre FOREIGN KEY (genre) REFERENCES Genres(name)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Person->Movie (ACTED_IN)
CREATE TABLE ActedIn (
  personId INT NOT NULL,
  movieId  INT NOT NULL,
  PRIMARY KEY (personId, movieId),
  CONSTRAINT fk_acted_person FOREIGN KEY (personId) REFERENCES People(personId)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_acted_movie FOREIGN KEY (movieId) REFERENCES Movies(movieId)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Person->Movie (DIRECTED)
CREATE TABLE Directed (
  personId INT NOT NULL,
  movieId  INT NOT NULL,
  PRIMARY KEY (personId, movieId),
  CONSTRAINT fk_dir_person FOREIGN KEY (personId) REFERENCES People(personId)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_dir_movie FOREIGN KEY (movieId) REFERENCES Movies(movieId)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4) Indexuri utile
CREATE INDEX idx_users_city ON Users(city);
CREATE INDEX idx_movies_title ON Movies(title);

CREATE INDEX idx_friends_u2 ON Friends(userId2);
CREATE INDEX idx_ratings_movie ON Ratings(movieId);
CREATE INDEX idx_mg_genre ON MovieGenres(genre);

CREATE INDEX idx_people_name ON People(name);

