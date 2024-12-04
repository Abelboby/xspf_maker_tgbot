import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO

def get_credentials_from_env():
    """
    Extract Google Service Account credentials from environment variables
    """
    try:
        credentials_dict = {
            "type": os.getenv("GOOGLE_CREDENTIALS_TYPE", "service_account"),
            "project_id": os.getenv("GOOGLE_CREDENTIALS_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_CREDENTIALS_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GOOGLE_CREDENTIALS_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("GOOGLE_CREDENTIALS_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_CREDENTIALS_CLIENT_ID"),
            "auth_uri": os.getenv("GOOGLE_CREDENTIALS_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("GOOGLE_CREDENTIALS_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("GOOGLE_CREDENTIALS_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("GOOGLE_CREDENTIALS_CLIENT_CERT_URL")
        }
        
        # Remove None values
        credentials_dict = {k: v for k, v in credentials_dict.items() if v is not None}
        
        return service_account.Credentials.from_service_account_info(
            credentials_dict, 
            scopes=['https://www.googleapis.com/auth/drive']
        )
    except Exception as e:
        raise ValueError(f"Failed to create credentials from environment: {e}")

def create_drive_service():
    """
    Create Google Drive service using environment-based credentials
    """
    try:
        credentials = get_credentials_from_env()
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        raise ValueError(f"Failed to create Drive service: {e}")

def download_from_drive(file_identifier, folder_id, by_id=False):
    service = create_drive_service()
    
    if by_id:
        file_id = file_identifier
        file_metadata = service.files().get(fileId=file_id, fields="id, name, parents").execute()
        file_name_kitti = file_metadata.get('name')
    else:
        results = service.files().list(q=f"name='{file_identifier}' and '{folder_id}' in parents", fields="files(id)").execute()
        files = results.get('files', [])
        if not files:
            return None
        file_id = files[0]['id']

    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    file_name = file_name_kitti if by_id else file_identifier
    with open(file_name, 'wb') as f:
        f.write(fh.read())
    return os.path.abspath(file_name)

def upload_to_drive(file_path, folder_id):
    service = create_drive_service()
    
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='text/xml')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def search_xspf_files(folder_id):
    service = create_drive_service()
    
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='text/xml' and name contains '.xspf'",
        fields="files(name)").execute()
    
    xspf_files = [file['name'] for file in results.get('files', [])]
    xspf_files = sorted(xspf_files)
    return xspf_files

def search_files(folder_id, query):
    drive_service = create_drive_service()
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