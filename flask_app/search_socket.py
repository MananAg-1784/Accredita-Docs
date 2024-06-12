

from flask_socketio import rooms, join_room, leave_room, close_room, emit
from flask import render_template, render_template_string, url_for, request, current_app
from json import loads,dumps
from time import sleep
import concurrent.futures
import threading

from flask_app.database import connection
from flask_app.socket_connection import socketio
from flask_app.drive_func.google_drive import Create_Service

from flask_app.other_func.authentication import validate_user_access
from flask_app.other_func.enc_dec import encrypt_fernet, decrypt_fernet
from flask_app.other_func.update_data import getCreationDate, get_file_name_data, delete_file_data
from flask_app.other_func.filters import  dept_category_list, get_criteria_data
from flask_app.other_func.files import check_filters, check_actitivty, search_folder_files, get_insights
from flask_app.other_func.global_variables import date_now

def activity_(folders, user, namespace,sid, dept_id):
    # check activity for folders
    try:
        room_name = f"{dept_id}_search"
        socketio.emit('stream_updated',dumps({'data':1}),namespace= namespace, room = room_name)
        sleep(1)
        folder_data = []
        updated = ''
        for folder in folders:
            folder_details = connection.execute_query(f'select folder_id, drive_id, lastActivityCheckTime from folder where folder_name = "{folder}" ')
            folder_data.append({
                'folder': folder,
                'folder_id': folder_details[0][0],
                'drive_id': folder_details[0][1],
                'last_check_time': folder_details[0][2]
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(folders)) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(check_actitivty, x['drive_id'], x['folder_id'], x['last_check_time'], user): x['folder'] for x in folder_data}

            for future in concurrent.futures.as_completed(future_to_url):
                folder_name = future_to_url[future]
                try:
                    data = future.result()
                    print(data)
                    if data:
                        updated += folder_name + ' '
                except Exception as exc:
                    print("Exception while check_activity call...", exc)
        
        if updated:
            print("Data is updated for folder",updated)
            socketio.emit('stream_updated',
                        dumps({'data':f'Stream Updated for Folder: {updated}'}), 
                        namespace=namespace,
                        room = room_name)
        else:
            socketio.emit('stream_updated',dumps({'data':2}),namespace= namespace, room = room_name)
    except Exception as e:
        print("Error while loading further details...")
        socketio.emit('stream_updated',dumps({'data':2}),namespace= namespace, room=room_name)
    return
  

@socketio.on("connect", namespace='/search')
def connection_made():
    user_id = request.cookies.get('user_id')
    user_id = decrypt_fernet(user_id,current_app.config['SECRET_KEY'])
    try:
        dept = connection.execute_query(f'select dept_id from user where user_id = "{user_id}" ')[0][0]
        room_name = f"{dept}_search"
        join_room(room_name)
        print("Client Connected..")
    except:
        pass

@socketio.on("disconnect", namespace='/search')
def connection_closed():
    print(rooms())
    user_id = request.cookies.get('user_id')
    user_id = decrypt_fernet(user_id,current_app.config['SECRET_KEY'])
    try:
        dept = connection.execute_query(f'select dept_id from user where user_id = "{user_id}" ')[0][0]
        room_name = f"{dept}_search"
        leave_room(room_name)
        print("Client disconnected !")
        print(rooms())
    except:
        pass
          
@socketio.on('get-category-data', namespace='/search')
@validate_user_access
def category_data(data_dict , **kwargs):
    print(rooms())
    print("Data Recieved...", data_dict)
    try:
        dept_id = kwargs.get('user').dept
        dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{dept_id}" ')
        if dept_id:
            dept_id = dept_id[0][0]
            data = dept_category_list(dept_id)
            return data
        else:
            return {'response': None}
    except Exception as e: 
        print("Error in category_data() ...", e)
        return None


@socketio.on('get-criteria-data', namespace='/search')
@validate_user_access
def criteria_data(data_dict , **kwargs):
    print("Data Recieved...", data_dict)
    try:
        accredition_data = {}
        acc = connection.dict_query('select * from accreditions')
        for _ in acc:
            criteria = get_criteria_data(_['id'])
            accredition_data[_['accredition']] = criteria
        return accredition_data
    except Exception as e:
        print("Error in criteria_data() ...", e)
        return None


@socketio.on('search_using_category', namespace='/search')
@validate_user_access
def search_category(data_dict, **kwargs):
    sid = request.sid
    response = {'error' : 0, 'response' : {'data_list' : ''}}
    try:
        user = kwargs.get('user')
        dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{user.dept}" ')[0][0]
        
        if check_filters(data_dict, dept_id):
            raise Exception("Filter values are Broken, Reload and Try again... ")

        # check activity
        
        # data_dict => year month folders:list category:list
        files_list = search_folder_files(folders = data_dict['folders'], user = user, category = data_dict['category'], year = data_dict['year'], month = data_dict['month'])
        
        checking_activity = threading.Thread(target=activity_, args=(data_dict['folders'], user, '/search',sid, dept_id))
    
        files_data = files_list.get('data')
        category_data = files_list.get('filter_data')
        data_item_list = files_list.get("data_item")

        # sort the category_data based on decreasing order of no of files
        category_data.sort(key=lambda key: len(files_data[key['category']]), reverse=True)

        if files_list:
            response['response']['data_list'] = render_template('search/search_category_layout.html', data = files_data, category_data = category_data)
            response['error'] = files_list.get('error')

            for x in data_item_list.keys():
                _data_ = encrypt_fernet(data_item_list[x], current_app.config['SECRET_KEY']).decode()
                data_item_list[x] = _data_
            response['response']['data_item_list'] = data_item_list
                
    except Exception as e:
        print("Exception in searching using category ...", e)
        response['error'] = "Server Error, Try Again.."

    checking_activity.start()
    return dumps(response)

@socketio.on('search_using_criteria', namespace='/search')
@validate_user_access
def search_criteria(data_dict, **kwargs):
    sid = request.sid
    response = {'error' : 0, 'response' : {'data_list' : ''}}
    try:
        user = kwargs.get('user')
        dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{user.dept}" ')[0][0]
        
        if check_filters(data_dict, dept_id):
            raise Exception("Filter values are Broken, Reload and Try again... ")

        checking_activity = threading.Thread(target=activity_, args=(data_dict['folders'], user, '/search',sid, dept_id))

        # data_dict => year month folders:list criteria:list
        files_list = search_folder_files(folders = data_dict['folders'], user = user, criteria = data_dict['criteria'], year = data_dict['year'], month = data_dict['month'])

        files_data = files_list.get('data')
        criteria_data = files_list.get('filter_data')
        data_item_list = files_list.get("data_item")

        if files_list:
            response['response']['data_list'] = render_template('search/search_criteria_layout.html', data = files_data, criteria_data = criteria_data)
            response['error'] = files_list.get('error')

            for x in data_item_list.keys():
                _data_ = encrypt_fernet(data_item_list[x], current_app.config['SECRET_KEY']).decode()
                data_item_list[x] = _data_
            response['response']['data_item_list'] = data_item_list
        
    except Exception as e:
        print("Exception in searching using criteria ...", e)
        response['error'] = "Server Error, Try Again.."

    checking_activity.start()
    return dumps(response)


@socketio.on('get_folder_insights', namespace='/search')
@validate_user_access
def get_insights_data(data_dict, **kwargs):
    print(data_dict)
    response = {'error' : 0, 'response' : None}
    try:
        user = kwargs.get('user')
        dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{user.dept}" ')[0][0]

        insights = get_insights(data_dict.get('folder'))
        response['response']= render_template('search/folder_insights_layout.html', data = insights, folders = data_dict['folder'])
        
    except Exception as e:
        print("Exception in getting insights ...", e)
        response['error'] = "Server Error, Try Again.."

    return dumps(response)


@socketio.on('delete_file',namespace='/search')
@validate_user_access
def delete_file_data_search(data_dict, **kwargs):
    print("Recieved request to load upload activity....", data_dict)
    try:
        service = Create_Service(kwargs['user'].id)
        drive_id = data_dict['drive_id']
        drive_id = decrypt_fernet(drive_id, current_app.config['SECRET_KEY'])
        action = data_dict['action']

        if drive_id:
            if action == 'trash':
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
                        return 'Cannot Trash File'

                    try:
                        delete_file_data(service,{'type':action}, drive_id, date_now(onlyDate=False).isoformat()+'Z', file_data[1] )
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


@socketio.on('rename_file',namespace='/search')
@validate_user_access
def rename_file_data_search(data_dict, **kwargs):
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


@socketio.on('ignore_file', namespace='/search')
@validate_user_access
def ignore_file(data_dict, **kwargs):
    print(data_dict)
    response = {'error' : 0, 'response' : None}
    try:
        user = kwargs.get('user')
        file_id = connection.execute_query(f'select file_id from files where drive_id = "{data_dict["drive_id"]}" ')[0][0]
        folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{data_dict["folder"]}" ')[0][0]

        connection.execute_query(f"insert into ignored_files values({file_id},{folder_id},'{data_dict['reason']}' )")

        response['response'] = 'File Added to Ignore list'

    except Exception as e:
        print("Exception in getting insights ...", e)
        response['error'] = "Cannot Ignore File"

    return dumps(response)


@socketio.on('include_file', namespace='/search')
@validate_user_access
def include_file(data_dict, **kwargs):
    print(data_dict)
    response = {'error' : 0, 'response' : None}
    try:
        user = kwargs.get('user')
        file_id = connection.execute_query(f'select file_id from files where drive_id = "{data_dict["drive_id"]}" ')[0][0]
        folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{data_dict["folder"]}" ')[0][0]

        ignored = connection.execute_query(f'select * from ignored_files where file_id = {file_id} and folder_id = {folder_id} ')
        if ignored:
            connection.execute_query(f'delete from ignored_files where file_id = {file_id} and folder_id = {folder_id}')
      
            response['response'] = 'File removed from Ignore list'
        else:
            response['error'] = "File already included"

    except Exception as e:
        print("Exception in getting insights ...", e)
        response['error'] = "Cannot Include File"

    return dumps(response)

@socketio.on('add_file_category', namespace='/search')
@validate_user_access
def add_file_category(data_dict, **kwargs):
    print(data_dict)
    response = {'error' : 0, 'response' : None}
    try:
        user = kwargs.get('user')
        file_id = connection.execute_query(f'select file_id, folder_id from files where drive_id = "{data_dict["drive_id"]}" ')[0]
        folder_id = file_id[1]
        file_id = file_id[0]
        categories = connection.execute_query(f'select category_id from file_category where file_id = {file_id} ')
        category_id = connection.execute_query(f'select category_id from category where category = "{data_dict["category"]}" ')[0][0]
        flag = 1
        for category in categories:
            if category_id == category:
                flag = 0
                break
        if flag == 1:
            connection.execute_query(f'insert into file_category values({file_id},{category_id})')
            response['response'] = 'Category Added to File'
        else:
            response['error'] = 'Category already present for File'
        connection.execute_query(f'insert into ignored_files values({file_id},{folder_id},"Category added to File")')

    except Exception as e:
        print("Exception in getting insights ...", e)
        response['error'] = "Cannot Add Category"

    return dumps(response)


@socketio.on('rename_file_insights', namespace='/search')
@validate_user_access
def rename_file_insights(data_dict, **kwargs):
    print(data_dict)
    response = {'error' : 0, 'response' : None}
    try:

        file_id = connection.execute_query(f'select file_id, folder_id from files where drive_id = "{data_dict["drive_id"]}" ')[0]
        folder_id = file_id[1]
        file_id = file_id[0]
        category_id = connection.execute_query(f'select category_id from category where category = "{data_dict["category"]}" ')[0][0]
        flag = 1

        if file_id:
            # check if file naming format is correct or not
            name_format = get_file_name_data(data_dict['name'])
            creationTime = name_format[0]
            creationTime = getCreationDate(creationTime)
            if not creationTime:
                print("Incorrect")
                response['response'] = 'File Format is incorrect'
            else:
                service = Create_Service(kwargs['user'].id)
                # change the file anem and creation Time
                print("Renaming the file...", data_dict['name'])
                file_metadata = {
                    'name': data_dict["name"]
                }
                try:
                    updated_file = service.files().update(
                        fileId=data_dict["drive_id"],
                        body=file_metadata,
                        fields='id, name'
                    ).execute()
                except:
                    return "Cannot Rename File"
                try:
                    connection.execute_query(f'update files set file_name = "{data_dict["name"]}", creationTime = "{creationTime}" where file_id = {file_id}')
                except:
                    pass

            # delete and add all categories
            connection.execute_query(f'delete from file_category where file_id = {file_id}')
            category = name_format[1]
            # multiple categories...
            if not category:
                print("No category for the file...")
            else:
                if data_dict['category'] == category:
                    connection.execute_query(f'insert into file_category values({file_id},{category_id})')
                response['response'] = 'File Renamed'
        else:
            response['error'] = 'Cannot Rename File'
    except Exception as e:
        print("Exception in getting insights ...", e)
        response['error'] = 'Cannot Rename File'

    return dumps(response)

