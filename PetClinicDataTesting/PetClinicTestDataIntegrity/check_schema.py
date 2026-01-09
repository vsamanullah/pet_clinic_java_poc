import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=10.134.77.68,1433;"
    "DATABASE=BookStore-Master;"
    "UID=testuser;"
    "PWD=TestDb@26#!;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

tables = ['Authors', 'Books', 'Genres', 'Customers', 'Rentals', 'Stocks']

for table_name in tables:
    print(f"\n=== {table_name} Table Structure ===")
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
    """)
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]:20} {row[1]:15} NULL={row[2]}")
    else:
        print(f"  Table '{table_name}' not found or has no columns")

conn.close()

