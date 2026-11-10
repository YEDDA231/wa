from typing import Any, Dict, List, Optional

from database import get_connection


# ---------- Generic helpers ----------

def _execute(query: str, params: tuple = ()) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()


def _fetchall(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def _fetchone(query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------- Veterinarian ----------

def create_vet(data: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO Veterinarian (vetID, vetFName, vetLName, vetAddress, vetSpecial)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["vetID"],
            data["vetFName"],
            data["vetLName"],
            data["vetAddress"],
            data["vetSpecial"],
        ),
    )


def update_vet(vet_id: str, data: Dict[str, Any]) -> None:
    _execute(
        """
        UPDATE Veterinarian
        SET vetFName = ?, vetLName = ?, vetAddress = ?, vetSpecial = ?
        WHERE vetID = ? AND is_deleted = 0
        """,
        (
            data["vetFName"],
            data["vetLName"],
            data["vetAddress"],
            data["vetSpecial"],
            vet_id,
        ),
    )


def logical_delete_vet(vet_id: str) -> None:
    _execute("UPDATE Veterinarian SET is_deleted = 1 WHERE vetID = ?", (vet_id,))


def get_vet(vet_id: str) -> Optional[Dict[str, Any]]:
    return _fetchone(
        "SELECT * FROM Veterinarian WHERE vetID = ? AND is_deleted = 0", (vet_id,)
    )


def search_vets(keyword: str = "") -> List[Dict[str, Any]]:
    if not keyword:
        return _fetchall("SELECT * FROM Veterinarian WHERE is_deleted = 0 ORDER BY vetLName")
    like = f"%{keyword}%"
    return _fetchall(
        """
        SELECT * FROM Veterinarian
        WHERE is_deleted = 0
          AND (vetID LIKE ? OR vetFName LIKE ? OR vetLName LIKE ? OR vetSpecial LIKE ?)
        ORDER BY vetLName
        """,
        (like, like, like, like),
    )


# ---------- PetOwner ----------

def create_owner(data: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO PetOwner (petOwnerID, petOwnerFName, petOwnerLName, petOwnerBDate, petOwnerTelNo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["petOwnerID"],
            data["petOwnerFName"],
            data["petOwnerLName"],
            data["petOwnerBDate"],
            data["petOwnerTelNo"],
        ),
    )


def update_owner(owner_id: str, data: Dict[str, Any]) -> None:
    _execute(
        """
        UPDATE PetOwner
        SET petOwnerFName = ?, petOwnerLName = ?, petOwnerBDate = ?, petOwnerTelNo = ?
        WHERE petOwnerID = ? AND is_deleted = 0
        """,
        (
            data["petOwnerFName"],
            data["petOwnerLName"],
            data["petOwnerBDate"],
            data["petOwnerTelNo"],
            owner_id,
        ),
    )


def logical_delete_owner(owner_id: str) -> None:
    _execute("UPDATE PetOwner SET is_deleted = 1 WHERE petOwnerID = ?", (owner_id,))


def get_owner(owner_id: str):
    return _fetchone(
        "SELECT * FROM PetOwner WHERE petOwnerID = ? AND is_deleted = 0", (owner_id,)
    )


def search_owners(keyword: str = "") -> List[Dict[str, Any]]:
    if not keyword:
        return _fetchall("SELECT * FROM PetOwner WHERE is_deleted = 0 ORDER BY petOwnerLName")
    like = f"%{keyword}%"
    return _fetchall(
        """
        SELECT * FROM PetOwner
        WHERE is_deleted = 0
          AND (petOwnerID LIKE ? OR petOwnerFName LIKE ? OR petOwnerLName LIKE ?)
        ORDER BY petOwnerLName
        """,
        (like, like, like),
    )


# ---------- Pet ----------

def create_pet(data: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO Pet (petID, petName, petType, petSex, petBDate, petOwnerID)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["petID"],
            data["petName"],
            data["petType"],
            data["petSex"],
            data["petBDate"],
            data["petOwnerID"],
        ),
    )


def update_pet(pet_id: str, data: Dict[str, Any]) -> None:
    _execute(
        """
        UPDATE Pet
        SET petName = ?, petType = ?, petSex = ?, petBDate = ?, petOwnerID = ?
        WHERE petID = ? AND is_deleted = 0
        """,
        (
            data["petName"],
            data["petType"],
            data["petSex"],
            data["petBDate"],
            data["petOwnerID"],
            pet_id,
        ),
    )


def logical_delete_pet(pet_id: str) -> None:
    _execute("UPDATE Pet SET is_deleted = 1 WHERE petID = ?", (pet_id,))


def get_pet(pet_id: str):
    return _fetchone("SELECT * FROM Pet WHERE petID = ? AND is_deleted = 0", (pet_id,))


def search_pets(keyword: str = "") -> List[Dict[str, Any]]:
    if not keyword:
        return _fetchall(
            """
            SELECT P.*, O.petOwnerFName, O.petOwnerLName
            FROM Pet P
            LEFT JOIN PetOwner O ON P.petOwnerID = O.petOwnerID
            WHERE P.is_deleted = 0
            ORDER BY P.petName
            """
        )
    like = f"%{keyword}%"
    return _fetchall(
        """
        SELECT P.*, O.petOwnerFName, O.petOwnerLName
        FROM Pet P
        LEFT JOIN PetOwner O ON P.petOwnerID = O.petOwnerID
        WHERE P.is_deleted = 0
          AND (P.petID LIKE ? OR P.petName LIKE ? OR O.petOwnerFName LIKE ? OR O.petOwnerLName LIKE ?)
        ORDER BY P.petName
        """,
        (like, like, like, like),
    )


# ---------- Consultation ----------

def create_consultation(data: Dict[str, Any]) -> None:
    _execute(
        """
        INSERT INTO Consultation (consultID, petID, vetID, consultDate, diagnoses, prescription)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            data["consultID"],
            data["petID"],
            data["vetID"],
            data["consultDate"],
            data["diagnoses"],
            data["prescription"],
        ),
    )


def update_consultation(consult_id: str, data: Dict[str, Any]) -> None:
    _execute(
        """
        UPDATE Consultation
        SET petID = ?, vetID = ?, consultDate = ?, diagnoses = ?, prescription = ?
        WHERE consultID = ? AND is_deleted = 0
        """,
        (
            data["petID"],
            data["vetID"],
            data["consultDate"],
            data["diagnoses"],
            data["prescription"],
            consult_id,
        ),
    )


def logical_delete_consultation(consult_id: str) -> None:
    _execute("UPDATE Consultation SET is_deleted = 1 WHERE consultID = ?", (consult_id,))


def get_consultation(consult_id: str):
    return _fetchone(
        "SELECT * FROM Consultation WHERE consultID = ? AND is_deleted = 0",
        (consult_id,),
    )


def search_consultations(keyword: str = "") -> List[Dict[str, Any]]:
    if not keyword:
        return _fetchall(
            """
            SELECT C.*, P.petName, V.vetFName, V.vetLName
            FROM Consultation C
            LEFT JOIN Pet P ON C.petID = P.petID
            LEFT JOIN Veterinarian V ON C.vetID = V.vetID
            WHERE C.is_deleted = 0
            ORDER BY C.consultDate DESC
            """
        )
    like = f"%{keyword}%"
    return _fetchall(
        """
        SELECT C.*, P.petName, V.vetFName, V.vetLName
        FROM Consultation C
        LEFT JOIN Pet P ON C.petID = P.petID
        LEFT JOIN Veterinarian V ON C.vetID = V.vetID
        WHERE C.is_deleted = 0
          AND (C.consultID LIKE ? OR C.petID LIKE ? OR C.vetID LIKE ?)
        ORDER BY C.consultDate DESC
        """,
        (like, like, like),
    )


# ---------- Inquiry (Reports) ----------

def vets_by_specialization(special: str):
    like = f"%{special}%"
    return _fetchall(
        """
        SELECT vetID,
               vetFName,
               vetLName,
               vetSpecial
        FROM   Veterinarian
        WHERE  is_deleted = 0
           AND vetSpecial LIKE ?
        ORDER BY vetSpecial, vetLName
        """,
        (like,),
    )


def consultations_by_pet(pet_id: str):
    return _fetchall(
        """
        SELECT C.consultID,
               C.consultDate,
               C.diagnoses,
               C.prescription,
               P.petID,
               P.petName,
               V.vetID,
               V.vetFName,
               V.vetLName
        FROM   Consultation C
        JOIN   Pet P
               ON C.petID = P.petID
        JOIN   Veterinarian V
               ON C.vetID = V.vetID
        WHERE  C.is_deleted = 0
           AND C.petID = ?
        ORDER BY C.consultDate DESC
        """,
        (pet_id,),
    )


def consultations_by_owner(owner_id: str):
    return _fetchall(
        """
        SELECT C.consultID,
               C.consultDate,
               C.diagnoses,
               C.prescription,
               P.petID,
               P.petName,
               O.petOwnerID,
               O.petOwnerFName,
               O.petOwnerLName,
               V.vetID,
               V.vetFName,
               V.vetLName
        FROM   Consultation C
        JOIN   Pet P
               ON C.petID = P.petID
        JOIN   PetOwner O
               ON P.petOwnerID = O.petOwnerID
        JOIN   Veterinarian V
               ON C.vetID = V.vetID
        WHERE  C.is_deleted = 0
           AND O.petOwnerID = ?
        ORDER BY C.consultDate DESC
        """,
        (owner_id,),
    )


def consultations_by_vet(vet_id: str):
    return _fetchall(
        """
        SELECT C.consultID,
               C.consultDate,
               C.diagnoses,
               C.prescription,
               P.petID,
               P.petName,
               V.vetID,
               V.vetFName,
               V.vetLName
        FROM   Consultation C
        JOIN   Pet P
               ON C.petID = P.petID
        JOIN   Veterinarian V
               ON C.vetID = V.vetID
        WHERE  C.is_deleted = 0
           AND C.vetID = ?
        ORDER BY C.consultDate DESC
        """,
        (vet_id,),
    )


def consultations_between_dates(date_from: str, date_to: str):
    return _fetchall(
        """
        SELECT C.consultID,
               C.consultDate,
               C.diagnoses,
               C.prescription,
               P.petID,
               P.petName,
               O.petOwnerID,
               O.petOwnerFName,
               O.petOwnerLName,
               V.vetID,
               V.vetFName,
               V.vetLName
        FROM   Consultation C
        JOIN   Pet P
               ON C.petID = P.petID
        JOIN   PetOwner O
               ON P.petOwnerID = O.petOwnerID
        JOIN   Veterinarian V
               ON C.vetID = V.vetID
        WHERE  C.is_deleted = 0
           AND date(C.consultDate) BETWEEN date(?) AND date(?)
        ORDER BY C.consultDate DESC
        """,
        (date_from, date_to),
    )

