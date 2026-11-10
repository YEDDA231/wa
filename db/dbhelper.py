from sqlite3 import connect,Row

# (-----------------) edit db
database:str = "db/skills.db"
# (-----------------) end

# (-----------------) edit logins
SEED_USERS:list = [
    {"email":"alpha@uc.com","password":"hello123"},
    {"email":"bravo@uc.com","password":"hello123"},
    {"email":"charlie@uc.com","password":"hello123"},
    {"email":"delta@uc.com","password":"hello123"},
]
# (-----------------) end

# function to retrieving data
def getprocess(sql:str,vals:list)->list:
    conn:any = None
    cursor:any = None
    data:list = []
    try:
        conn = connect(database)
        conn.row_factory = Row
        cursor = conn.cursor()
        cursor.execute(sql,vals)
        data = cursor.fetchall()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    return data

# function for putting,updating,deleting data
def postprocess(sql:str,vals:list)->bool:
    conn:any = None
    cursor:any = None
    ok:bool = False
    try:
        conn = connect(database)
        cursor = conn.cursor()
        cursor.execute(sql,vals)
        conn.commit()
        ok = cursor.rowcount > 0
    except Exception as e:
        if conn is not None:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    return ok

# function to get all data from a table
def getall(table:str)->list:
    sql:str = f"SELECT * FROM `{table}` ORDER BY id"
    return getprocess(sql,[])

# function to get a specific data from a table
def getrecord(table:str,**kwargs)->list:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    flds:list = []
    for key in keys:
        flds.append("`"+key+"`=?")
    fld:str = " AND ".join(flds)
    sql:str = f"SELECT * FROM `{table}` WHERE {fld}"
    return getprocess(sql,vals)

# function for searching rows by keyword
def searchrecord(table:str,columns:list,keyword:str)->list:
    if keyword == "":
        return getall(table)
    parts:list = []
    vals:list = []
    like:str = "%"+keyword+"%"
    for column in columns:
        parts.append("`"+column+"` LIKE ?")
        vals.append(like)
    sql:str = f"SELECT * FROM `{table}` WHERE {' OR '.join(parts)} ORDER BY id"
    return getprocess(sql,vals)

# (-----------------) edit item search
def getinventory(keyword:str="")->list:
    sql:str = """SELECT p.id,p.sku,p.name,p.category_id,p.supplier_id,p.price,p.quantity,p.unit,
        c.name AS category,s.name AS supplier
        FROM products p
        LEFT JOIN categories c ON c.id=p.category_id
        LEFT JOIN suppliers s ON s.id=p.supplier_id"""
    vals:list = []
    if keyword != "":
        sql += " WHERE p.sku LIKE ? OR p.name LIKE ? OR IFNULL(c.name,'') LIKE ? OR IFNULL(s.name,'') LIKE ? OR IFNULL(p.unit,'') LIKE ?"
        like:str = "%"+keyword+"%"
        vals = [like,like,like,like,like]
    sql += " ORDER BY p.name"
    return getprocess(sql,vals)
# (-----------------) end

# (-----------------) edit log search
def getstocklogs(keyword:str="")->list:
    sql:str = """SELECT l.id,l.product_id,l.change_qty,l.action,l.note,l.created_at,
        p.sku,p.name AS product
        FROM stock_logs l
        LEFT JOIN products p ON p.id=l.product_id"""
    vals:list = []
    if keyword != "":
        sql += " WHERE IFNULL(p.sku,'') LIKE ? OR IFNULL(p.name,'') LIKE ? OR l.action LIKE ? OR IFNULL(l.note,'') LIKE ?"
        like:str = "%"+keyword+"%"
        vals = [like,like,like,like]
    sql += " ORDER BY l.id DESC"
    return getprocess(sql,vals)
# (-----------------) end

# function for deleting data
def deleterecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    flds:list = []
    for key in keys:
        flds.append("`"+key+"`=?")
    fld:str = " AND ".join(flds)
    sql:str = f"DELETE FROM `{table}` WHERE {fld}"
    return postprocess(sql,vals)

# function for adding data
def addrecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    qmark:str = ",".join(["?"]*len(keys))
    flds:str = "`,`".join(keys)
    sql:str = f"INSERT INTO `{table}`(`{flds}`) VALUES({qmark})"
    return postprocess(sql,vals)

# function for updating data. first field is the WHERE key.
def updaterecord(table:str,**kwargs)->bool:
    keys:list = list(kwargs.keys())
    vals:list = list(kwargs.values())
    flds:list = []
    newvals:list = []
    for i in range(1,len(keys)):
        flds.append("`"+keys[i]+"`=?")
        newvals.append(vals[i])
    fld:str = ",".join(flds)
    sql:str = f"UPDATE `{table}` SET {fld} WHERE `{keys[0]}`=?"
    newvals.append(vals[0])
    return postprocess(sql,newvals)

# (-----------------) edit tables
def initdb()->None:
    conn:any = None
    cursor:any = None
    try:
        conn = connect(database)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email varchar(50) UNIQUE,
                password varchar(25)
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                supplier_id INTEGER,
                price REAL NOT NULL DEFAULT 0,
                quantity INTEGER NOT NULL DEFAULT 0,
                unit TEXT DEFAULT 'pcs'
            );
            CREATE TABLE IF NOT EXISTS stock_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                change_qty INTEGER NOT NULL,
                action TEXT NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        # (-----------------) end
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    seed()

# (-----------------) edit seed
def seed()->None:
    conn:any = None
    cursor:any = None
    try:
        conn = connect(database)
        cursor = conn.cursor()
        for account in SEED_USERS:
            cursor.execute("SELECT id FROM users WHERE email=?",(account["email"],))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO users(email,password) VALUES(?,?)",
                    (account["email"],account["password"])
                )
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            categories:list = ["Electronics","Office","Tools"]
            for name in categories:
                cursor.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)",(name,))
            suppliers:list = [
                ("North Supply","555-0101","north@supply.com"),
                ("Metro Goods","555-0199","metro@goods.com"),
            ]
            for name,contact,email in suppliers:
                cursor.execute("SELECT id FROM suppliers WHERE name=?",(name,))
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO suppliers(name,contact,email) VALUES(?,?,?)",
                        (name,contact,email)
                    )
            items:list = [
                ("SKU-1001","USB Cable","Electronics","North Supply",3.50,40,"pcs"),
                ("SKU-1002","Notebook","Office","Metro Goods",1.25,100,"pcs"),
                ("SKU-1003","Hammer","Tools","North Supply",12.00,8,"pcs"),
                ("SKU-1004","Printer Paper","Office","Metro Goods",6.75,3,"ream"),
                ("SKU-1005","Mouse","Electronics","North Supply",9.99,15,"pcs"),
            ]
            for sku,name,category,supplier,price,qty,unit in items:
                cursor.execute("SELECT id FROM categories WHERE name=?",(category,))
                category_id:int = cursor.fetchone()[0]
                cursor.execute("SELECT id FROM suppliers WHERE name=?",(supplier,))
                supplier_id:int = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO products(sku,name,category_id,supplier_id,price,quantity,unit) VALUES(?,?,?,?,?,?,?)",
                    (sku,name,category_id,supplier_id,price,qty,unit)
                )
                cursor.execute(
                    "INSERT INTO stock_logs(product_id,change_qty,action,note) VALUES(?,?,?,?)",
                    (cursor.lastrowid,qty,"IN","Initial stock")
                )
        # (-----------------) end
        conn.commit()
    except Exception as e:
        if conn is not None:
            conn.rollback()
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
