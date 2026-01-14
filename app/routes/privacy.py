from fastapi import APIRouter
router = APIRouter()

@router.get("/{event_slug}")
def privacy(event_slug: str):
    # MVP: texto simples; no frontend você pode apontar pra este endpoint
    return {
        "title": f"Política de Privacidade - {event_slug}",
        "consent_required": True,
        "retention_days": 10,
        "contact": "privacidade@seu-dominio.com"
    }
