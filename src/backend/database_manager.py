import sqlite3
import logging
from typing import List, Dict, Optional
from models import Component, Supplier

logger = logging.getLogger("agnes.db")

class DatabaseManager:
    def __init__(self, db_path: str = "data/db_new.sqlite"):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_equivalence_class_id(self, name: str) -> Optional[int]:
        """Map a string name like 'Vitamin C' to its DB ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Try exact match first
            cursor.execute('SELECT Id FROM "Equivalence Class" WHERE Name = ?', (name,))
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Try case-insensitive partial match
            cursor.execute('SELECT Id FROM "Equivalence Class" WHERE Name LIKE ?', (f"%{name}%",))
            row = cursor.fetchone()
            if row:
                return row[0]
        return None

    def get_components_by_equivalence_class(self, eq_class_name: str) -> List[Component]:
        """Fetch components from DB for a given category."""
        eq_id = self.get_equivalence_class_id(eq_class_name)
        if not eq_id:
            logger.warning(f"Equivalence class '{eq_class_name}' not found in DB.")
            return []

        query = """
            SELECT 
                sp.ProductId, sp.SupplierId, rm.Name, sp.Price, sp.Quality, 
                sp.Certificates, sp.Allergents, sp.LeadTime, s.Name as SupplierName
            FROM Supplier_Product sp
            JOIN RawMaterial rm ON sp.ProductId = rm.Id
            JOIN Supplier s ON sp.SupplierId = s.Id
            WHERE rm.EquivalenceClassId = ?
        """
        
        components = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (eq_id,))
            for row in cursor.fetchall():
                # Parse certificates and allergens (stored as strings/JSON in DB)
                certs = row[5].split(",") if row[5] else []
                algs = row[6].split(",") if row[6] else []
                
                # Quality in DB is TEXT (reports), but our model expects float. 
                # We'll treat NULL/existing text as None and let the agent enrich it.
                try:
                    quality = float(row[4]) if row[4] and row[4].replace('.', '', 1).isdigit() else None
                except ValueError:
                    quality = None

                comp = Component(
                    id=str(row[0]),
                    supplier_id=str(row[1]),
                    name=row[2],
                    price_per_unit=int(row[3] * 100) if row[3] else None, # Convert to cents
                    quality=quality,
                    certificates=[c.strip() for c in certs],
                    allergens=[a.strip() for a in algs],
                    equivalence_class=eq_class_name,
                    lead_time=int(row[7]) if row[7] else None
                )
                components.append(comp)
        
        return components

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT Id, Name, Ethics, EsgScore FROM Supplier WHERE Id = ?', (supplier_id,))
            row = cursor.fetchone()
            if row:
                return Supplier(
                    id=str(row[0]),
                    name=row[1],
                    ethics=row[2],
                    esg_score=row[3]
                )
        return None

    def add_supplier(self, supplier: Supplier) -> int:
        """Add a new supplier discovered by the agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Supplier (Name) VALUES (?)', (supplier.name,))
            supplier.id = str(cursor.lastrowid)
            return cursor.lastrowid

    def add_component(self, component: Component, eq_class_id: int):
        """Add a new raw material and its supplier link."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Add to RawMaterial
            cursor.execute(
                'INSERT INTO RawMaterial (EquivalenceClassId, Name) VALUES (?, ?)', 
                (eq_class_id, component.name)
            )
            component.id = str(cursor.lastrowid)
            
            # 2. Add to Supplier_Product
            cursor.execute(
                'INSERT INTO Supplier_Product (SupplierId, ProductId) VALUES (?, ?)',
                (component.supplier_id, component.id)
            )
            return cursor.lastrowid

    def update_supplier_enrichment(self, supplier: Supplier):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE Supplier SET Ethics = ?, EsgScore = ? WHERE Id = ?',
                (supplier.ethics, supplier.esg_score, supplier.id)
            )

    def update_product_enrichment(self, component: Component):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Convert lists back to comma-separated strings
            certs = ",".join(component.certificates)
            algs = ",".join(component.allergens)
            price = component.price_per_unit / 100.0 if component.price_per_unit else None
            
            cursor.execute(
                '''UPDATE Supplier_Product 
                   SET Price = ?, Quality = ?, Allergents = ?, LeadTime = ?, Certificates = ? 
                   WHERE SupplierId = ? AND ProductId = ?''',
                (price, component.quality, algs, component.lead_time, certs, 
                 component.supplier_id, component.id)
            )
