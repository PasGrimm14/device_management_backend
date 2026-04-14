from fastapi import APIRouter

from app.api.v1.endpoints import audit_logs, auth, ausleihen, benutzer, bilder, geraete, reservierungen

api_router = APIRouter()

api_router.include_router(auth.router,                      prefix="/auth",          tags=["Auth"])
api_router.include_router(geraete.router,                   prefix="/geraete",       tags=["Geräte"])
api_router.include_router(ausleihen.router,                 prefix="/ausleihen",     tags=["Ausleihen"])
api_router.include_router(reservierungen.router,            prefix="/reservierungen",tags=["Reservierungen"])
api_router.include_router(benutzer.router,                  prefix="/benutzer",      tags=["Benutzer"])
api_router.include_router(audit_logs.router,                prefix="/audit-logs",    tags=["Audit-Logs"])
api_router.include_router(bilder.upload_router,             prefix="/admin/bilder",  tags=["Bilder"])
api_router.include_router(bilder.admin_geraet_bild_router,  prefix="/admin/geraete", tags=["Bilder"])
