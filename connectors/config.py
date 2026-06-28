# -*- coding: utf-8 -*-
"""Carrega segredos do cofre canônico (~/.secrets/.env) e a config da entidade.
Nunca imprime valores. Ordem de precedência: variável de ambiente > cofre."""
import os
import sys
from pathlib import Path

# entity.py vive na raiz do repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from entity import ENTITY  # noqa: E402


def _load_cofre() -> dict:
    path = os.environ.get("SECRETS_ENV") or str(Path.home() / ".secrets" / ".env")
    out: dict[str, str] = {}
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


_COFRE = _load_cofre()


def get_secret(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or _COFRE.get(name) or default


GITHUB_TOKEN = get_secret("GITHUB_TOKEN")
HF_TOKEN = get_secret("HF_TOKEN")
GOOGLE_DRIVE_CLIENT_ID = get_secret("GOOGLE_DRIVE_CLIENT_ID")
GOOGLE_DRIVE_CLIENT_SECRET = get_secret("GOOGLE_DRIVE_CLIENT_SECRET")
GOOGLE_DRIVE_REFRESH_TOKEN = get_secret("GOOGLE_DRIVE_REFRESH_TOKEN")
VERCEL_TOKEN = get_secret("VERCEL_TOKEN")


def supabase_creds() -> dict | None:
    """Credenciais Supabase da entidade, se houver prefixo configurado (ex.: DETRAN -> SUPABASE_URL_DETRAN)."""
    prefix = ENTITY.get("supabase_env_prefix")
    if not prefix:
        return None
    url = get_secret(f"SUPABASE_URL_{prefix}")
    key = get_secret(f"SUPABASE_SERVICE_{prefix}") or get_secret(f"SUPABASE_ANON_{prefix}")
    if not url or not key:
        return None
    return {"url": url.rstrip("/"), "key": key}


def secret_status() -> dict:
    """Status mascarado dos segredos (para diagnóstico — nunca expõe valor)."""
    def mask(v):
        if not v:
            return "<ausente>"
        return f"{v[:3]}...{v[-3:]}" if len(v) > 8 else "****"
    sb = supabase_creds()
    return {
        "entity": ENTITY["name"],
        "github_token": mask(GITHUB_TOKEN),
        "hf_token": mask(HF_TOKEN),
        "google_drive": mask(GOOGLE_DRIVE_REFRESH_TOKEN),
        "vercel_token": mask(VERCEL_TOKEN),
        "supabase": "configurado" if sb else "<n/a p/ esta entidade>",
    }
