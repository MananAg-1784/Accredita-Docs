
from flask_app.database import connection
from datetime import datetime, timedelta
from flask_app.other_func.global_variables import date_now
import pytz

def getOneOf_(obj):
  for key in obj:
    return key
  return None

def getCreationDate(fileDate, createdTime=None):
    # checking for the data of creation time
    flag = 1
    print("Date : ", fileDate)
    try:
        if fileDate and len(fileDate) == 8 and fileDate.isdigit():
            print("The file has a valid inbulilt date")
            try:
                date_object = datetime(int(fileDate[:4]), int(fileDate[4:6]), int(fileDate[6:8]))
                flag = 0
                if date_object > date_now():
                    flag =1
                else:
                    #print("File date in file_name")
                    print("Date object : ", date_object)
                    return date_object.strftime("%Y-%m-%d")
            except ValueError as e:
                print("Value error: ",e)
                flag = 1
        
        if flag == 1 and createdTime:
            print("Fields name does not have any date")
            # Given RFC 3339 date-time string
            rfc3339_datetime_str = createdTime
            rfc3339_datetime = datetime.strptime(rfc3339_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            utc_timezone = pytz.utc

            # Convert the UTC time to IST
            ist_timezone = pytz.timezone('Asia/Kolkata')  # Indian Standard Time
            ist_datetime = utc_timezone.localize(rfc3339_datetime).astimezone(ist_timezone)

            standard_datetime_str = ist_datetime.strftime("%Y-%m-%d")

            return standard_datetime_str
            
        return None
    except Exception as e:
        print("getting creation date :", e)
        return None

def get_file_name_data(file_name):
    try:
        file_name = file_name.replace(' ','')
        if file_name.rfind('.') != -1:
            file_name = file_name[ : file_name.rfind('.')  ]
        name_format = file_name.split('_')
        _ = 3 - len(name_format)
        if _ > 0:
            for i in range(0,_):
                name_format.append('')
        return name_format
    except Exception as e:
        return None
           
# add files data into the database
def update_file_data(file_data, folder_id, newEntry = False, action = None):
    print("\n\nFile... ", file_data["name"])

    # Ignores the readme file
    if file_data["name"].lower() == 'readme':
        return  

    # file_id drive_id folder_id file_name creationTime size owner_email mimeType_id driveLink
    file_id = connection.execute_query(f'select file_id from files where drive_id = "{file_data["id"]}" ') 
    
    if file_data.get('size'):
            file_data['size'] = int(file_data.get('size'))
    else:
        file_data['size'] = None
    print(file_data['size'])

    owner_email = file_data.get('owners')
    try:
        if owner_email:
            owner_email = owner_email[0].get('emailAddress')
    except Exception as e:
        owner_email = None
    print(owner_email)

    file_name = file_data['name']
    drive_id = file_data['id']
    
    # check all the data and update if necessary
    if file_id:
        print("File data present")
        newEntry = False
        file_id = file_id[0][0]
        print(file_id)

        data = connection.dict_query(f'select file_name, size, owner_email from files where drive_id = "{drive_id}" ')
        data = data[0]
        print(data)
        if action == 'rename' or data['file_name'] != file_name:
            connection.execute_query(f'update files set file_name = "{file_name}" where drive_id = "{drive_id}" ')
            action = 'rename'
        else:
            print("No renaming..")

        if not data['owner_email'] or (data['owner_email'] != owner_email and owner_email):
            connection.execute_query(f'update files set owner_email = "{owner_email}" where drive_id = "{drive_id}" ')
        else:
            print("Same owner..")

        if file_data['size'] and data['size'] < file_data['size']:
            connection.execute_query(f'update files set size = "{file_data["size"]}" where drive_id = "{drive_id}" ')
        else:
            print("File_size is same...")

    #Entry new record for the file
    else:
        print("Creating new data...")
        newEntry = True
        connection.execute_query(f'''
        insert into 
        files(drive_id, folder_id, file_name, size, owner_email, driveLink) 
        values('{drive_id}',{folder_id},
            '{file_name}','{file_data['size']}',
            '{owner_email}',
            '{file_data['webViewLink']}')
        ''')
    
        file_id = connection.execute_query(f"select file_id from files where drive_id = '{drive_id}' ")[0][0]
        
        # get and update the mimeType_id
        mimeType_id = connection.execute_query(f'select mimeType_id from mimeType where mimeType = "{file_data["mimeType"]}" ')
        if not mimeType_id:
            connection.execute_query(f'insert into mimeType(mimeType, iconLink) values("{file_data["mimeType"]}","{file_data["iconLink"]}")')
            mimeType_id = connection.execute_query(f'select mimeType_id from mimeType where mimeType = "{file_data["mimeType"]}" ')

        connection.execute_query(f'update files set mimeType_id = {mimeType_id[0][0]} where file_id = {file_id}')
    
    # get and update the creationTime
    # get and update the categories related to the folder
    try:
        name_format = get_file_name_data(file_name)
        creationTime = name_format[0]
        creationTime = getCreationDate(creationTime, file_data.get('createdTime'))

        if action == 'rename' or newEntry :
            if creationTime:
                print("Adding Creation Date to the file")
                connection.execute_query(f'update files set creationTime = "{creationTime}" where file_id = {file_id} ')
            else:
                print("Format of the file is wrong..")
        else:
            print("CreationTime present ...")

        connection.execute_query(f'delete from file_category where file_id = {file_id}')
        category = name_format[1]
        # multiple categories...
        if not category:
            print("No category for the file...")
        else:
            category = category.split(',')
            category_id = []
            for cat in category:
                if cat:
                    cat_id = connection.execute_query(f'select category_id from category where category = "{cat}" ')
                    if cat_id:
                        category_id.append(cat_id[0][0])
                    else:
                        print("category not present ...", cat)
            for cat_id in category_id:
                connection.execute_query(f'insert into file_category values({file_id},{cat_id})')

    except Exception as e:
        print("Exception in extraction data from file_name ...", e)
        
# uploaded files-> restored / created in upload_activity
def add_upload_activity(folder_id, file_id, action, type_, time):

    week_ago =  date_now(onlyDate=False) - timedelta(days=7)
    date = week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    time = getCreationDate(None, time)
    creationTime = datetime.strptime(time, '%Y-%m-%d')
    if creationTime > date:
        print("Activity is between the one week time span")
        try:
            # new file added -> created / restored
            file_data = connection.execute_query(f'select file_id from files where drive_id = "{file_id}" and folder_id = {folder_id} ')
            
            if file_data:
                print("file data present ... adding the file to upload")
                file_data = file_data[0]
                type_ = getOneOf_(type_)
                if action == 'create':
                    if type_ == 'copy':
                        type_ = 'copied'
                    elif type_ == 'upload':
                        type_ = 'uploaded'
                    else:
                        type_= 'created'
                elif action == 'restore':
                    # delete the file data from trashed if 
                    print("Restored the file...")
                    print("Removing all the data for the file if available in the trash")
                    connection.execute_query(f'delete from trashed where drive_id = "{file_id}" ')
                    type_ = 'restored'
                print("Adding in upload_activity")
                data = connection.execute_query(f'insert into upload_activity values ({file_data[0]},{folder_id}, "{type_}","{time}") ')
                if data == 'failed':
                    print("Exception while entering data in upload_activity table..")
                    connection.execute_query(f'update upload_activity set action = "{type_}", time = "{time}" where file_id = {file_data[0]} ')
                    print("Updated action type : ", type_)

            else:
                print("File data not present not adding...")
        except Exception as e:
            print(f"Exception while uploading_activity_data : ACTION : {action} : ", e)

# delete data - trash - completly
def delete_file_data(service, action, file_drive_id, time, folder_id, file_data = None):
    action = action['type'].lower()
    file_id = None
    print(action)

    week_ago =  date_now(onlyDate=False) - timedelta(days=7)
    date = week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    time = getCreationDate(None, time)
    creationTime = datetime.strptime(time, '%Y-%m-%d')

    if action == 'trash':
        # remove the data from the files and trash and put it in trash
        if file_drive_id and not file_data:
            file_data = connection.dict_query(f'select * from files where drive_id = "{file_drive_id}" ')
            print(file_data)
            if file_data:
                file_data = file_data[0]
                file_id = file_data['file_id']
                print("File_id is present : ", file_id)
            else:
                file_data = service.files().get(fileId = file_drive_id, fields='id, name, mimeType, webViewLink, owners(emailAddress)').execute()
                if file_data:
                    file_data["file_name"] = file_data["name"]
                    file_data["driveLink"] = file_data["webViewLink"]
                    file_data["owner_email"] = file_data["owners"][0]['emailAddress']
                    mime_id = connection.execute_query(f'select mimeType_id from mimeType where mimeType = "{file_data["mimeType"]}" ')
                    if mime_id:
                        file_data["mimeType_id"] = mime_id[0][0]
                    else:
                        file_data["mimeType_id"] = None

        if (file_id or file_data) and creationTime > date:
            print("Trashed within 7 days from today...")
            data = connection.execute_query(f'insert into trashed(drive_id, folder_id, file_name, mimeType_id, time, owner, link) values("{file_drive_id}",{folder_id},"{file_data["file_name"]}", {file_data["mimeType_id"]} ,"{time}", "{file_data["owner_email"]}", "{file_data["driveLink"]}") ')
            if data == 'failed':
                print("Exception while entring data in trashed...")
                connection.execute_query(f'update trashed set time = "{time}" where drive_id = "{file_drive_id}" ')

    else:
        # remove the file data from the trashed folder
        connection.execute_query(f'delete from trashed where drive_id = "{file_drive_id}" ')
        file_id = connection.execute_query(f'select file_id from files where drive_id = "{file_drive_id}" ')
        if file_id:
            file_id = file_id[0][0]

    if file_id:
        print("removing all the data for the file")
        connection.execute_query(f'delete from files where file_id = {file_id}')
        connection.execute_query(f'delete from upload_activity where file_id = {file_id}')
        connection.execute_query(f'delete from ignored_files where file_id = {file_id}')
        connection.execute_query(f'delete from file_category where file_id = {file_id}')

def update_category_for_file(category_id, category_name):
    print("Checking if some files have the category...")
    print(f"category : {category_name}, ID : {category_id}")
    files = connection.execute_query('select file_id, file_name from files')
    counter = 0
    for file in files:
        try:
            file_format = get_file_name_data(file[1])
            category = file_format[1]
            # multiple categories...
            if category:
                category = category.split(',')
                for cat in category:
                    if cat and cat == category_name:
                        counter +=1
                        print("FIle id : ", file[0])
                        connection.execute_query(f'insert into file_category(file_id, category_id) values({file[0]},{category_id})')
        except:
            print("Exception ...",e)
            pass
    print("Updated for all files...")
    print("Total files category added : ", counter)
    return
