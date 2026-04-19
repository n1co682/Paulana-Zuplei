import sqlite3
conn = sqlite3.connect("data/db_new.sqlite")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Supplier)")
print("Supplier table info:")
for row in cursor.fetchall():
    print(row)
cursor.execute("PRAGMA table_info(Supplier_Product)")
print("\nSupplier_Product table info:")
for row in cursor.fetchall():
    print(row)
conn.close()
