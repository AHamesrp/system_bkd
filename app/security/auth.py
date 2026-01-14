# app/security/auth.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets, os

security = HTTPBasic()

def _read_env(k: str, default: str) -> str:
    v = os.getenv(k, default)
    # remove aspas, espaços e quebras acidentais do .env
    if v is None:
        return default
    return v.strip().strip('"').strip("'")

USER = _read_env("BASIC_ADMIN_USER", "admin")
PASS = _read_env("BASIC_ADMIN_PASS", "troque-isto")

def require_basic(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, USER)
    ok_pass = secrets.compare_digest(credentials.password, PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=403, detail="Acesso negado")
    return True
