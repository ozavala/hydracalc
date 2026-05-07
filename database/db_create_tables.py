import sqlite3
import os

class CreateDatabaseTables:
    def __init__(self, db_path="datos/Hydracalc.db"):
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. Tabla de Fluidos (Líquidos)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS liquids (
                name VARCHAR(50),
                formula NVARCHAR(50),
                temperature_c REAL,
                pressure_bar_g INTEGER,
                density_kg_m3 REAL,
                viscosity_cp REAL,
                vapor_pressure_kPa_a REAL,
                state INTEGER
            )
       ''')

        # 2. Tabla de Catálogo de Tuberías (Materiales y Diámetros)
        # Tabla en milímetros
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipes_mm (
                material VARCHAR(50),
                schedule VARCHAR(50),
                nominal_mm NVARCHAR(50),
                nominal_in NVARCHAR(50),
                thickness_mm REAL,
                outiside_diam_mm REAL,
                inside_diam_mm REAL,
                roughness_mm REAL,
                weight_kg_m REAL,
            )
        ''')
        # Tabla en pulgadas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pipes_in (
                material VARCHAR,
                schedule VARCHAR,
                nominal_mm NVARCHAR,
                nominal_in NVARCHAR,
                thickness_in REAL,
                outiside_diam_in REAL,
                inside_diam_in REAL,
                roughness_in REAL,
                weight_lb_ft REAL
            )
        ''')

        # 3. Tabla de Accesorios (Factores K)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accesorios (
                symbol INTEGER, -- iconos de accesorios
                type NVARCHAR(50), -- sb (standard bend)
                nominal_mm NVARCHAR(50),
                nominal_in NVARCHAR(50),
                descripction NVARCHAR(50), -- "standard bend"
                K REAL
            )
        ''')

        
        self.conn.commit()
        print("Base de datos Hydracalc inicializada correctamente.")

    def close(self):
        self.conn.close()
        