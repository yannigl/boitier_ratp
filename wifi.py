# wifi.py
import network, time

SSID = "Penvern"
PASS = "AvenueSuffren"

_w = network.WLAN(network.STA_IF)

def connect(timeout=20):
    if _w.isconnected():
        return True
    _w.active(True)
    _w.config(reconnects=5)
    _w.connect(SSID, PASS)
    t = time.time()
    while not _w.isconnected():
        if time.time() - t > timeout:
            return False
        time.sleep_ms(300)
    return True

def ensure():
    """A appeler avant chaque requete."""
    if _w.isconnected():
        return True
    _w.disconnect()
    _w.active(False)
    time.sleep(1)
    return connect()

def ip():
    return _w.ifconfig()[0] if _w.isconnected() else None