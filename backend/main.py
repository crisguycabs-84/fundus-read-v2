from fastapi import FastAPI, HTTPException, Response, Cookie
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
import psycopg2

app = FastAPI(title="fundus-read api")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALG = "HS256"
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "15"))

class LoginRequest(BaseModel):
    cc: str
    password: str

def create_access_token(payload: dict) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MIN)
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)

class SubmitDiagnosisRequest(BaseModel):
    lectura_id: str
    diagnostico_clase_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/login")
def login(data: LoginRequest, response: Response):
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, password_hash, is_active, role FROM usuarios WHERE cc = %s",
            (data.cc,)
        )
        row = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    if not row:
        return {"success": False, "message": "Usuario no encontrado"}

    user_id, password_hash, is_active, role = row

    if not is_active:
        return {"success": False, "message": "Usuario inactivo"}

    # (opcional pero recomendable) evita el error de 72 bytes de bcrypt
    if len(data.password.encode("utf-8")) > 72:
        return {"success": False, "message": "Credenciales inválidas"}

    if not pwd_context.verify(data.password, password_hash):
        return {"success": False, "message": "Credenciales inválidas"}

    token = create_access_token({"sub": str(user_id), "cc": data.cc, "role": role})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,      # en Railway vas por https
        samesite="lax",   # mismo site
        max_age=JWT_EXPIRES_MIN * 60,
        path="/",
    )

    return {"success": True}

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"success": True}

@app.get("/auth/me")
def me(access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALG])
        return {
            "user_id": payload.get("sub"),
            "cc": payload.get("cc"),
            "role": payload.get("role"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
        
from fastapi import Query

@app.get("/reading/next")
def reading_next(
    modo_id: int = Query(..., description="0=no asistido, 1=asistido"),
    access_token: str | None = Cookie(default=None),
):
    # 1) validar sesión (cookie con JWT)
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    # 2) SOLO LECTURA: primera lectura pendiente de ese usuario y modo
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            """
            SELECT lectura_id, img_id, posicion
            FROM public.lecturas
            WHERE user_id = %s
              AND modo_id = %s
              AND done IS NULL
            ORDER BY posicion
            LIMIT 1;
            """,
            (user_id, modo_id)
        )
        row = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    if not row:
        return {"found": False, "message": "No hay lecturas pendientes"}

    lectura_id, img_id, posicion = row
    return {
        "found": True,
        "lectura_id": lectura_id,
        "img_id": img_id,
        "posicion": posicion,
        "modo_id": modo_id
    }
    
@app.get("/images/{img_id}")
def get_image_url(img_id: str):
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            """
            SELECT img_id, url, clase_id
            FROM public.imagenes
            WHERE img_id = %s
            """,
            (img_id,)
        )
        row = cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")

    img_id_db, url, clase_id = row
    return {"img_id": img_id_db, "url": url, "clase_id": clase_id}
    
@app.get("/gradcam/{img_id}")
def get_gradcams(img_id: str):
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            """
            SELECT grad_id, modelo_id, clase1_id, clase2_id, url
            FROM public.gradcam
            WHERE img_id = %s
            ORDER BY modelo_id ASC;
            """,
            (img_id,)
        )
        rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    if not rows:
        return {"found": False, "img_id": img_id, "gradcams": []}

    gradcams = []
    for grad_id, modelo_id, clase1_id, clase2_id, url in rows:
        gradcams.append({
            "grad_id": grad_id,
            "modelo_id": modelo_id,
            "clase1_id": clase1_id,
            "clase2_id": clase2_id,
            "url": url
        })

    return {
        "found": True,
        "img_id": img_id,
        "gradcams": gradcams
    }

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def ui_index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/mode")
def ui_mode():
    return FileResponse(STATIC_DIR / "mode.html")

@app.get("/read")
def ui_read():
    return FileResponse(STATIC_DIR / "read.html")

@app.get("/na_read")
def ui_na_read():
    return FileResponse(STATIC_DIR / "na_read.html")


@app.get("/clases")
def get_clases():
    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        cur = conn.cursor()
        cur.execute(
            """
            SELECT clase_id, nombre
            FROM public.clases
            WHERE clase_id <> 'Pendiente'
            ORDER BY nombre ASC;
            """
        )
        rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    clases = [{"clase_id": clase_id, "nombre": nombre} for clase_id, nombre in rows]
    return {"found": True, "clases": clases}

@app.get("/reading/next-na")
def reading_next_na(access_token: str | None = Cookie(default=None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        conn.autocommit = False
        cur = conn.cursor()

        cur.execute(
            """
            SELECT l.lectura_id, l.img_id, l.posicion, i.url
            FROM public.lecturas l
            JOIN public.imagenes i
              ON i.img_id = l.img_id
            WHERE l.user_id = %s
              AND l.modo_id = 0
              AND l.diagnostico_clase_id = 'Pendiente'
            ORDER BY l.posicion
            LIMIT 1
            FOR UPDATE;
            """,
            (user_id,)
        )
        row = cur.fetchone()

        if not row:
            conn.commit()
            return {"found": False, "message": "No hay lecturas pendientes en modo no asistido"}

        lectura_id, img_id, posicion, url = row

        cur.execute(
            """
            UPDATE public.lecturas
            SET start = COALESCE(start, NOW())
            WHERE lectura_id = %s
            """,
            (lectura_id,)
        )

        conn.commit()

    except Exception as e:
        if "conn" in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    return {
        "found": True,
        "lectura_id": lectura_id,
        "img_id": img_id,
        "posicion": posicion,
        "url": url,
        "modo_id": 0
    }

@app.post("/reading/submit-na")
def submit_reading_na(
    data: SubmitDiagnosisRequest,
    access_token: str | None = Cookie(default=None)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALG])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    try:
        conn = psycopg2.connect(os.environ["DATABASE_URL"])
        conn.autocommit = False
        cur = conn.cursor()

        cur.execute(
            """
            SELECT lectura_id
            FROM public.lecturas
            WHERE lectura_id = %s
              AND user_id = %s
              AND modo_id = 0
              AND diagnostico_clase_id = 'Pendiente'
            FOR UPDATE;
            """,
            (data.lectura_id, user_id)
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Lectura no encontrada o ya finalizada")

        cur.execute(
            """
            UPDATE public.lecturas
            SET diagnostico_clase_id = %s,
                done = NOW()
            WHERE lectura_id = %s
            """,
            (data.diagnostico_clase_id, data.lectura_id)
        )

        conn.commit()

    except HTTPException:
        if "conn" in locals():
            conn.rollback()
        raise
    except Exception as e:
        if "conn" in locals():
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cur" in locals(): cur.close()
        if "conn" in locals(): conn.close()

    return {"success": True, "lectura_id": data.lectura_id}