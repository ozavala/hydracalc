import sqlite3

class DatabaseManager:
    def __init__(self, db_path="database/hydracalc.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_fluids(self):
        # Usando la tabla 'liquids' y columnas del PDF
        query = "SELECT rowid, name, temperature_c FROM liquids"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error en base de datos: {e}")
            # Log para depuración: imprime las columnas reales encontradas
            self.cursor.execute("PRAGMA table_info(liquids)")
            cols = [info[1] for info in self.cursor.fetchall()]
            print(f"Columnas detectadas en la tabla 'liquids': {cols}")
            return [] 
    def get_distinct_materials(self):
        # Usando 'pipes_mm' como base por ahora
        query = "SELECT DISTINCT material FROM pipes_mm"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def get_schedules_by_material(self, material):
        query = "SELECT DISTINCT schedule FROM pipes_mm WHERE material = ?"
        self.cursor.execute(query, (material,))
        return [row[0] for row in self.cursor.fetchall()]

    def get_sizes(self, material, schedule):
        # Usando 'nominal_mm' e 'inside_diam_mm' según el PDF
        query = "SELECT rowid, nominal_mm FROM pipes_mm WHERE material = ? AND schedule = ?"
        self.cursor.execute(query, (material, schedule))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
