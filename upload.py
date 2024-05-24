import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO

# Function to authenticate and create a Google Drive service
def create_drive_service(credentials_file):
    with open(credentials_file) as f:
        credentials = json.load(f)
    credentials_obj = service_account.Credentials.from_service_account_info(credentials, scopes=['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=credentials_obj)
    return service

# Function to download a file from Google Drive
def download_from_drive(file_name, folder_id, credentials_file):
    service = create_drive_service(credentials_file)
    results = service.files().list(q=f"name='{file_name}' and '{folder_id}' in parents", fields="files(id)").execute()
    files = results.get('files', [])
    if not files:
        return None
    else:
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        with open(file_name, 'wb') as f:
            f.write(fh.read())
        return os.path.abspath(file_name)

def upload_to_drive(file_path, folder_id, credentials_file):
    service = create_drive_service(credentials_file)
    
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='text/xml')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def search_xspf_files(folder_id, credentials_file):
    service = create_drive_service(credentials_file)
    
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='text/xml' and name contains '.xspf'",
        fields="files(name)").execute()
    
    xspf_files = [file['name'] for file in results.get('files', [])]
    return xspf_files

def search_files(folder_id, query, credentials_file):
    drive_service = create_drive_service(credentials_file)
    results = []
    page_token = None

    while True:
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and name contains '{query}' and trashed=false",
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=page_token
        ).execute()

        for file in response.get('files', []):
            results.append({
                'id': file.get('id'),
                'name': file.get('name')
            })

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return results