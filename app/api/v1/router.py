from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit_logs,
    auth,
    ausleihen,
    benutzer,
    bilder,
    export,
    geraete,
    qr_nfc,
    reservierungen,
    standorte,
    statistik,
)

api_router = APIRouter()

api_router.include_router(auth.router,                      prefix="/auth",          tags=["Auth"])
api_router.include_router(geraete.router,                   prefix="/geraete",       tags=["Geräte"])
api_router.include_router(qr_nfc.geraet_router,             prefix="/geraete",       tags=["QR & NFC"])
api_router.include_router(qr_nfc.nfc_router,                prefix="/nfc",           tags=["QR & NFC"])
api_router.include_router(standorte.bildungseinrichtungen_router, prefix="/bildungseinrichtungen", tags=["Standorte"])
api_router.include_router(standorte.standorte_router,           prefix="/standorte",             tags=["Standorte"])
api_router.include_router(standorte.boxen_router,               prefix="/boxen",                 tags=["Standorte"])
api_router.include_router(ausleihen.router,                 prefix="/ausleihen",     tags=["Ausleihen"])
api_router.include_router(reservierungen.router,            prefix="/reservierungen",tags=["Reservierungen"])
api_router.include_router(benutzer.router,                  prefix="/benutzer",      tags=["Benutzer"])
api_router.include_router(audit_logs.router,                prefix="/audit-logs",    tags=["Audit-Logs"])
api_router.include_router(bilder.upload_router,             prefix="/admin/bilder",  tags=["Bilder"])
api_router.include_router(bilder.admin_geraet_bild_router,  prefix="/admin/geraete", tags=["Bilder"])
api_router.include_router(export.router,                    prefix="/export",        tags=["Export"])
api_router.include_router(statistik.router,                 prefix="/statistik",     tags=["Statistik"])
