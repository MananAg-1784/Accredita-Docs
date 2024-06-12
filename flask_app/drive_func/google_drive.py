from google.auth.transport.requests import Request  # sending request
from google.oauth2.credentials import Credentials   # authentication
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.http import MediaIoBaseDownload

from json import loads
import io
import concurrent.futures
from flask_app.database import connection

from flask_app.other_func.global_variables import users, drive_permissions
from flask_app.other_func.update_data import update_file_data, add_upload_activity

def get_creds(user_id):
    try:
        data = connection.execute_query(f'select token from user where user_id = "{user_id}"  ')

        creds = loads(data[0][0])
        creds = Credentials.from_authorized_user_info(creds)

        # credentials are their but expired
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                connection.execute_query(f" update user set token = '{creds.to_json()}' where user_id = '{user_id}' ")
                print("Credentials refreshed ...\n", creds)
        return creds
    except Exception as e:
        print(f"Error getting_creds: {e}")
        return None


# Creating service and validation
def Create_Service(user_id):
    
    if users[user_id].service:
        print("Service present returning...")
        service = users[user_id].service
        if service != None:
            users[user_id].service = None
            return service

    creds = get_creds(user_id)
    try:
        # creating the connection with the access token
        service_build = build('drive', 'v3', credentials=creds)
        print("New service created = ",service_build)
        return service_build

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_folders(service, **kwargs):
    # 1. Search all the folders in the drive
    # 2. Search for specific folder name in the drive
    # 3. Search for folders both 1 & 2 in specific parent
    query = "mimeType = 'application/vnd.google-apps.folder' "
    if not kwargs.get('all_drive', None):
        query = query + "and sharedWithMe "
    else:
        query = query + "and 'root' in parents "
    if kwargs.get('parent_id'):
        query = query + f"and parents = '{kwargs['parent_id']}' "
    if kwargs.get('name'):
        query = query + f"and name = '{kwargs['name']}' "
    print(query)
    page_token = None
    folders = []
    try:
        while True:

            response = service.files().list(
                q = query,
                spaces = 'drive',
                fields = "nextPageToken, files(id,name)",
                pageToken = page_token
            ).execute()

            folders.extend(response.get('files',[]))
            if page_token is not None:
                page_token = response.get('nextPageToken', None)    
            else:
                break 
        
        # list of dict [{id:'' , name: ''}, ....]
        return folders

    except Exception as e:
        print("Exception in finding folders :",e)
        return None


def get_files( parent_id, service, **kwargs):
    files = []
    page_token = None
    query = f"parents = '{parent_id}' and trashed = false"
    if kwargs.get('exclude_mimeType'):
        query = query + f"and mimeType != '{kwargs.get('exclude_mimeType')}'"
    elif kwargs.get('mimeType'):
        query = query + f"and mimeType = '{kwargs.get('mimeType')}' "
    if kwargs.get('name'):
        query = query + f"and name = '{kwargs['name']}' "
    try:
        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files( id, name, createdTime, mimeType, webViewLink, size, iconLink, owners(emailAddress) )''',
                pageToken=page_token).execute()
            
            files.extend(response.get('files',[]))      

            # page token ==> if nex page present or not i.e. the listing is incomplete if pafe_token != NONE
            page_token = response.get('nextPageToken', None)    
            if page_token is None:
                break 
    except Exception as e:
        print("Exception in finding files of folder:",e)
        return None

    return files


def upload_files(folder_ids, file_name, type_, file_url, service):
    print("Recieved Upload Request...")
    print("Folder : ",folder_ids)
    print("File name : ", file_name)

    # reading the file_data
    file_content = None
    file_id = None
    response = []
    with open(file_url, 'rb') as f:
        print("Reading contents of the file..")
        file_content = io.BytesIO(f.read())
    print("Contents read...", type(file_content))

    for parent_id in folder_ids:
        try:
            data = upload_file_in_drive(file_name, parent_id, file_content, type_, service)
            if data:
                response.append(data)
        except Exception as e:
            print("Exception cannot upload file in folder : ", repr(e))
    return response


def upload_file_in_drive(file_name, parent_id, file_content, type_, service):
    try:
        file_metadata = {
            'name' : file_name,
            'parents' : [parent_id]
        }
        # Create a MediaIoBaseUpload object
        media = MediaIoBaseUpload(file_content, mimetype=type_, resumable=True)
        file_content = None
        # Upload the file to Google Drive
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, createdTime, mimeType, webViewLink, size, iconLink, owners(emailAddress)'
        ).execute()

        print('Files are uploaded...',uploaded_file )
        folder_id = connection.execute_query(f'select folder_id from folder where drive_id = "{parent_id}" ')[0][0]
    except Exception as e:
        print("Exception while uploading file in", parent_id, ' ',e )
        return None

    try:
        # adding file data to the database
        update_file_data(uploaded_file, folder_id, newEntry = True)
        add_upload_activity(folder_id, uploaded_file['id'],action = 'create', type_ = {'upload':1}, time = uploaded_file.get('createdTime'))
        return (parent_id, uploaded_file.get('id'))
    except Exception as e:
        print("Exception while updating data for the file:",e )
        return  (parent_id, None)


def list_permissions(drive_id, user_id, service = None):
    try:
        if not service:
            service = Create_Service(user_id)

        response =  service.permissions().list(
            fileId=drive_id,
            fields='permissions(id,role,emailAddress)'
        ).execute()

        perm_ = response.get('permissions', [])
        return perm_

    except Exception as e:
        print("Error fetching permissions....",e )
        return None

# user_details -> email privilage dept_id prev_priv
def change_permissions(user_id,user_details, service = None, folders = None):
    if not service:
        service = Create_Service(user_id)
    role = 'denied'
    if user_details["privilage"] != 'denied':
        role = drive_permissions.get(user_details["privilage"],'denied')

    print("role for email : ", user_details["email"], " ", role)

    if not folders:
        folders = connection.execute_query(f'select drive_id from folder where dept_id = {user_details["dept_id"]}')
        folders = [x[0] for x in folders]
    if folders:
        for id_ in folders:
            permissions = list_permissions(id_, user_id, service)
            print(permissions)
            flag = 0
            for perm in permissions:
                user_email = perm['emailAddress']
                permission_id = perm['id']
                user_role = perm['role']

                if user_email == user_details["email"]:
                    #does not changes access for owner
                    if user_role == "owner":
                        break

                    flag = 1
                    print("Email has some access")
                    if user_role == role:
                        print(f"{user_email} has same role : {user_role}" )

                    elif role == 'denied':
                        print("Deleteing access for the user")
                        try:
                            del_prem = service.permissions().delete(
                                fileId = id_,
                                permissionId = permission_id,
                            ).execute()
                        except Exception as e:
                            print(e)
                            return "Cannot remove access for the user"
                    
                    else:
                        print("Changing permission for the email : ", user_details['email'])
                        try:
                            changed_perm = service.permissions().update(
                                fileId=id_,
                                permissionId = permission_id,
                                body = {'role':role},
                                fields = "id,role"
                            ).execute()
                            if changed_perm['role'] != role:
                                raise Exception("Cannot change priv")
                        except Exception as e:
                            print(e)
                            return "cannot change permission for the user"
                    
                    break
                   
            if flag == 0:
                print("Email not present in folder ....")
                if role != "denied":
                    print("Granting new acces to the user")
                    try:
                        created_prem = service.permissions().create(
                            fileId = id_,
                            body= {
                                "emailAddress": user_details["email"],
                                "type": "user",
                                "role" : role
                            } ,
                            fields = "id,role"
                        ).execute()
                        print(created_prem)
                        if created_prem['role'] != role:
                            raise Exception(1)
                    except Exception as e:
                        print(e)
                        return "Cannot grant permission to user"
                else:
                    print("Access already denied")
    else:
        pass
    return None

