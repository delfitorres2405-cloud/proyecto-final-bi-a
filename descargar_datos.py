"""
descargar_datos.py
Descarga los archivos .parquet de la carpeta de Google Drive a /data.

Dos formas de usarlo:
  1) Desde la terminal:      python descargar_datos.py
  2) Desde la app (datos.py): se llama sola si falta data/ o con el botón "Actualizar datos".

Requiere credentials.json en esta carpeta (se genera en Google Cloud Console).
La primera vez abre el navegador para autorizar y guarda token.json.
"""
from io import BytesIO
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
ID_CARPETA_DRIVE = "16rbOUqr9AKnALto9Z2ILZK4y6yXeUqoX"

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
DATA_DIR = BASE_DIR / "data"


def _autenticar():
    # Los imports de Google van acá adentro: si los parquet ya están descargados,
    # la app funciona aunque estas librerías no estén instaladas.
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def descargar_parquets():
    """Baja todos los .parquet de la carpeta de Drive a data/. Devuelve los nombres descargados."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    service = build("drive", "v3", credentials=_autenticar())

    respuesta = service.files().list(
        q=f"'{ID_CARPETA_DRIVE}' in parents and trashed=false",
        fields="files(id, name)",
        pageSize=100,
    ).execute()
    archivos = [a for a in respuesta.get("files", []) if a["name"].endswith(".parquet")]

    descargados = []
    for archivo in archivos:
        pedido = service.files().get_media(fileId=archivo["id"])
        buffer = BytesIO()
        descarga = MediaIoBaseDownload(buffer, pedido)
        terminado = False
        while not terminado:
            _, terminado = descarga.next_chunk()
        (DATA_DIR / archivo["name"]).write_bytes(buffer.getvalue())
        descargados.append(archivo["name"])
        print(f"Descargado: {archivo['name']}")

    return descargados


if __name__ == "__main__":
    nombres = descargar_parquets()
    print(f"Listo. {len(nombres)} archivos en {DATA_DIR}")
