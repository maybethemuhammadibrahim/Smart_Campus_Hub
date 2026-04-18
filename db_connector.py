import mysql.connector
from mysql.connector import pooling
from config import Config

connection_pool = pooling.MySQLConnectionPool(
    pool_name    = "campus_pool",
    pool_size    = 5,
    host         = Config.DB_HOST,
    port         = Config.DB_PORT,
    user         = Config.DB_USER,
    password     = Config.DB_PASS,
    database     = Config.DB_NAME
)

def get_connection():
    return connection_pool.get_connection()

def execute_query(query, params=None, fetch=True, many=False):
    """
    fetch=True  → returns list of dicts (SELECT)
    fetch=False → executes INSERT/UPDATE/DELETE, returns lastrowid
    many=True   → params is a list of tuples (executemany)
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if many:
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    finally:
        cursor.close()
        conn.close()

def call_procedure(proc_name, args=()):
    """Calls a stored procedure. Returns OUT params as the last item."""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        result_args = cursor.stored_results()
        return list(result_args)
    finally:
        cursor.close()
        conn.close()