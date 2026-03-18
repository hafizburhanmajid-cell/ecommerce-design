import pymysql

print(" Testing MySQL connection...")

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='Emaan123',
        database='ecommerce_db',
        port=3306
    )
    print(" SUCCESS! Database connected!")
    conn.close()
except pymysql.err.OperationalError as e:
    print(f" MySQL Error: {e}")