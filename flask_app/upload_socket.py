

from flask_socketio import rooms, join_room, leave_room, close_room, emit
from flask import render_template, url_for, request, current_app
from json import dumps
from time import sleep
import os
from datetime import datetime, timedelta
import concurrent.futures
import threading

from flask_app.database import connection
from flask_app.socket_connection import socketio
from flask_app.drive_func.google_drive import Create_Service, upload_files

from flask_app.other_func.update_data import *
from flask_app.other_func.enc_dec import encrypt_fernet, decrypt_fernet
from flask_app.other_func.authentication import validate_user_access
from flask_app.other_func.files import check_actitivty
from flask_app.other_func.global_variables import users, FileDataDetails, date_now


def remove_cache(user):
    print('Removing all file data for the user...')
    for x in user.uploading_files:
        url = create_url(user.id, x.name)
        if not x.uploadingLock:
            remove_upload_file_data(url,user.uploading_files.index(x) ,user.uploading_files)
        else:
            print("File already uploading to google drive...")

def remove_data_activity(folder_id, date):
    data = connection.execute_query(f'select file_id, time from upload_activity where folder_id = {folder_id}')
    for _ in data:
        try:
            time = datetime.strptime(_[1], '%Y-%m-%d')
            if time < date:
                print("Removing", _)
                connection.execute_query(f'delete from upload_activity where file_id = {_[0]}')
        except Exception as e:
            print("Exception while deleting data upload_activity")
    
    data = connection.execute_query(f'select drive_id, time from trashed where folder_id = {folder_id}')
    for _ in data:
        try:
            time = datetime.strptime(_[1], '%Y-%m-%d')
            if time < date:
                print("Removing", _)
                connection.execute_query(f'delete from trashed where drive_id = {_[0]}')
        except Exception as e:
            print("Exception while deleting data upload_activity")
    return 1

def create_url(user_id, file_name):
    # Get the absolute path of the static folder
    current_working_directory = os.getcwd()
    static_folder_path = os.path.join(current_app.root_path, current_app.static_folder)
    # Convert the absolute path to a relative path
    relative_path = os.path.relpath(static_folder_path, current_working_directory)
    return os.path.join(relative_path,'files_uploading',f'{user_id}_{file_name}')

def check_file_data(name,categories):
    file_name = get_file_name_data(name)
    print("File_name : ", file_name)
    file_creation_date = getCreationDate(file_name[0] ,None)
    print("File_date : ", file_creation_date)

    if not file_creation_date:
        return 'File naming Error'

    category = file_name[1]
    print("File Category : ", category)
    # multiple categories...
    if not category:
        print("No category for the file...")
        return 'File naming Error'
    else:
        category = category.split(',')
        category_id = []
        for cat in category:
            if cat:
                cat_id = connection.execute_query(f'select category_id from category where category = "{cat}" ')
                print("Ccategory _id : ", cat_id)
                if cat_id and (cat not in categories):
                    return 'File naming Error'
                elif not cat_id:
                    return 'Category not present'
    return None

def remove_upload_file_data(url, index, files_list):
    print('remove data for the file : ', url)
    if os.path.exists(url):
        try:
            os.remove(url)
        except:
            print(f"The file '{url}' deletion error.")
    try: 
        del files_list[index]
    except: pass

def upload_file_toDrive(file_index, url, user, sid):
    print(user)
    try:
        file_data = user.uploading_files[file_index]
        itemNo = file_data.itemNo
        sleep(1)
        socketio.emit('progress_report', dumps({'progress' : 'upload', 'itemNo' : itemNo}),namespace='/upload', room=sid) 
        sleep(1)
        print("Starting upload... background_task....")

        resp = {'itemNo' : itemNo, 'progress': ''}
        flag = 0
        _ = file_data.folders
        folder_ids = []
        for i in _:
            id_ = connection.execute_query(f'select drive_id from folder where folder_name = "{i}" ')
            if id_:
                folder_ids.append(id_[0][0])
            else:
                resp['error'] = 'Folder not Present' 
                flag = 1
                break
        
        if flag == 0:
            print("Folder_ids", folder_ids)
            if os.path.isfile(url):
                service = Create_Service(user.id)
                file_data.uploadingLock = 1
                print('Uploading file to the folder...')
                
                response = upload_files(folder_ids= folder_ids, file_name = file_data.name,type_= file_data.mimeType,file_url = url,service= service)

                file_data.uploadingLock = 0
                print(response)
                print("............................")
                if response and len(response) < len(folder_ids):
                    print("File Successfully Uploaded....")
                    for x in response:
                        resp['progress'] += file_data.folders[ folder_ids.index(x[0])] + ', '
                elif response and len(response) == len(folder_ids):
                    resp['progress'] = 'uploaded'
                elif not response:
                    print("File cannot be uploaded")
                    resp['error'] = 'Cannot be uploaded'

            else:
                print("File not found....")
                resp['error'] = 'Server Error, Try Again'

    except Exception as e:
        print("Exception ...", e)
        resp['error'] = 'Server Error, Try Again'

    print("............................")
    remove_upload_file_data(url, file_index, user.uploading_files)
    print("Response to emit ...", resp)
    if resp.get('error'):
        resp['progress'] = ''
    socketio.emit('progress_report', 
                   dumps(resp),
                   namespace='/upload', room=sid) 

def activity_forUpload(folders, user, namespace, sid):
    # check activity for folders
    try:
        socketio.emit('activity_updated',dumps({'data':1}),namespace= namespace, room = sid)
        sleep(1)
        folder_data = []
        updated = ''
        for folder in folders:
            folder = folder[1]
            folder_details = connection.execute_query(f'select folder_id, drive_id, lastActivityCheckTime from folder where folder_name = "{folder}" ')
            folder_data.append({
                'folder': folder,
                'folder_id': folder_details[0][0],
                'drive_id': folder_details[0][1],
                'last_check_time': folder_details[0][2]
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(folders)) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(check_actitivty, x['drive_id'], x['folder_id'], x['last_check_time'], user, True): x['folder'] for x in folder_data}

            for future in concurrent.futures.as_completed(future_to_url):
                folder_name = future_to_url[future]
                try:
                    data = future.result()
                    print(data)
                    if data > 1:
                        updated += folder_name + ' '
                except Exception as exc:
                    print("Exception while check_activity call...", exc)
        
        if updated:
            print("Data is updated for folder",updated)
            socketio.emit('activity_updated',
                        dumps({'data':f'Activity Updated for Folder: {updated}'}), 
                        namespace=namespace, room = sid)
        
        else:
            print("No new activity is updated...")
            socketio.emit('activity_updated',dumps({'data':2}),namespace= namespace, room=sid)
    except Exception as e:
        print("Error while loading further details...")
        socketio.emit('activity_updated',dumps({'data':2}),namespace= namespace, room=sid) 
    return


@socketio.on("connect", namespace='/upload')
def connection_made():
    user_id = request.cookies.get('user_id')
    user_id = decrypt_fernet(user_id,current_app.config['SECRET_KEY'])
    print("Client Connected..")
    try:
        dept = connection.execute_query(f'select dept_id from user where user_id = "{user_id}" ')[0][0]
        room_name = f"{dept}_upload"
        join_room(room_name)
    except:
        pass

@socketio.on("disconnect", namespace='/upload')
def upload_connection_closed():
    print("Client disconnected !")
    user_id = request.cookies.get('user_id')
    user_id = decrypt_fernet(user_id, current_app.config['SECRET_KEY'])
    try:
        user = users[user_id]
        remove_cache(user = user)
        dept = connection.execute_query(f'select dept_id from user where user_id = "{user_id}" ')[0][0]
        room_name = f"{dept}_upload"
        leave_room(room_name)
        print("Client disconnected !")
    except:
        pass

@socketio.on('send_file_data', namespace='/upload')
@validate_user_access
def recieve_file_data(data_dict, **kwargs):
    sid = request.sid
    #{itemNo: file.itemNo, name:file.name, size:file.size, mimeType:file.mimeType , categories:file.categoies , folders:file.folders , segment:segment , data:'' }
    user_socket_id = request.sid
    user = kwargs.get('user')
    print("Data recieving for the file ....")

    folders = data_dict.get('folders')
    categories = data_dict.get('categories')
    print('item_no', data_dict['itemNo'])

    name = data_dict['name']
    url = create_url(user.id, name)
    file_uploading = None
    index = None
    error = None

    # find the index for the uploading files if it exists
    for i,x in enumerate(user.uploading_files):
            if x.name == name and x.size == data_dict['size'] and x.mimeType == data_dict['mimeType']:
                file_uploading = x
                index = i
                break

    if(folders and categories and data_dict.get('new_file_upload') and data_dict['segment'] == 1):
        # new file is being send
        print(categories, folders)
        if index:
            del user.uploading_files[x]

        if data_dict['size'] <= 200*1024*1024:
            # validate folders categories and file_name
            response =check_file_data(name, categories)
            if response:
                print("Error while validating data for the file")
                return {'error' : response}
            else:
                print('file_naming is correct')

            print("Creating new file_data....")
            user.uploading_files.append(
                FileDataDetails(
                    sid = user_socket_id, itemNo = data_dict['itemNo'],categories =categories, folders = folders, name = name, size = data_dict['size'], mimeType = data_dict['mimeType'], segment = data_dict['segment']
                )
            )
            index = len(user.uploading_files) - 1
            file_uploading = user.uploading_files[index]

            if os.path.isfile(url):
                print("Exsisting file... deleting..")
                try:
                    os.remove(url)
                except :
                    print(f"The file '{url}' error while deleting")
            with open(url, 'wb') as f:
                f.write(data_dict['data'])
            print("New file created at : ", url)
        else:
            return dumps({'error' : 'File Size too Big'})

    # adding to previous file data
    else:
        # check and get the url for the file
        print("Finding new file_data....")
        # instance of file_uploading
        if file_uploading and file_uploading.sid == user_socket_id:
            try:
                if data_dict['segment'] == file_uploading.segment + 1:
                    print("Segmnet in sequence...")
                    with open(url, 'ab') as f:
                        f.write(data_dict['data'])
                    file_uploading.segment += 1
                else:
                    print("Segmnet not in sequence...")
                    file_uploading.extraSegment[data_dict['segment']] = data_dict['data']

                keys_= list(file_uploading.extraSegment.keys())
                x = 0
                while x < len(keys_):
                    if keys_[x] == file_uploading.segment + 1:
                        print("Found segement :....", keys_[x])
                        with open(url, 'ab') as f:
                            f.write(file_uploading.extraSegment[keys_[x]])
                        file_uploading.segment += 1
                        del file_uploading.extraSegment[keys_[x]]
                        x = 0
                    else:
                        x += 1

            except:
                print("Exception while adding data to file....")
                error = 1

        # file data not found in the user uploading files
        elif not file_uploading:
            print("File not found...")
            error = 1
        
        else:
            print("User connection changed...")
            error =  1

    # all the data has been uploaded ... processing and uploading the file
    if data_dict.get('finished'):
        if index>=0:
            print("Sending progress log...")
            # upload the file from the url
            upload_file = threading.Thread(target = upload_file_toDrive, args=(index, url, user,sid)).start()
        else:
            print("File data not found in users object...")
            error = 1
    
    if error:
        remove_upload_file_data(url, index, user.uploading_files)
        return {'error' : 'Server Error, Try Again'}
    return 1

@socketio.on('clear_cache', namespace='/upload')
@validate_user_access
def remove_cache_datas(data_dict, **kwargs):
    # ... recieve error if a file upload has error... scrapes of the entire file data..
    print("Request to remove all data for the user...")
    user = kwargs['user']
    remove_cache(user)
    print(user.uploading_files)
    return 1
    
# check the upload and trahsed tables
# delete files which are greater than 7 days
# add rest of the files in html_data
@socketio.on('load_activity', namespace='/upload')
@validate_user_access
def load_acitivity(data_dict, **kwargs):
    sid = request.sid
    print("Recieved request to load upload activity....", data_dict)
    priv = kwargs['user'].privilage
    email = None
    if priv != 'admin':
        email = connection.execute_query(f'select email from user where user_id = "{kwargs["user"].id}" ')[0][0]
        print(email)

    dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{kwargs["user"].dept}" ')[0][0]
    folders = connection.execute_query(f'select folder_id, folder_name from folder where dept_id = {dept_id} ')
    today_date = date_now(onlyDate=False)
    week_ago =  today_date- timedelta(days=7)
    date = week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    date_string_today = today_date.strftime("%Y-%m-%d")
    date_formatted = today_date.strftime("%d %B, %Y")
    print('week before date : ',date)

    print("Removing data before 7 days..")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(folders)) as executor:
        try:
        # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(remove_data_activity, folder[0], date): folder[0] for folder in folders}
        except Exception as e:
            print("Exception", e)

        for future in concurrent.futures.as_completed(future_to_url):
            try:
                result = future.result()
            except Exception as exc:
                print("Exception getting activity call...")
    print("Removed data...")

    activity_details = {}
    recent_activity = []
    # data_item_id : drive_id -> for the folders
    data_item = {}
    data_item_no = 0
    no_data = []
    iconLinks_ = connection.execute_query('select mimeType_id, iconLink from mimeType')
    iconLinks = {}
    for _ in iconLinks_:
        iconLinks[_[0]] = _[1]

    for folder in folders:
        print("Folder : ", folder[1])
        activity_details[folder[1]] = []
        try:
            upload_file_data = connection.execute_query(f'select * from upload_activity where folder_id = {folder[0]}')
            print("Upload Activity len : ", len(upload_file_data))
            for file in upload_file_data:
                file_data = connection.execute_query(f'select * from files where file_id = {file[0]}')
                file_data = file_data[0]
                print(file_data[6])
                if not email or (email and email == file_data[6]):
                    data_item_no +=1
                    data = {
                        'data_item': data_item_no,
                        'name': file_data[3],
                        'icon': iconLinks[file_data[7]] if iconLinks[file_data[7]] else "/static?file_name=file-regular-24.png",
                        'owner': file_data[6][:file_data[6].find('@')].replace('.',' '),
                        'folder': folder[0],
                        'action': file[2],
                        'time': file[3],
                        'link': file_data[8],
                        'folder': folder[1]
                    }
                    data_item[data_item_no] = encrypt_fernet(data = file_data[1], key = current_app.config['SECRET_KEY']).decode()
                    if file[3] == date_string_today:
                        recent_activity.append(data)
                    else:
                        activity_details[folder[1]].append(data)

            deleted_file_data = connection.execute_query(f'select * from trashed where folder_id = {folder[0]}')
            print("Deleted Activity len : ", len(deleted_file_data))
            for file in deleted_file_data:
                print(file[5])
                if not email or (email and email == file[5]):
                    data_item_no +=1
                    data = {
                        'data_item': data_item_no,
                        'name': file[2],
                        'icon':  iconLinks[file[3]] if iconLinks[file[3]] else "/static?file_name=file-regular-24.png",
                        'folder': folder[0],
                        'action': 'trashed',
                        'time': file[4],
                        'owner': file[5][:file[5].find('@')].replace('.',' '),
                        'link': file[6],
                        'folder': folder[1]
                    }
                    data_item[data_item_no] = encrypt_fernet(data = file[0], key = current_app.config['SECRET_KEY']).decode()
                    if file[4] == date_string_today:
                        recent_activity.append(data)
                    else:
                        activity_details[folder[1]].append(data)
   
        except Exception as exc:
            print("Exception getting activity call...", exc)

        if len(activity_details[folder[1]]) < 1:
            no_data.append(folder[1])

    update_activity = threading.Thread(target = activity_forUpload, args=(folders, kwargs['user'], '/upload', sid)).start()

    print(no_data)
    return {
        'html_data' : render_template('upload/upload_activity.html', activity = activity_details,recent_activity = recent_activity, folders = folders, no_data = no_data, date = date_formatted, priv=priv), 
        'data': data_item
    }

@socketio.on('delete_file',namespace='/upload')
@validate_user_access
def delete_file_data_(data_dict, **kwargs):
    print("Recieved request to load upload activity....", data_dict)
    try:
        service = Create_Service(kwargs['user'].id)
        drive_id = data_dict['drive_id']
        drive_id = decrypt_fernet(drive_id, current_app.config['SECRET_KEY'])
        action = data_dict['action']

        if drive_id:
            if action == 'delete':
                print('permanently deleting the file')
                # completely delete the file
                file_data = connection.execute_query(f'select drive_id from trashed where drive_id = "{drive_id}"')
                file_data_ = connection.execute_query(f'select file_id from files where drive_id = "{drive_id}" ')
                if file_data or file_data_:
                    try:
                        response = service.files().delete(fileId = drive_id)
                    except Exception as e:
                        print("Exception :", e)
                        return "Cannot Delete File"
                    try:
                        delete_file_data(service, {'type':action}, drive_id, date_now(onlyDate=False).isoformat()+'Z', None )
                    except:
                        pass
                    return 'File deleted forever'
                else:
                    return 'File already Deleted'
            
            elif action == 'trash':
                print("Moving the file to trash..")
                # move the file to trash
                file_data = connection.execute_query(f'select file_id, folder_id from files where drive_id = "{drive_id}" ')
                if file_data:
                    file_data = file_data[0]
                    file_id = file_data[0]

                    body_value = {'trashed': True}
                    try:
                        response = service.files().update(fileId=drive_id, body=body_value).execute()
                    except:
                        return "Cannot Trash File"
                    try:
                        delete_file_data(service,{'type':action}, drive_id,date_now(onlyDate=False).isoformat()+'Z', file_data[1] )
                    except:
                        pass
                    return 'File moved to Trash'
                else:
                    data = connection.execute_query(f'select * from trashed where drive_id = "{drive_id}" ')
                    if data:
                        return 'File Already in Trash'
                    else:
                        return 'File not present'
            else:
                return "Cannot Delete File"
        else:
            return "Cannot Delete File"
    except Exception as e:
        print("Exception in deleting file : ", e)
        return "Cannot Delete File"

@socketio.on('rename_file',namespace='/upload')
@validate_user_access
def rename_file_data_(data_dict, **kwargs):
    print("Recieved request to load upload activity....", data_dict)
    try:
        service = Create_Service(kwargs['user'].id)
        drive_id = data_dict.get('drive_id')
        drive_id = decrypt_fernet(drive_id, current_app.config['SECRET_KEY'])
        if drive_id:
            if data_dict['new_name'] == data_dict['name']:
                return 'Same File name'
            else:
                file_id = connection.execute_query(f'select file_id from files where drive_id = "{drive_id}" and file_name = "{data_dict["name"]}" ')
                if file_id:
                    file_id = file_id[0][0]
                    # check if file naming format is correct or not
                    name_format = get_file_name_data(data_dict['new_name'])
                    creationTime = name_format[0]
                    creationTime = getCreationDate(creationTime)
                    if not creationTime:
                        return 'File format is incorrect'
                    else:
                        # change the file anem and creation Time
                        print("Renaming the file...", data_dict['new_name'])
                        file_metadata = {
                            'name': data_dict["new_name"]
                        }
                        try:
                            updated_file = service.files().update(
                                fileId=drive_id,
                                body=file_metadata,
                                fields='id, name'
                            ).execute()
                        except:
                            return "Cannot Rename File"
                        try:
                            connection.execute_query(f'update files set file_name = "{data_dict["new_name"]}", creationTime = "{creationTime}" where file_id = {file_id}')
                        except:
                            pass
                    # delete and add all categories
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
                        return 'File Renamed'
                else:
                    return 'Cannot Rename File'
        else:
            return 'Cannot Rename File'
       
    except Exception as e:
        print("Exception in deleting file : ", e)
        return "Cannot Rename File"

@socketio.on('restore_file',namespace='/upload')
@validate_user_access
def restore_file_data_(data_dict, **kwargs):
    print("Recieved request to load upload activity....", data_dict)
    try:
        service = Create_Service(kwargs['user'].id)
        drive_id = data_dict['drive_id']
        drive_id = decrypt_fernet(drive_id, current_app.config['SECRET_KEY'])
        folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{data_dict["folder"]}" ')
        folder_id = folder_id[0][0]

        if drive_id:
            # move the file to trash
            body_value = {'trashed': False}
            try:
                response = service.files().update(fileId=drive_id, body=body_value, fields="id, name, createdTime, mimeType, webViewLink, size, iconLink, owners(emailAddress), parents").execute()
            except Exception as e:
                print("Exception :", e)
                return "Cannot Restore File"
            try:
                update_file_data(response, folder_id,newEntry = True)
                add_upload_activity(folder_id = folder_id ,file_id = drive_id, action='restore', type_ ='restore', time=date_now(onlyDate=False).isoformat()+'Z')
            except:
                pass

            return 'File restored'
        else:
            return "Cannot Restore File"
    except Exception as e:
        print("Exception in deleting file : ", e)
        return "Cannot Restore File"
