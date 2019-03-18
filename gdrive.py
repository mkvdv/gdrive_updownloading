from __future__ import print_function

import os.path
import pickle
from typing import List

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# If modifying these scopes, delete the file token.pickle. for reinitialization
SCOPES = ['https://www.googleapis.com/auth/drive']

"""
You can login, but they change button's and field's id 
https://gist.github.com/ikegami-yukino/51b247080976cb41fe93
so using selenium here looks creepy solution look s
"""


## Some Exceptions^

class FolderNotFound(Exception):
    pass


class FileNotFound(Exception):
    pass


class WrongGDriveFileNameFormat(Exception):
    pass


class GDriveUtils:
    @staticmethod
    def get_credentials(relogin=False):
        creds = None
        # The file token.pickle stores the user's access and refresh tokens,
        # and is created automatically when the authorization flow completes
        # for the first time.
        if not relogin and os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # use server strategy for getting credentials
                # it will open user's browser for logging in and accepting
                # agreement
                creds = flow.run_local_server(port=8000)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        return creds

    # both
    @staticmethod
    def gdrive_fname_and_folders(full_file_name: str) -> (str, List[str]):
        if full_file_name[0] != '/':
            msg = "Path '{}' does not begin with GDrive root marker /" \
                .format(full_file_name)
            raise WrongGDriveFileNameFormat(msg)

        splitted = full_file_name.split('/')
        folders = splitted[1:-1]
        if len(folders) == 1 and folders[0] is '':
            folders = []
        name = splitted[-1]
        return name, folders

    # both
    @staticmethod
    def find_folder(drive_service, folder_name: str, parent_id: str) -> str:
        if parent_id is None:
            parent_id = 'root'
        query = "name='{0}' and '{1}' in parents " \
                "and mimeType = 'application/vnd.google-apps.folder'" \
            .format(folder_name, parent_id)

        response = drive_service.files().list(q=query, spaces='drive',
                                              fields='files(id)').execute()

        files = response.get('files', [])
        if len(files) < 1:
            raise FolderNotFound("Folder {0} not found".format(folder_name))
        return files[0].get('id')


class Uploader:
    # upload
    @staticmethod
    def create_folder(drive_service, folder_name: str, parent: str) -> \
            str:
        if parent is None:  # todo check if we need to mark it as root
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
        else:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent]
            }
        file = drive_service.files().create(body=file_metadata,
                                            fields='id').execute()
        return file.get('id')

    # upload
    @staticmethod
    def get_last_parent(drive_service, folders: List[str]) -> str:
        last_existed_parent_id = None
        parent_id = None

        for folder in folders:
            try:
                parent_id = GDriveUtils.find_folder(drive_service, folder,
                                                    parent_id)
            except FolderNotFound:
                parent_id = Uploader.create_folder(drive_service, folder,
                                                   last_existed_parent_id)
                # print("Created {}".format(folder))

            last_existed_parent_id = parent_id

        return parent_id

    @staticmethod
    def upload_file(drive_service, src_file: str, dst_file):
        dst_base_name, dst_folders = GDriveUtils.gdrive_fname_and_folders(
            dst_file)
        parent_id = None
        if len(dst_folders) > 0:
            parent_id = Uploader.get_last_parent(drive_service, dst_folders)

        file_metadata = {'name': dst_base_name}
        if parent_id is not None:
            file_metadata['parents'] = [parent_id]

        media = MediaFileUpload('{}'.format(src_file),
                                mimetype='/',
                                resumable=True)
        file = drive_service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        return file.get('id')


class Downloader:
    @staticmethod
    def download_file(drive_service, file_id: str, file_name: str):
        '''

        :param service: Drive v3 service
        :param file_id: id of file inside google drive
        :return: id of file; if not found - throw exception
        '''
        request = drive_service.files().get_media(fileId=file_id)

        dirs, _ = os.path.split(file_name)
        if dirs:
            os.makedirs(dirs, exist_ok=True)

        with open(file_name, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download {}%%.".format(int(status.progress() * 100)))

    # down
    @staticmethod
    def find_file(drive_service, filename: str) -> str:
        '''

        :param service: Drive v3 service
        :param filename: full name of file with prefix and extension
        :return: id of file; if not found - throw FileNotFound exception
        '''
        name, folders = GDriveUtils.gdrive_fname_and_folders(filename)

        founded_folder_id = None
        for folder in folders:
            founded_folder_id = GDriveUtils.find_folder(drive_service, folder,
                                                        founded_folder_id)
            if founded_folder_id is None:
                raise FolderNotFound("Folder {0} not found".format(folder))
            # print("folder {} : {}".format(folder, founded_folder_id))

        parent = founded_folder_id if founded_folder_id is not None else 'root'
        query = "name='{0}' and '{1}' in parents".format(name, parent)
        response = drive_service.files().list(q=query, spaces='drive',
                                              fields='files(id, name, parents)').execute()

        files = response.get('files', [])
        if len(files) < 1:
            raise FileNotFound("File {0} not found".format(filename))
        return files[0].get('id')


##############################################################################
# Interface, these functions are exported to other modules.
##############################################################################

def upload(src_file, dst_file):
    creds = GDriveUtils.get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    file_id = Uploader.upload_file(drive_service, src_file, dst_file)
    print('Uploaded file\'s ID: {}'.format(file_id))


def download(src_file, dst_file):
    creds = GDriveUtils.get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)

    file_id = Downloader.find_file(drive_service, src_file)
    Downloader.download_file(drive_service, file_id, dst_file)
    print("Downloaded file {}!".format(dst_file))
