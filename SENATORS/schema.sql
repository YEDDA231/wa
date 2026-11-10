-- Philippine National Election
-- Create the database with the sqlite3 tool in this folder:
--   sqlite3.exe Election.db ".read schema.sql"

PRAGMA foreign_keys = ON;

CREATE TABLE Positions (
    posID INTEGER PRIMARY KEY,
    posName TEXT NOT NULL,
    numOfPositions INTEGER NOT NULL CHECK (numOfPositions >= 1),
    posStat TEXT NOT NULL CHECK (posStat IN ('active', 'inactive'))
);

CREATE TABLE Voters (
    voterID TEXT PRIMARY KEY,
    voterPass TEXT NOT NULL,
    voterFName TEXT NOT NULL,
    voterMName TEXT,
    voterLName TEXT NOT NULL,
    voterStat TEXT NOT NULL CHECK (voterStat IN ('active', 'inactive')),
    voted TEXT NOT NULL DEFAULT 'n' CHECK (voted IN ('y', 'n'))
);

CREATE TABLE Candidates (
    candID INTEGER PRIMARY KEY,
    candFName TEXT NOT NULL,
    candMName TEXT,
    candLName TEXT NOT NULL,
    posID INTEGER NOT NULL,
    candStat TEXT NOT NULL CHECK (candStat IN ('active', 'inactive')),
    FOREIGN KEY (posID) REFERENCES Positions (posID)
);

CREATE TABLE Votes (
    posID INTEGER NOT NULL,
    voterID TEXT NOT NULL,
    candID INTEGER NOT NULL,
    PRIMARY KEY (voterID, candID),
    FOREIGN KEY (posID) REFERENCES Positions (posID),
    FOREIGN KEY (voterID) REFERENCES Voters (voterID),
    FOREIGN KEY (candID) REFERENCES Candidates (candID)
);

CREATE INDEX idx_candidates_position ON Candidates (posID);
CREATE INDEX idx_votes_position ON Votes (posID);
CREATE INDEX idx_votes_candidate ON Votes (candID);

INSERT INTO Positions (posID, posName, numOfPositions, posStat) VALUES
    (1, 'President', 1, 'active'),
    (2, 'Vice President', 1, 'active'),
    (3, 'Senator', 12, 'active');

INSERT INTO Voters (voterID, voterPass, voterFName, voterMName, voterLName, voterStat, voted) VALUES
    ('V001', 'election', 'Pedro', 'A', 'Santos', 'active', 'y'),
    ('V002', 'election', 'Rosa', 'B', 'Reyes', 'active', 'y'),
    ('V003', 'election', 'Luis', 'C', 'Garcia', 'active', 'y'),
    ('V004', 'election', 'Ana', 'D', 'Cruz', 'active', 'y'),
    ('V005', 'election', 'Miguel', 'E', 'Torres', 'active', 'y'),
    ('V006', 'election', 'Carmen', 'F', 'Flores', 'active', 'y'),
    ('V007', 'election', 'Jose', 'G', 'Ramos', 'active', 'y'),
    ('V008', 'election', 'Luz', 'H', 'Mendoza', 'active', 'y'),
    ('V009', 'election', 'Rico', 'I', 'Navarro', 'active', 'n'),
    ('V010', 'election', 'Tina', 'J', 'Bautista', 'active', 'n'),
    ('V011', 'election', 'Noel', 'K', 'Diaz', 'inactive', 'n');

INSERT INTO Candidates (candID, candFName, candMName, candLName, posID, candStat) VALUES
    (1, 'Elena', 'M', 'Ramos', 1, 'active'),
    (2, 'Marco', 'L', 'Villanueva', 1, 'active'),
    (3, 'Liza', 'P', 'Navarro', 2, 'active'),
    (4, 'Carlo', 'S', 'Mendoza', 2, 'active'),
    (5, 'Sofia', 'R', 'Reyes', 2, 'active'),
    (6, 'Ramon', 'T', 'Bautista', 3, 'active'),
    (7, 'Benita', 'U', 'Cruz', 3, 'active'),
    (8, 'Paolo', 'V', 'Diaz', 3, 'active'),
    (9, 'Diana', 'W', 'Flores', 3, 'active'),
    (10, 'Ernesto', 'A', 'Garcia', 3, 'active'),
    (11, 'Fe', 'B', 'Hernandez', 3, 'active'),
    (12, 'Gabriel', 'C', 'Ignacio', 3, 'active'),
    (13, 'Hilda', 'D', 'Jimenez', 3, 'active'),
    (14, 'Ivan', 'E', 'Santos', 3, 'active'),
    (15, 'Julia', 'F', 'Torres', 3, 'active'),
    (16, 'Kevin', 'G', 'Uy', 3, 'active'),
    (17, 'Lorna', 'H', 'Yap', 3, 'active'),
    (18, 'Miguel', 'I', 'Zamora', 3, 'active'),
    (19, 'Nina', 'J', 'Alonzo', 3, 'active');

INSERT INTO Votes (posID, voterID, candID) VALUES
    (1, 'V001', 1),
    (1, 'V002', 1),
    (1, 'V003', 1),
    (1, 'V004', 1),
    (1, 'V005', 1),
    (1, 'V006', 2),
    (1, 'V007', 2),
    (1, 'V008', 2),
    (2, 'V001', 3),
    (2, 'V002', 3),
    (2, 'V003', 4),
    (2, 'V004', 4),
    (2, 'V005', 5),
    (2, 'V006', 5),
    (2, 'V007', 5),
    (2, 'V008', 5),
    (3, 'V001', 6),
    (3, 'V001', 7),
    (3, 'V001', 8),
    (3, 'V001', 9),
    (3, 'V001', 10),
    (3, 'V001', 12),
    (3, 'V001', 14),
    (3, 'V001', 16),
    (3, 'V002', 6),
    (3, 'V002', 7),
    (3, 'V002', 8),
    (3, 'V002', 9),
    (3, 'V002', 10),
    (3, 'V002', 12),
    (3, 'V002', 14),
    (3, 'V002', 16),
    (3, 'V003', 6),
    (3, 'V003', 7),
    (3, 'V003', 8),
    (3, 'V003', 9),
    (3, 'V003', 11),
    (3, 'V003', 12),
    (3, 'V003', 14),
    (3, 'V003', 17),
    (3, 'V004', 6),
    (3, 'V004', 7),
    (3, 'V004', 8),
    (3, 'V004', 9),
    (3, 'V004', 11),
    (3, 'V004', 12),
    (3, 'V004', 14),
    (3, 'V004', 17),
    (3, 'V005', 6),
    (3, 'V005', 7),
    (3, 'V005', 8),
    (3, 'V005', 10),
    (3, 'V005', 11),
    (3, 'V005', 13),
    (3, 'V005', 15),
    (3, 'V005', 18),
    (3, 'V006', 6),
    (3, 'V006', 7),
    (3, 'V006', 8),
    (3, 'V006', 10),
    (3, 'V006', 11),
    (3, 'V006', 13),
    (3, 'V006', 15),
    (3, 'V007', 6),
    (3, 'V007', 7),
    (3, 'V007', 9),
    (3, 'V007', 10),
    (3, 'V007', 11),
    (3, 'V007', 13),
    (3, 'V007', 15),
    (3, 'V008', 6),
    (3, 'V008', 8),
    (3, 'V008', 9),
    (3, 'V008', 10),
    (3, 'V008', 12),
    (3, 'V008', 13),
    (3, 'V008', 16);
