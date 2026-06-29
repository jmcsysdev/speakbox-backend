import sqlite3
 
db = sqlite3.connect("speakbox.db")
 
# Tabla de usuarios
db.execute("""CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  nombre TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  fecha_registro TEXT
)""")
 
# Tabla de sesiones — ahora con user_id para saber de quién es cada sesión
db.execute("""CREATE TABLE IF NOT EXISTS sesiones (
  fecha TEXT,
  device_id TEXT,
  transcripcion TEXT,
  respuesta_ia TEXT,
  duracion_seg INTEGER,
  bateria_pct REAL,
  lux REAL,
  user_id INTEGER
)""")
 
db.commit()
db.close()
print("BD lista con tabla de usuarios")
 