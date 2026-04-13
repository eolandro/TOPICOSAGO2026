import sqlite3
import bcrypt
from config import DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen. Se llama desde main.py."""
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            correo        TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS semillas_2fa (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario      INTEGER NOT NULL,
            semilla_secreta TEXT    NOT NULL,
            activo          BOOLEAN DEFAULT 1,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
        );
    ''')
    conn.commit()
    conn.close()

def _hash_password(password: str) -> str:
    """Hashea con bcrypt (rounds=12, sal automática). Devuelve str para SQLite."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')            # guardar como texto en la BD


def _check_password(password: str, stored: str) -> bool:
    """Verifica la contraseña contra el hash bcrypt almacenado.
       bcrypt.checkpw extrae la sal del propio hash — comparación en tiempo constante."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
    except Exception:
        return False

def crear_usuario(username: str, correo: str, password: str) -> int:
    """Inserta usuario con hash bcrypt (sal automática). Retorna el id asignado.
       Protección contra SQL Injection: usa consulta parametrizada con '?'."""
    password_hash = _hash_password(password)
    conn = get_db()
    try:
        cur = conn.execute(
            'INSERT INTO usuarios (username, correo, password_hash) VALUES (?, ?, ?)',
            [username, correo, password_hash]         
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def buscar_usuario(username: str):
    """Devuelve Row(id, username, correo, password_hash) o None.
       Nota: '?' evita inyección aunque username contenga comillas o SQL."""
    conn = get_db()
    row  = conn.execute(
        'SELECT id, username, correo, password_hash FROM usuarios WHERE username = ?',
        [username]
    ).fetchone()
    conn.close()
    return row


def buscar_usuario_por_id(user_id: int):
    """Devuelve Row(id, username, correo, password_hash) por ID o None."""
    conn = get_db()
    row  = conn.execute(
        'SELECT id, username, correo, password_hash FROM usuarios WHERE id = ?',
        [user_id]
    ).fetchone()
    conn.close()
    return row


def verificar_password(password: str, pw_hash) -> bool:
    """Acepta hash como str o bytes (sqlite3.Row devuelve str)."""
    if isinstance(pw_hash, bytes):
        pw_hash = pw_hash.decode('utf-8')
    return _check_password(password, pw_hash)


def listar_usuarios() -> list:
    conn = get_db()
    rows = conn.execute('''
        SELECT u.id, u.username, u.correo,
               CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END AS has_2fa
        FROM   usuarios u
        LEFT JOIN semillas_2fa s ON s.id_usuario = u.id AND s.activo = 1
        ORDER  BY u.id
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Semillas 2FA ──────────────────────────────────────────────────────────────

def guardar_semilla(id_usuario: int, semilla: str):
    conn = get_db()
    conn.execute(
        'INSERT INTO semillas_2fa (id_usuario, semilla_secreta) VALUES (?, ?)',
        [id_usuario, semilla]
    )
    conn.commit()
    conn.close()


def obtener_semilla_activa(id_usuario: int):
    conn = get_db()
    row  = conn.execute(
        'SELECT semilla_secreta FROM semillas_2fa WHERE id_usuario = ? AND activo = 1',
        [id_usuario]
    ).fetchone()
    conn.close()
    return row['semilla_secreta'] if row else None
