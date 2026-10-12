import gc
import time

try:
    import requests as _rq
except ImportError:
    import urequests as _rq

import wifi   # le module cree precedemment (SSID / mot de passe)

# ---- a renseigner -----------------------------------------------------
CLE_PRIM = "eWNCHsjSkI37iwRlN50lF8U4bO0FVUrm"
ARRET = "STIF::StopPoint:Q:423950"     # ton MonitoringRef, deux-points final inclus
LIGNE = None        # ex. "C01043" pour ne garder que la 43, ou None pour tout
NB_MAX = 4          # nombre de passages a afficher
# -----------------------------------------------------------------------

URL = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring?MonitoringRef="


def _secondes(iso):
    """'2026-10-04T16:19:00Z' -> secondes depuis l'epoque de la carte."""
    try:
        an = int(iso[0:4]); mo = int(iso[5:7]); jo = int(iso[8:10])
        he = int(iso[11:13]); mi = int(iso[14:16]); se = int(iso[17:19])
        return time.mktime((an, mo, jo, he, mi, se, 0, 0))
    except (ValueError, IndexError, TypeError):
        return None


def recuperer():
    """Retourne une liste de tuples (minutes, ligne, destination).

    Le delai est calcule par rapport a l'horodatage de la reponse,
    pas a l'horloge locale : la carte n'a pas d'horloge fiable.
    """
    if not wifi.ensure():
        raise OSError("wifi indisponible")

    gc.collect()
    r = _rq.get(URL + ARRET, headers={"apikey": CLE_PRIM})
    if r.status_code != 200:
        code = r.status_code
        r.close()
        raise OSError("HTTP %d" % code)

    try:
        d = r.json()
    finally:
        r.close()
        gc.collect()

    sd = d["Siri"]["ServiceDelivery"]
    maintenant = _secondes(sd.get("ResponseTimestamp", ""))
    visites = sd["StopMonitoringDelivery"][0].get("MonitoredStopVisit", [])

    passages = []
    for v in visites:
        j = v["MonitoredVehicleJourney"]
        ligne = j.get("LineRef", {}).get("value", "")

        if LIGNE and LIGNE not in ligne:
            continue

        noms = j.get("DestinationName") or []
        dest = noms[0].get("value", "?") if noms else "?"

        appel = j.get("MonitoredCall") or {}
        brut = (appel.get("ExpectedDepartureTime")
                or appel.get("ExpectedArrivalTime")
                or appel.get("AimedDepartureTime")
                or appel.get("AimedArrivalTime"))
        t = _secondes(brut)
        if t is None or maintenant is None:
            continue

        mins = (t - maintenant) // 60
        if mins < 0:          # bus deja parti, encore present dans la reponse
            continue
        passages.append((mins, ligne, dest))

    del d, sd, visites
    gc.collect()

    passages.sort(key=lambda p: p[0])
    return passages[:NB_MAX]


def afficher():
    try:
        passages = recuperer()
    except Exception as e:
        print("Erreur:", e)
        return

    if not passages:
        print("Aucun passage annonce.")
        return

    print("-" * 40)
    for mins, ligne, dest in passages:
        libelle = "a quai" if mins == 0 else "%d min" % mins
        print("%8s   %-28s" % (libelle, dest[:28]))
    print("-" * 40)
    print("RAM libre:", gc.mem_free(), "octets")


def boucle(periode=60):
    """Rafraichit en continu. Ctrl+C pour arreter."""
    while True:
        afficher()
        time.sleep(periode)
