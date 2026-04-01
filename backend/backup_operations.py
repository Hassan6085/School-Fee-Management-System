import os
import tempfile
import shutil
import json
import datetime
from db import DB_FILE

# Optional imports for Google Drive integration
try:
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive
except ImportError:
    GoogleAuth = None
    GoogleDrive = None

# Global vars
gauth = None
drive = None


def authenticate_drive():
    """
    Authenticate with Google Drive using OAuth2.
    Uses client_secrets.json (Google API credentials).
    """
    global gauth, drive
    if GoogleAuth is None or GoogleDrive is None:
        raise RuntimeError("PyDrive not installed. Install with: pip install pydrive")

    client_secrets_path = os.path.join(os.path.dirname(__file__), '..', 'client_secrets.json')
    if not os.path.exists(client_secrets_path):
        raise RuntimeError(f"client_secrets.json not found at {client_secrets_path}")

    with open(client_secrets_path, 'r') as f:
        json.load(f)

    gauth = GoogleAuth()
    gauth.LoadClientConfigFile(client_secrets_path)
    gauth.LocalWebserverAuth()   # Opens browser for OAuth2
    drive = GoogleDrive(gauth)
    return True


def upload_backup_to_gdrive(file_path, filename):
    """
    Upload or replace a file on Google Drive.
    If filename already exists -> replace it, else create new.
    """
    global drive
    if drive is None:
        raise RuntimeError("Not connected to Google Drive. Run authenticate_drive() first.")

    try:
        # Search file by title
        file_list = drive.ListFile({'q': f"title='{filename}' and trashed=false"}).GetList()
        if file_list:
            # Replace old file
            f = file_list[0]
            f.SetContentFile(file_path)
            f.Upload()
        else:
            # Create new file
            f = drive.CreateFile({'title': filename})
            f.SetContentFile(file_path)
            f.Upload()

        return f['id']
    except Exception as e:
        raise RuntimeError(f"Upload failed: {str(e)}")


def backup_database(current_user=None):
    """
    Make a DB backup.
    1. Replace single latest backup file (school_fee_backup.db)
    2. Also create a timestamped backup for history
    """
    if not current_user:
        raise RuntimeError("User not logged in")

    try:
        # === Create temp copy of DB ===
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tmp.close()
        shutil.copy(DB_FILE, tmp.name)

        # === 1. Replace latest backup ===
        latest_id = upload_backup_to_gdrive(tmp.name, "school_fee_backup.db")

        # === 2. Create timestamped backup ===
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        history_filename = f"backup_{timestamp}.db"
        history_id = upload_backup_to_gdrive(tmp.name, history_filename)

        # Clean up
        os.unlink(tmp.name)

        return {"latest": latest_id, "history": history_id}

    except Exception as e:
        raise RuntimeError(f"Backup failed: {str(e)}")


def restore_database():
    """
    Restore DB from the latest backup file (school_fee_backup.db).
    """
    global drive
    if drive is None:
        raise RuntimeError("Not connected to Google Drive. Run authenticate_drive() first.")

    try:
        file_list = drive.ListFile({'q': "title='school_fee_backup.db' and trashed=false"}).GetList()
        if not file_list:
            raise RuntimeError("No latest backup file found on Google Drive.")

        f = file_list[0]

        # Download temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tmp.close()
        f.GetContentFile(tmp.name)

        # Replace local DB
        shutil.copy(tmp.name, DB_FILE)
        os.unlink(tmp.name)
        return True
    except Exception as e:
        raise RuntimeError(f"Restore failed: {str(e)}")
