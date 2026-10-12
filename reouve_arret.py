#!/usr/bin/env python3
"""
Trouve le MonitoringRef PRIM d'un arret de bus, et identifie le bon sens
en interrogeant l'API temps reel.

A lancer sur un ordinateur ou un Raspberry Pi (pas sur l'ESP32).

    pip install requests
    python3 trouve_arret.py
"""

import requests
from datetime import datetime, timezone

# ---- a renseigner -----------------------------------------------------
CLE_PRIM = "eWNCHsjSkI37iwRlN50lF8U4bO0FVUrm"
NOM_ARRET = "Hoche"          # fragment du nom, sans accent de preference
LIGNE = "43"                 # numero de ligne tel qu'affiche
DESTINATION_VOULUE = "Bagatelle"   # mot cle du terminus recherche
# -----------------------------------------------------------------------

REFERENTIEL = ("https://data.iledefrance-mobilites.fr/api/explore/v2.1"
               "/catalog/datasets/arrets-lignes/records")
TEMPS_REEL = "https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring"


def cherche_arrets():
    """Interroge le referentiel ouvert (pas de cle necessaire)."""
    params = {
        "where": f'search(stop_name, "{NOM_ARRET}")',
        "limit": 100,
    }
    r = requests.get(REFERENTIEL, params=params, timeout=30)
    r.raise_for_status()
    resultats = r.json().get("results", [])

    # on ne garde que la ligne voulue
    garde = []
    for rec in resultats:
        blob = " ".join(str(v) for v in rec.values())
        if f" {LIGNE} " in f" {blob} " or rec.get("route_long_name") == LIGNE:
            garde.append(rec)
    return garde or resultats


def id_depuis(rec):
    """Extrait le numero d'arret, quel que soit le champ utilise."""
    for champ in ("arrid", "id_arret", "stop_id", "zdaid", "id"):
        v = rec.get(champ)
        if v:
            return str(v).split(":")[-1]
    return None


def prochains_passages(numero):
    ref = f"STIF:StopPoint:Q:{numero}:"
    r = requests.get(TEMPS_REEL,
                     params={"MonitoringRef": ref},
                     headers={"apikey": CLE_PRIM},
                     timeout=30)
    if r.status_code != 200:
        return ref, None, f"HTTP {r.status_code}"
    try:
        d = r.json()
        visites = (d["Siri"]["ServiceDelivery"]
                    ["StopMonitoringDelivery"][0]
                    .get("MonitoredStopVisit", []))
    except (KeyError, IndexError, ValueError) as e:
        return ref, None, f"reponse inattendue ({e})"

    destinations = []
    for v in visites:
        j = v["MonitoredVehicleJourney"]
        noms = j.get("DestinationName") or []
        nom = noms[0].get("value") if noms else "?"
        ligne = j.get("LineRef", {}).get("value", "?")
        destinations.append((ligne, nom, minutes_restantes(j)))
    destinations.sort(key=lambda d: (d[2] is None, d[2]))
    return ref, destinations, None


def minutes_restantes(journey):
    """Delai en minutes avant le passage, ou None si non communique."""
    appel = journey.get("MonitoredCall") or {}
    brut = (appel.get("ExpectedDepartureTime")
            or appel.get("ExpectedArrivalTime")
            or appel.get("AimedDepartureTime")
            or appel.get("AimedArrivalTime"))
    if not brut:
        return None
    try:
        t = datetime.fromisoformat(brut.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    delta = (t - datetime.now(timezone.utc)).total_seconds()
    return int(delta // 60)


def format_delai(m):
    if m is None:
        return "  ?  "
    if m < 0:
        return "parti"
    if m == 0:
        return "a quai"
    return f"{m:2d} min"


def main():
    print(f"Recherche des arrets '{NOM_ARRET}' sur la ligne {LIGNE}...\n")
    arrets = cherche_arrets()
    if not arrets:
        print("Aucun arret trouve. Elargis NOM_ARRET.")
        return

    vus = set()
    for rec in arrets:
        num = id_depuis(rec)
        if not num or num in vus:
            continue
        vus.add(num)
        nom = rec.get("stop_name", "?")
        commune = rec.get("nom_commune") or rec.get("stop_desc") or ""
        print(f"--- {nom}  {commune}   id={num}")

        if CLE_PRIM.startswith("COLLE"):
            print("    (cle PRIM non renseignee, pas de test temps reel)")
            continue

        ref, dests, err = prochains_passages(num)
        if err:
            print(f"    {ref}  ->  {err}")
            continue
        if not dests:
            print(f"    {ref}  ->  aucun passage annonce pour l'instant")
            continue
        print(f"    {ref}")
        for ligne, dest, m in dests[:8]:
            marque = "  <== CELUI-CI" if DESTINATION_VOULUE.lower() in dest.lower() else ""
            print(f"      {format_delai(m):>7}   ligne {ligne}  vers {dest}{marque}")
        print()


if __name__ == "__main__":
    main()
