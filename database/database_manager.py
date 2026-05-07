# En database_manager.py
import sqlite3
import os

class DatabaseManager:
    
    def __init__(self, db_path="datos/Hydracalc.db"):
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
    def get_liquids(self):
        self.cursor.execute("SELECT name, temperature_c, density_kg_m3,viscosity_cp FROM liquidos")
        return self.cursor.fetchall()

    def get_distinct_materiales(self):
        self.cursor.execute("SELECT DISTINCT material, schedule FROM pipes_mm")
        return self.cursor.fetchall()

    def get_schedules_by_material(self, material):
        query = "SELECT DISTINCT schedule FROM pipes_mm WHERE material = ?"
        self.cursor.execute(query, (material,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_diameters(self, material, schedule):
        self.cursor.execute("SELECT nominal_mm FROM pipes_mm WHERE material=? AND schedule=?", (material, schedule))
        return self.cursor.fetchall()
