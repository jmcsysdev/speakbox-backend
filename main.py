from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import hashlib
 
app = FastAPI(title="SpeakBox TCI Server")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
 
# ── Helpers ──────────────────────────────────────────────────────
def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
 
def get_db():
    db = sqlite3.connect("speakbox.db")
    db.row_factory = sqlite3.Row
    return db
 
# ── Modelos ──────────────────────────────────────────────────────
class RegistroData(BaseModel):
    username: str
    nombre: str
    email: str
    password: str
 
class LoginData(BaseModel):
    email: str
    password: str
 
class SesionFeynman(BaseModel):
    device_id: str
    transcripcion: str
    respuesta_ia: str
    duracion_seg: int
    bateria_pct: float
    lux: float
    user_id: int = 0   # opcional por compatibilidad con el ESP32
 
# ── AUTH ─────────────────────────────────────────────────────────
 
# Registro
@app.post("/api/registro")
async def registro(data: RegistroData):
    db = get_db()
    # Verificar si el email o username ya existen
    existe = db.execute(
        "SELECT id FROM usuarios WHERE email=? OR username=?",
        (data.email, data.username)
    ).fetchone()
    if existe:
        db.close()
        raise HTTPException(status_code=400, detail="El email o nombre de usuario ya está registrado")
    
    db.execute(
        "INSERT INTO usuarios (username, nombre, email, password, fecha_registro) VALUES (?,?,?,?,?)",
        (data.username, data.nombre, data.email, hash_pass(data.password), datetime.now().isoformat())
    )
    db.commit()
    
    # Devolver el usuario recién creado
    usuario = db.execute(
        "SELECT id, username, nombre, email FROM usuarios WHERE email=?",
        (data.email,)
    ).fetchone()
    db.close()
    return {"ok": True, "usuario": dict(usuario)}
 
# Login
@app.post("/api/login")
async def login(data: LoginData):
    db = get_db()
    usuario = db.execute(
        "SELECT id, username, nombre, email FROM usuarios WHERE email=? AND password=?",
        (data.email, hash_pass(data.password))
    ).fetchone()
    db.close()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    
    return {"ok": True, "usuario": dict(usuario)}
 
# ── SESIONES ─────────────────────────────────────────────────────
 
# ESP32 guarda sesión
@app.post("/api/sesion")
async def guardar_sesion(sesion: SesionFeynman):
    db = sqlite3.connect("speakbox.db")
    db.execute("""INSERT INTO sesiones VALUES (?,?,?,?,?,?,?,?)""",
        (datetime.now().isoformat(), sesion.device_id,
         sesion.transcripcion, sesion.respuesta_ia,
         sesion.duracion_seg, sesion.bateria_pct,
         sesion.lux, sesion.user_id))
    db.commit()
    db.close()
    return {"ok": True}
 
# Web lee sesiones — filtra por user_id si se pasa
@app.get("/api/sesiones")
async def listar_sesiones(user_id: int = 0):
    db = get_db()
    if user_id > 0:
        cursor = db.execute(
            "SELECT * FROM sesiones WHERE user_id=? ORDER BY fecha DESC LIMIT 50",
            (user_id,)
        )
    else:
        cursor = db.execute("SELECT * FROM sesiones ORDER BY fecha DESC LIMIT 50")
    rows = cursor.fetchall()
    db.close()
    return {"sesiones": [dict(r) for r in rows]}
 
# ── ESTADO EN VIVO ───────────────────────────────────────────────
estado_actual = {}
 
@app.post("/api/estado")
async def actualizar_estado(data: dict):
    estado_actual.update(data)
    return {"ok": True}
 
@app.get("/api/estado")
async def obtener_estado():
    return estado_actual