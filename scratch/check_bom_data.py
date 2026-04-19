import sqlite3
conn = sqlite3.connect("data/db_new.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT * FROM BOM WHERE ProductID = 1")
print("BOM for Product 1:")
for row in cursor.fetchall():
    print(row)
cursor.execute("SELECT * FROM RawMaterial WHERE Id IN (SELECT Materiald FROM BOM WHERE ProductID = 1)")
print("\nRawMaterials in BOM:")
for row in cursor.fetchall():
    print(row)
conn.close()
