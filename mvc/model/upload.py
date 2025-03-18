from fastapi import FastAPI, UploadFile, File
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
import io
import os

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_account.json')
PARENT_FOLDER_ID = "1t815zr_mpIlI2MV3UjCPUkcoNCGUxjKz"

def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def upload_photo(file: UploadFile):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file.filename,  # Use the uploaded file's name
        'parents': [PARENT_FOLDER_ID]
    }

    file_stream = io.BytesIO(file.file.read())  # Read the uploaded file as bytes

    media = MediaIoBaseUpload(file_stream, mimetype=file.content_type, resumable=True)

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return {"file_id": uploaded_file.get("id")}
