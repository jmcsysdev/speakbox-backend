from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3, hashlib

app = FastAPI(title="SpeakBox TCI Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

class SesionFeynman(BaseModel):
    device_id: str
    transcripcion: str
    respuesta_ia: str
    duracion_seg: int
    bateria_pct: float
    lux: float
    user_id: int = 0

class RegistroIn(BaseModel):
    nombre: str
    username: str
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

def get_db():
    db = sqlite3.connect("speakbox.db")
    db.row_factory = sqlite3.Row
    return db

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

@app.post("/api/registro")
async def registro(data: RegistroIn):
    db = get_db()
    existe = db.execute(
        "SELECT id FROM usuarios WHERE email=? OR username=?",
        (data.email, data.username)
    ).fetchone()
    if existe:
        db.close()
        raise HTTPException(400, "El email o nombre de usuario ya está en uso.")
    db.execute(
        "INSERT INTO usuarios (nombre, username, email, password) VALUES (?,?,?,?)",
        (data.nombre, data.username, data.email, hash_pw(data.password))
    )
    db.commit()
    user = db.execute("SELECT * FROM usuarios WHERE email=?", (data.email,)).fetchone()
    db.close()
    return {"ok": True, "user_id": user["id"], "username": user["username"], "nombre": user["nombre"]}

@app.post("/api/login")
async def login(data: LoginIn):
    db = get_db()
    user = db.execute(
        "SELECT * FROM usuarios WHERE email=? AND password=?",
        (data.email, hash_pw(data.password))
    ).fetchone()
    db.close()
    if not user:
        raise HTTPException(401, "Email o contraseña incorrectos.")
    return {"ok": True, "user_id": user["id"], "username": user["username"], "nombre": user["nombre"]}

@app.post("/api/sesion")
async def guardar_sesion(sesion: SesionFeynman):
    db = get_db()
    db.execute(
        "INSERT INTO sesiones VALUES (?,?,?,?,?,?,?,?)",
        (datetime.now().isoformat(), sesion.device_id, sesion.transcripcion,
         sesion.respuesta_ia, sesion.duracion_seg, sesion.bateria_pct,
         sesion.lux, sesion.user_id)
    )
    db.commit(); db.close()
    return {"ok": True}

@app.get("/api/sesiones")
async def listar_sesiones(user_id: int = 0):
    db = get_db()
    if user_id:
        rows = db.execute(
            "SELECT * FROM sesiones WHERE user_id=? ORDER BY fecha DESC LIMIT 50",
            (user_id,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM sesiones ORDER BY fecha DESC LIMIT 50"
        ).fetchall()
    db.close()
    return {"sesiones": [dict(r) for r in rows]}

estado_actual = {}

@app.post("/api/estado")
async def actualizar_estado(data: dict):
    estado_actual.update(data)
    return {"ok": True}

@app.get("/api/estado")
async def obtener_estado():
    return estado_actual
