import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "Election.db")


def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def person_name(first, middle, last):
    parts = []
    for part in (first, middle, last):
        if part and str(part).strip():
            parts.append(str(part).strip())
    return " ".join(parts)


def get_counts():
    conn = connect()
    counts = {
        "positions": conn.execute("SELECT COUNT(*) FROM Positions").fetchone()[0],
        "candidates": conn.execute("SELECT COUNT(*) FROM Candidates").fetchone()[0],
        "voters": conn.execute("SELECT COUNT(*) FROM Voters").fetchone()[0],
        "ballots": conn.execute(
            "SELECT COUNT(*) FROM Voters WHERE voted = 'y'"
        ).fetchone()[0],
    }
    conn.close()
    return counts


def get_positions():
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM Positions ORDER BY posID"
    ).fetchall()
    conn.close()
    return rows


def get_position(pos_id):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM Positions WHERE posID = ?",
        (pos_id,),
    ).fetchone()
    conn.close()
    return row


def add_position(pos_name, num_of_positions, pos_stat):
    conn = connect()
    conn.execute(
        """
        INSERT INTO Positions (posName, numOfPositions, posStat)
        VALUES (?, ?, ?)
        """,
        (pos_name, num_of_positions, pos_stat),
    )
    conn.commit()
    conn.close()


def update_position(pos_id, pos_name, num_of_positions, pos_stat):
    conn = connect()
    conn.execute(
        """
        UPDATE Positions
        SET posName = ?, numOfPositions = ?, posStat = ?
        WHERE posID = ?
        """,
        (pos_name, num_of_positions, pos_stat, pos_id),
    )
    conn.commit()
    conn.close()


def deactivate_position(pos_id):
    conn = connect()
    conn.execute(
        "UPDATE Positions SET posStat = 'inactive' WHERE posID = ?",
        (pos_id,),
    )
    conn.commit()
    conn.close()


def get_candidates():
    conn = connect()
    rows = conn.execute(
        """
        SELECT c.*, p.posName
        FROM Candidates c
        JOIN Positions p ON p.posID = c.posID
        ORDER BY p.posID, c.candLName, c.candFName
        """
    ).fetchall()
    conn.close()
    return rows


def get_candidate(cand_id):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM Candidates WHERE candID = ?",
        (cand_id,),
    ).fetchone()
    conn.close()
    return row


def add_candidate(first, middle, last, pos_id, cand_stat):
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO Candidates
                (candFName, candMName, candLName, posID, candStat)
            VALUES (?, ?, ?, ?, ?)
            """,
            (first, middle, last, pos_id, cand_stat),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("Select a valid position.")
    finally:
        conn.close()


def update_candidate(cand_id, first, middle, last, pos_id, cand_stat):
    conn = connect()
    try:
        current = conn.execute(
            "SELECT posID FROM Candidates WHERE candID = ?",
            (cand_id,),
        ).fetchone()
        if current is None:
            raise ValueError("Candidate not found.")
        if current["posID"] != int(pos_id):
            vote_count = conn.execute(
                "SELECT COUNT(*) FROM Votes WHERE candID = ?",
                (cand_id,),
            ).fetchone()[0]
            if vote_count:
                raise ValueError(
                    "This candidate already has votes, so the position cannot be changed."
                )
        conn.execute(
            """
            UPDATE Candidates
            SET candFName = ?, candMName = ?, candLName = ?, posID = ?, candStat = ?
            WHERE candID = ?
            """,
            (first, middle, last, pos_id, cand_stat, cand_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("Select a valid position.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deactivate_candidate(cand_id):
    conn = connect()
    conn.execute(
        "UPDATE Candidates SET candStat = 'inactive' WHERE candID = ?",
        (cand_id,),
    )
    conn.commit()
    conn.close()


def get_voters():
    conn = connect()
    rows = conn.execute(
        "SELECT * FROM Voters ORDER BY voterID"
    ).fetchall()
    conn.close()
    return rows


def get_voter(voter_id):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM Voters WHERE voterID = ?",
        (voter_id,),
    ).fetchone()
    conn.close()
    return row


def add_voter(voter_id, voter_pass, first, middle, last, voter_stat):
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO Voters
                (voterID, voterPass, voterFName, voterMName, voterLName, voterStat, voted)
            VALUES (?, ?, ?, ?, ?, ?, 'n')
            """,
            (voter_id, voter_pass, first, middle, last, voter_stat),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("That voter ID is already in use.")
    finally:
        conn.close()


def update_voter(voter_id, voter_pass, first, middle, last, voter_stat):
    conn = connect()
    conn.execute(
        """
        UPDATE Voters
        SET voterPass = ?, voterFName = ?, voterMName = ?, voterLName = ?, voterStat = ?
        WHERE voterID = ?
        """,
        (voter_pass, first, middle, last, voter_stat, voter_id),
    )
    conn.commit()
    conn.close()


def deactivate_voter(voter_id):
    conn = connect()
    conn.execute(
        "UPDATE Voters SET voterStat = 'inactive' WHERE voterID = ?",
        (voter_id,),
    )
    conn.commit()
    conn.close()


def authenticate(voter_id, voter_pass):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM Voters WHERE voterID = ? AND voterPass = ?",
        (voter_id, voter_pass),
    ).fetchone()
    conn.close()
    return row


def get_ballot():
    conn = connect()
    positions = conn.execute(
        """
        SELECT * FROM Positions
        WHERE posStat = 'active'
        ORDER BY posID
        """
    ).fetchall()
    ballot = []
    for position in positions:
        candidates = conn.execute(
            """
            SELECT * FROM Candidates
            WHERE posID = ? AND candStat = 'active'
            ORDER BY candLName, candFName
            """,
            (position["posID"],),
        ).fetchall()
        ballot.append({"position": position, "candidates": candidates})
    conn.close()
    return ballot


def cast_votes(voter_id, selections):
    conn = connect()
    try:
        voter = conn.execute(
            "SELECT * FROM Voters WHERE voterID = ?",
            (voter_id,),
        ).fetchone()
        if voter is None:
            raise ValueError("Voter not found.")
        if voter["voterStat"] != "active":
            raise ValueError("Your account is inactive. You cannot vote.")
        if voter["voted"] == "y":
            raise ValueError("You have already voted.")
        if not selections:
            raise ValueError("Select at least one candidate.")

        grouped = {}
        for pos_id, cand_id in selections:
            grouped.setdefault(int(pos_id), []).append(int(cand_id))

        for pos_id, cand_ids in grouped.items():
            if len(cand_ids) != len(set(cand_ids)):
                raise ValueError("A candidate was selected more than once.")
            position = conn.execute(
                "SELECT * FROM Positions WHERE posID = ?",
                (pos_id,),
            ).fetchone()
            if position is None or position["posStat"] != "active":
                raise ValueError("That position is not open for voting.")
            if len(cand_ids) > position["numOfPositions"]:
                raise ValueError(
                    "You may vote for at most "
                    f"{position['numOfPositions']} candidate(s) for {position['posName']}."
                )
            for cand_id in cand_ids:
                candidate = conn.execute(
                    """
                    SELECT candID FROM Candidates
                    WHERE candID = ? AND posID = ? AND candStat = 'active'
                    """,
                    (cand_id, pos_id),
                ).fetchone()
                if candidate is None:
                    raise ValueError("One of the selected candidates is not available.")

        try:
            for pos_id, cand_ids in grouped.items():
                for cand_id in cand_ids:
                    conn.execute(
                        """
                        INSERT INTO Votes (posID, voterID, candID)
                        VALUES (?, ?, ?)
                        """,
                        (pos_id, voter_id, cand_id),
                    )
            updated = conn.execute(
                """
                UPDATE Voters
                SET voted = 'y'
                WHERE voterID = ? AND voted = 'n' AND voterStat = 'active'
                """,
                (voter_id,),
            )
            if updated.rowcount != 1:
                raise ValueError("You have already voted.")
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError("Your ballot could not be saved.")
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.close()


def get_results():
    conn = connect()
    rows = conn.execute(
        """
        SELECT
            p.posID,
            p.posName,
            p.numOfPositions,
            p.posStat,
            c.candID,
            c.candFName,
            c.candMName,
            c.candLName,
            c.candStat,
            COUNT(v.candID) AS totalVotes
        FROM Positions p
        LEFT JOIN Candidates c ON c.posID = p.posID
        LEFT JOIN Votes v ON v.candID = c.candID AND v.posID = p.posID
        GROUP BY p.posID, c.candID
        ORDER BY p.posID, totalVotes DESC, c.candLName, c.candFName
        """
    ).fetchall()
    conn.close()

    blocks = []
    index = {}
    for row in rows:
        pos_id = row["posID"]
        if pos_id not in index:
            block = {
                "posID": pos_id,
                "posName": row["posName"],
                "numOfPositions": row["numOfPositions"],
                "posStat": row["posStat"],
                "candidates": [],
                "votesCast": 0,
            }
            index[pos_id] = block
            blocks.append(block)
        if row["candID"] is None:
            continue
        block = index[pos_id]
        total_votes = row["totalVotes"]
        block["votesCast"] += total_votes
        block["candidates"].append(
            {
                "candID": row["candID"],
                "name": person_name(row["candFName"], row["candMName"], row["candLName"]),
                "candStat": row["candStat"],
                "totalVotes": total_votes,
            }
        )

    for block in blocks:
        total = block["votesCast"]
        for candidate in block["candidates"]:
            if total:
                candidate["percentage"] = round(candidate["totalVotes"] * 100 / total, 2)
            else:
                candidate["percentage"] = 0
    return blocks


def get_winners():
    winners = []
    for block in get_results():
        seated = block["candidates"][: block["numOfPositions"]]
        for candidate in seated:
            winners.append(
                {
                    "posName": block["posName"],
                    "name": candidate["name"],
                    "totalVotes": candidate["totalVotes"],
                }
            )
    return winners
