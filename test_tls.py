import socket, ssl

HOST = "prim.iledefrance-mobilites.fr"

def essai(nom, mini, maxi):
    ctx = ssl.create_default_context()
    ctx.minimum_version = mini
    ctx.maximum_version = maxi
    try:
        with socket.create_connection((HOST, 443), timeout=10) as s:
            with ctx.wrap_socket(s, server_hostname=HOST) as ss:
                print(f"{nom:10} OK   version={ss.version()}  cipher={ss.cipher()[0]}")
    except Exception as e:
        print(f"{nom:10} ECHEC  {type(e).__name__}: {e}")

essai("TLS 1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2)
essai("TLS 1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3)
essai("auto",    ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3)