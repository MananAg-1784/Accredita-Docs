
from google_auth_oauthlib.flow import Flow
from json import loads
from flask_app.database import connection
from datetime import datetime
import pytz

class OAuthVariable():
    scopes=  [
        'openid', 
        'https://www.googleapis.com/auth/userinfo.email', 
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/drive', 
        "https://www.googleapis.com/auth/drive.activity.readonly",
        ]
    domain = connection.execute_query('select domain from setup')[0][0]
    redirect = connection.execute_query('select auth_redirect from setup')[0][0]
    client_config = loads(connection.credentials())
    print(client_config["web"]["redirect_uris"])
    activity_check = {}
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=scopes,
        redirect_uri= redirect
    )

class User:
    def __init__(self, id, privilage = None, dept = None, logged_in = False):
        self.id = id
        self.service = None
        self.logged_in = logged_in
        self.privilage = privilage
        self.dept = dept
        self.sid = None
        self.uploading_files = []

    def login_user(self):
        self.logged_in = True

    def logout_user(self):
        self.logged_in = False

class FileData:
    def __init__(self, sid, total_size, name):
        self.sid = sid
        self.file_data = b''    # None as soon as data is read
        self.total_size = total_size
        self.name = name
        self.read_size = 0
        self.Lock = True
        self.acc = None
        self.fields = None

class FileDataDetails:
    def __init__(self, sid, **kwargs):
        self.sid = sid
        self.uploadingLock = 0
        self.itemNo = kwargs.get('itemNo')
        self.categories = kwargs.get('categories')
        self.folders = kwargs.get('folders')
        self.name = kwargs.get('name')
        self.size = kwargs.get('size')
        self.mimeType = kwargs.get('mimeType')
        self.segment = kwargs.get('segment')
        self.extraSegment = {}

class Insights:
    def __init__(self):
        # {file_id : category}
        self.new_category = []
        # {file_id : reason}
        self.wrong_file_format = []
        self.ignored_files = []

        self.error = set()
        # file_id : file_data
        self.file_data = {}
        # category_name : file count
        self.missing_category = {}

    def remove_duplicate(self):
        self.error = list(self.error)

        _ = self.new_category
        # remove duplicate data for new category
        for x in _:
            count = 0
            for j in _:
                if j == x:
                    count +=1
                    if count > 1:
                        self.new_category.remove(j)
        
        _ = self.wrong_file_format
        for x in _:
            count = 0
            for j in _:
                if j['id'] == x['id']:
                    count +=1
                    if count > 1:
                        self.wrong_file_format.remove(j)

        _ = self.ignored_files
        for x in _:
            count = 0
            for j in _:
                if j['id'] == x['id']:
                    count +=1
                    if count > 1:
                        self.ignored_files.remove(j)

class check_activities:
    def __init__(self):
        self.folder_id = []

flow = OAuthVariable.flow
# user_id : User()
users = {}

# privilages are their id's
accreditions = [ x[0] for x in connection.execute_query('select accredition from accreditions') ]
priv = {'admin': ['Search', 'Upload', 'Update'], 'viewer' : ['Search'], 'editor' : ['Search', 'Upload']}


# owner -> owner of the file
# reader -> viewer
# writer -> editor
drive_permissions = {'owner':'owner', 'admin':'writer','editor':'writer','viewer':'reader'}

# folder_drive_id : 1/0 
# 1 => changes done in the folder
# 0 => no changes done
# if present in the list --> updating if not present not updating
activity_flag = check_activities()
time_zone = connection.execute_query('select timezone from setup')[0][0]

def date_now(typeStr=False, onlyDate = True):
    intz = pytz.timezone(time_zone)
    format_ = "%Y-%m-%d %H:%M:%S.%f"
    if onlyDate:
        format_ = "%Y-%m-%d"

    nowdt = datetime.now(intz).strftime(format_)
    if typeStr:
        return nowdt

    nowdt = datetime.strptime(nowdt, format_)
    return nowdt
