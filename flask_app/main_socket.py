
from flask import render_template, url_for, request
from json import dumps
from time import sleep
from io import BytesIO
import openpyxl
import threading

from flask_app.database import connection
from flask_app.socket_connection import socketio
from flask_app.drive_func.google_drive import Create_Service, get_folders, list_permissions, change_permissions

from flask_app.other_func.global_variables import accreditions, priv, users, FileData
from flask_app.other_func.authentication import validate_user_access
from flask_app.other_func.filters import *
from flask_app.other_func.update_data import update_category_for_file


def process_file_(*args, **kwargs):
    # Process the sheet as needed
    print("\n Background Task ... Processing the Excel File")
    error = "Error while Processing ... Try Again"
    try:
        user_id = kwargs['user_id']
        user = users[user_id]
        dept_id = connection.execute_query(f'select dept_id from department where dept_name = "{user.dept}" ')[0][0]
        sheet = kwargs['sheet']
        c = 0
        file_data = []
        header = {}
        # get all the rows and header from the excel file
        for row in sheet.iter_rows(values_only=True):
            c=c+1
            if c == 1:
                fields_not_present = []
                row = [ x.lower() for x in row ]

                # check if the excel file is from criteria or not
                if 'criteria' in row and 'folder' not in row and user.file.acc:
                    print("The Excel file is from criteria")
                    pass
                # check if the excel file is from category or not
                elif 'criteria' not in row and 'folder' in row and not user.file.acc:
                    print("The Excel file is from Category")
                    pass
                else:
                    error = "Columns are incorrect ..."
                    raise Exception(error)

                for field in user.file.fields:
                    if field not in row:
                        fields_not_present.append(field)
                    else:
                        header[field] = row.index(field)
                # mandatory field is not present
                if fields_not_present:
                    error = f"Field not Present :  {fields_not_present}"
                    raise Exception(f'Fields not present :  {fields_not_present}')
            else:
                # Process the file data...
                file_data.append(row)
        sheet = None

        # Process the entire file data
        html_data = ''
        # for categories
        if not user.file.acc :
            html_data = process_categories(file_data, dept_id, header)
        # for criteria
        else:
            html_data = process_criteria(file_data, dept_id, header, user.file.acc)

        if not html_data:
            raise Exception('Error while processing the file')
        else:
            print("File Proccessed and data added to the database ...")
        file_data = f'''
            <strong>Excel File data Updated Successfully</strong>
            <div>Total data uploaded : {c-1}</div>
            {html_data}
        '''
        socketio.emit('processed_file_data', dumps({'data' : file_data}), namespace = '/update' )

    except Exception as e:
        print("Error while Processing the excel file :", e)
        socketio.emit('processed_file_data', dumps({'error' : error}), namespace = '/update')
    user.file = None
   
@socketio.on('dept_users', namespace="/profile")
@validate_user_access
def get_dept_users(data_dict, **kwargs):
    try:
        privilage = kwargs.get('user').privilage
        user_dept = connection.execute_query(f'select dept_id from department where dept_name = "{ kwargs.get("user").dept}" ')
        user_dept = user_dept[0][0] if user_dept else None

        if privilage == 'admin':
            # all the users that are under the admins department
            response = {}
            response['dept_users'] = []
            data = connection.execute_query(f'select user_id,email,name, privilage from user where dept_id = "{user_dept}" ')
            if data:
                for _ in data:
                    if _[1] != data_dict['email']:
                        response['dept_users'].append( {
                            'name' : _[2],
                            'email' : _[1],
                            'privilage' : _[3]
                        } )   
            response['available-privs'] = list(priv.keys())
            response['dept_users'] = render_template('profile/dept_users.html', dept_users = response['dept_users'], available_privs = response['available-privs'])
            return response
        else:
            return None
    except Exception as e:
        print("Exception while getting dept_users", e)
        return None
 

@socketio.on('dept_access', namespace="/profile")
@validate_user_access
def dept_access(data_dict, **kwargs):
    try:
        dept = data_dict['department']
        user_id = kwargs.get('user').id
        print("Requested dept : ",dept)
        print("Requested user_id : ",user_id)

        data = connection.execute_query(f'select dept_id from department where dept_name = "{dept}" ')
        dept_id = data[0][0] if data else None
        if not dept_id:
            dept = None
        else:
            connection.execute_query(f"update user set dept_id = '{dept_id}', privilage = '' where user_id = '{user_id}' ")

        if users[user_id]:
            users[user_id].dept = dept
            users[user_id].privilage = None
            print('Changing dept ... reset priv : ', users[user_id].privilage)
        return 1
    
    except Exception as e:
        print("Exception while updating department ..", e)
        return None


@socketio.on('priv_grant', namespace="/profile")
@validate_user_access
def priv_grant(data_dict, **kwargs):
    try:
        privilage =  data_dict['privilage']
        email = data_dict['email']
        print("Set Privilage : ", privilage)
        print("Email :", email )

        data = connection.execute_query(f'select user_id,dept_id,privilage from user where email = "{email}" ')

        if data:
            user_id = data[0][0]
            if privilage not in priv.keys():
                privilage = 'denied'
            user_details = {
                "email": email,
                "privilage" : privilage,
                "dept_id": data[0][1],
                "prev_priv": data[0][2]
            }
            ef = change_permissions(kwargs["user"].id,user_details)
            if not ef:
                connection.execute_query(f'update user set privilage = "{privilage}" where user_id = "{user_id}" ')
            else:
                raise Exception(ef)

            if users.get(user_id):
                users[user_id].privilage = privilage
            return privilage
        else:
            raise Exception("Email id is not registered")

    except Exception as e:
        print("Exception while updating privilage ...", e)
        return None


@socketio.on('remove_user', namespace="/profile")
@validate_user_access
def remove_user(data_dict, **kwargs):
    try:
        email = data_dict
        data = connection.execute_query(f'select user_id, privilage from user where email = "{email}" ')
        if data:
            user_id = data[0][0]
            connection.execute_query(f'delete from user where user_id = "{user_id}" ')
            if users.get(user_id):
                del users[user_id]
            return "Removed"
        else:
            raise Exception("Email id is not registered")

    except Exception as e:
        print("Exception while updating privilage ...", e)
        return None

@socketio.on('update-folder', namespace='/update')
@validate_user_access
def update_folder(data_dict, **kwargs):

    print("Request Recieved ...", data_dict)
    try:
        user_id = kwargs.get('user').id
        user_dept = kwargs.get('user').dept
        email = connection.execute_query(f'select email from user where user_id = "{user_id}" ')[0][0]

        response = {}
        folders = connection.dict_query(f'select folder_name, accredition from folder where dept_id = (select dept_id from department where dept_name = "{user_dept}" )')

        service = Create_Service(user_id)

        owner_email = connection.execute_query(f'select owner from department where dept_name = "{user_dept}" ')
        owner = False
        buffer = None
        response['drive_folders'] = []
        if owner_email and owner_email[0][0] == email :
            owner = True
            buffer = get_folders(service = service, all_drive = True)
            for x in buffer:
                response['drive_folders'].append({'name': x['name'], 'drive' : 1})
            buffer= get_folders(service)
            for x in buffer:
                response['drive_folders'].append({'name': x['name'], 'drive' : 'Shared Drive'})

        else:
            buffer = get_folders(service)
            for x in buffer:
                response['drive_folders'].append({'name': x['name'],'drive' : 1})

        kwargs.get('user').service = service

        update_folder = render_template('update/update-folder.html', folders = folders, accredition = accreditions, owner = owner)
        return {'data' : update_folder, 'response' : response}

    except Exception as e:
        print("Exception in update_folder() : ",e)
        return None


@socketio.on('modify-folder-list', namespace='/update')
@validate_user_access
def modify_folder(data_dict, **kwargs):
    try:
        user = kwargs.get('user')
        user_dept = connection.execute_query(f'select dept_id from department where dept_name = "{user.dept}" ')[0][0]
        service = Create_Service(user.id)
        user_email = connection.execute_query(f'select email from user where user_id = "{user.id}" ')[0][0]
        
        list_folders = data_dict['folders']
        print("List of Folders : ",list_folders)
        print("Dept", user_dept)

        database_folders = connection.dict_query(f'select folder_id,folder_name, accredition, drive_id from folder where dept_id =  "{user_dept}" ')

        for folder in list_folders:
            flag = 0
            for _ in database_folders:
                if folder['name'] == _['folder_name'] and folder['accredition'] == _['accredition']:
                    database_folders.pop( database_folders.index(_) )
                    print(folder, "Already in the database")
                    flag = 1
                    break

            if flag != 1:
                print(folder, "not in database..")
                drive_id = get_folders(service = service, name = folder['name'])

                if not drive_id:
                    drive_id = get_folders(service = service, name = folder['name'], all_drive = True)
                    if not drive_id:
                        return {'error': f"Folder {folder['name']} not present in your drive, Please create the folder"}

                drive_id = drive_id[0]['id']
                connection.execute_query(f'insert into folder(folder_name,dept_id,accredition,drive_id) values("{folder["name"]}",{user_dept},"{folder["accredition"]}","{drive_id}") ')
        
        print("Folders that are to be removed ...", database_folders)
        for folder in database_folders:
            user_perm_id = None
            perm_ = list_permissions(folder['drive_id'], user.id, service)
            print("Removing permissions for the folder :", len(perm_) )
            for permission in perm_:
                if permission['role'] != 'owner' and permission['emailAddress'] != user_email:
                    print("removing permission for :", permission['emailAddress'])
                    # remove the folder permission from all the users
                    try:
                        del_prem = service.permissions().delete(
                                    fileId = folder['drive_id'],
                                    permissionId = permission['id']
                                ).execute()
                    except:
                        pass
                elif permission['role'] != 'owner' and permission['emailAddress'] == user_email:
                    user_perm_id = permission['id']

            if user_perm_id:
                try:
                 del_prem = service.permissions().delete(
                        fileId = folder['drive_id'],
                        permissionId = user_perm_id
                    ).execute()
                except:
                 pass
            remove_folder_data(folder['folder_id'])       

        # change the priv for all the rest of the dept users
        print("Granting access for the rest of the drive folders...", list_folders)
        users_data = connection.execute_query(f'select email, privilage from user where dept_id = {user_dept}')
        print("Total Users : ", len(users_data))
        for user_ in users_data:
            user_details = {
                'email': user_[0],
                'privilage': user_[1],
                'dept_id': user_dept
            }
            change_permissions(user.id, user_details, service)

        user.service = service
        return {'response':"Folder List Updated.."}

    except Exception as e:
        print("Exception ..", e)
        return {'error' : "Cannot Modify List"}


@socketio.on('create-folder', namespace='/update')
@validate_user_access
def modify_folder(data_dict, **kwargs):
    try:
        user = kwargs.get('user')
        user_dept = connection.execute_query(f'select dept_id from department where dept_name = "{user.dept}" ')[0][0]
        user_email = connection.execute_query(f'select email from user where user_id = "{user.id}" ')[0][0]

        owner = connection.execute_query(f"select owner from department where dept_id = {user_dept}")
        if not (owner and owner[0][0] == user_email):
            return {'error':'You Cannot Create a new Folder for Department'}
        

        service = Create_Service(user.id)
        folder_name = data_dict['folder_name']
        if folder_name:

            dept_folder = connection.execute_query(f'select folder_name from folder where dept_id = {user_dept}')
            for _ in dept_folder:
                if folder_name == _[0]:
                    return {'error':'Folder Already Exists'}

            # Create a new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = None
            try:
                folder = service.files().create(body=folder_metadata, fields='id,name').execute()
            except Exception as e:
                folder = None
                print("Exception while creating new folder : ", e)
                return {'error': 'Could Not Create Folder'}

            if folder:
                connection.execute_query(f'insert into folder(folder_name,dept_id,accredition,drive_id) values("{folder["name"]}",{user_dept},"{data_dict["accredition"]}","{folder["id"]}") ')

                # change the priv for all the rest of the dept users
                print("Granting access for the rest of the drive folder...", folder["name"])
                users_data = connection.execute_query(f'select email, privilage from user where dept_id = {user_dept}')
                print("Total Users : ", len(users_data))
                for user_ in users_data:
                    user_details = {
                        'email': user_[0],
                        'privilage': user_[1],
                        'dept_id': user_dept
                    }
                    change_permissions(user.id, user_details, service, [folder["id"]])
                
            else:
                raise Exception('Could Not Create Folder')
        else:
            raise Exception('No Folder Name given')

        user.service = service
        return {"response": "Folder Created .."}

    except Exception as e:
        print("Exception ..", e)
        return {'error' : e}

@socketio.on('update-category', namespace='/update')
@validate_user_access
def update_category(data_dict, **kwargs):
    print("Request Recieved ...", data_dict)
    try:
        dept = kwargs.get('user').dept
        dept_id = connection.execute_query(f'select dept_id from department where dept_name = "{dept}" ')[0][0]

        folders = connection.dict_query(f'select folder_name from folder where dept_id = {dept_id} ')
        categories = connection.dict_query('select category,definition from category')

        return {'data' : render_template( 'update/category-layout.html', folders = folders),'category': categories}

    except Exception as e:
        print("Exception in update_category() : ",e)
        return None


@socketio.on('get-folder-cat', namespace='/update')
@validate_user_access
def get_folder_cat(data_dict, **kwargs):
    print("Request Recieved ...", data_dict)
    try:
        response = {}
        folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{data_dict["folder"]}" ')[0][0]

        folder_cat, available_cat = get_category_data(folder_id)
        update_category = render_template( 'update/update-category.html', category_list =  folder_cat)

        response['folder_category'] = folder_cat
        response['available_category'] = available_cat
        return {'data' : update_category, 'response' : response}

    except Exception as e:
        print("Exception in get_folder_cat() : ",e)
        return None


@socketio.on('modify-category', namespace='/update')
@validate_user_access
def modify_category(data_dict, **kwargs):
    print("Request Recieved ...", data_dict)
    try:
        
        folder = data_dict['folder']
        folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{folder}" ')

        if folder_id:
            folder_id = folder_id[0][0]
        else:
            return {'error' : "Folder not found"}

        categories_not_present = []
        categories_present = connection.execute_query(f"select category_id from category_folder where folder_id = {folder_id}")
        categories_present = [x[0] for x in categories_present]

        for category in data_dict['categories']:
            category_id = connection.execute_query(f'select category_id from category where category = "{category}" ')
            if not category_id:
                categories_not_present.append(category)
            else:
                category_id = category_id[0][0]

                if category_id in categories_present:
                    print(category, "Category present in the database ..")
                    categories_present.pop( categories_present.index(category_id))

                else:
                    print(category, "Adding in the database ..")
                    connection.execute_query(f'insert into category_folder values({category_id},{folder_id})')
        
        print("Categories to be deleted : ", categories_present)
        for x in categories_present:
            connection.execute_query(f'delete from category_folder where category_id = {x} and folder_id = {folder_id} ')

        print("categories not present are :", categories_not_present)
        if not categories_not_present:
            return 1
        else:
            return {'error' : f"{categories_not_present} are not in the category list, create new category "}

    except Exception as e:
        print("Exception while modifying category_folder_list", e)
        return {"error":"Cannot Modify List"}


@socketio.on('add-new-category', namespace='/update')
@validate_user_access
def new_category(data_dict, **kwargs):
    print("Recieved : ", data_dict)
    # check for the category_name and def and if it exists or not
    # else return error --> category already present | incorrect value
    # return 1 if everything correct
    try:
        category = data_dict['name'].upper()
        definition = data_dict['def']
        folder = data_dict['folder']

        cat_present = connection.execute_query('select category from category')
        cat_present = [x[0] for x in cat_present]
        flag = 1  if category in cat_present else 0

        if flag == 1:
            return {"error" : f"Category {category} already present.."}
        else:
            print(category)
            print(len(category))
            if len(category) > 5 or len(category) < 3:
                return {"error":"Cateogry naming Error"}

            connection.execute_query(f'insert into category(category, definition) values("{category}","{definition}")')

            categories = connection.dict_query('select category,definition from category')
            category_id = connection.execute_query(f'select category_id from category where category = "{category}" ')[0][0]

            if category_id:
                # creating a thread and updating files .... anme for the category

                update_thread = threading.Thread(target = update_category_for_file, args=(category_id, category))
                update_thread.start()

            folder_id = None
            if folder != '1':
                folder_id = connection.execute_query(f'select folder_id from folder where folder_name = "{folder}" ')[0][0]

            if folder_id and category_id:
                print("Adding the category into the folder",  folder)
                #inserting the new category in the folder
                connection.execute_query(f'insert into category_folder values({category_id},{folder_id})')

            return {'response':categories}
    except Exception as e:
        print("Exception while creating new category", e)
        return {"error":"Cannot add Category"}

@socketio.on('delete-category', namespace='/update')
@validate_user_access
def delete_category(data_dict, **kwargs):
    print("Recieved : ", data_dict)
    # check for the category_name and def and if it exists or not
    # else return error --> category already present | incorrect value
    # return 1 if everything correct
    try:
        if data_dict:
            cat_id = connection.execute_query(f'select category_id from category where category = "{data_dict}" ')
            if cat_id:
                remove_category_data(cat_id[0][0])
                categories = connection.dict_query('select category,definition from category')
                return {'response':categories}
            else:
                return {"error":"Category not present"}
        else:
            return {"error":"Cannot Delete Category"}
    except Exception as e:
        print("Exception while creating new category", e)
        return {"error":"Cannot Delete Category"}


@socketio.on('modify_old_category', namespace='/update')
@validate_user_access
def modify_category_def(data_dict, **kwargs):
    print("Recieved : ", data_dict)
    try:
        category = connection.dict_query(f'select * from category where category = "{data_dict["category"]}" ')[0]
        if not category or not data_dict['definition']:
            return {"error":"Category is not present, Add new Category"}
        
        connection.execute_query(f"update category set definition = '{data_dict['definition']}' where category_id = {category['category_id']} ")
        categories = connection.dict_query('select category,definition from category')
        return {'response':categories}

    except Exception as e:
        print("Exception while modifying the category", e)
        return {"error":"Cannot Modify Category"}

@socketio.on('recieve_file_data', namespace='/update')
@validate_user_access
def recieve_file(data_dict, **kwargs):
    
    print()
    # recieve file with category_list and file_name --> if multiple
    # unpack the xlsx or csv --> read in the format for code definition and folder
    # raise alert if --> category not present and ask if create new category
    # add those category to the respective folders

    user_socket_id = request.sid
    user = kwargs.get('user')
    print("Data recieved for the file ....")

    try:
        print(user.file.sid)
        if (user.file.sid != user_socket_id) and not(data_dict.get('file_size') and data_dict.get('file_name')) :
            print("Not same sid..")
            user.file = None
            return {"error":"Try Again"}

        if data_dict.get('file_size') and data_dict.get('file_name') and not user.file.Lock:
            print("Has the FileData object..")
            user.file = FileData(user_socket_id, data_dict['file_size'], data_dict['file_name'])

            if data_dict.get('acc'):
                user.file.acc = data_dict['acc']
                user.file.fields = ['serial no', 'criteria', 'definition', 'category']
            else:
                user.file.fields = ['serial no', 'category', 'folder', 'definition']

    except:
        print("User has no FileData object... Creating...")
        user.file = FileData(user_socket_id, data_dict['file_size'], data_dict['file_name'])
        print(user.file.name, user.file.total_size)
        if data_dict.get('acc'):
                user.file.acc = data_dict['acc']
                user.file.fields = ['serial no', 'criteria', 'definition', 'category']
        else:
            user.file.fields = ['serial no', 'category', 'folder', 'definition']

        if not user.file.name.endswith('.xlsx') and not user.file.name.endswith('.csv'):
            return {"error":"Not an Excel or csv File"}
        
        if user.file.total_size == 0:
            return {"error":"File has no data"}
        
        # limit size if 50 MB
        if user.file.total_size > (50*1024*1024):
            return {"error":"File is Too Large"}

    user.file.file_data += data_dict['file_data']
    print("length of recieved file : ", len(data_dict['file_data']))
    user.file.read_size += len(data_dict['file_data'])
    print("Data read till now :", user.file.read_size)

    if( data_dict.get('finished') == 1 ):
        print("All data Collected..")
        print(user.file.total_size, user.file.read_size)

        if user.file.total_size > user.file.read_size:
            return {"error":"Try Again"}

        if user.file.name.endswith('.xlsx'):
            print("Excel file it is ...")

            try:
                # Convert the received chunk back to a BytesIO object
                chunk_bytes_io = BytesIO(user.file.file_data)
                user.file.file_data = None
                # Load the Excel file using openpyxl
                wb = openpyxl.load_workbook(chunk_bytes_io)
                # Access a specific sheet (modify as needed)
                sheet = wb.active
                
                # starting background task for processing the file
                socketio.start_background_task(target = process_file_, sheet = sheet,user_id = user.id)

            except Exception as e:
                user.file = None
                print("Exception while reading the excel file", e)
                return {"error":"Corrupt File, Try Again.."}

        elif user.file.name.endswith('.csv'):
            print("CSV file it is ...")
            return {'error': "CSV file not supporeted"}
            user.file = None

    return 1

@socketio.on('criteria-data', namespace='/update')
@validate_user_access
def criteria_details(data_dict, **kwargs):
    print("Recieved data... ,", data_dict)
    acc = data_dict['accredition']
    try:
        acc_id = connection.execute_query(f'select id from accreditions where accredition = "{acc}" ')
        if acc_id:
            acc_id = acc_id[0][0]
            criteria = get_criteria_data(acc_id)
            data = render_template('update/update-criteria.html', criteria = criteria)
            categories = connection.dict_query('select category,definition from category')
            return {'error' : 0, 'response' : {'criteria': criteria, 'data' : data,'categories' : categories}}
        else:
            print("invalid Accredition")
            return {'error' : "Invalid Accredition"}

    except Exception as e:
        print("Exception while criteria_details()", e)
        return {'error' : "Reload and Try Again"}


@socketio.on('add-criteria', namespace='/update')
@validate_user_access
def add_new_criteria(data_dict, **kwargs):
    sleep(1)
    print("Recieved data... ", data_dict)
    try:
        if data_dict.get('criteria') and data_dict.get('definition') and data_dict.get('accredition'):
            try:
             float(data_dict['criteria'].replace('.',''))
            except:
                return {"error":"Criteria Name can only contain numbers or (.)"}
            acc_id = connection.execute_query(f'select id from accreditions where accredition = "{data_dict["accredition"]}" ')
            criteria_id = connection.execute_query(f'select criteria_id from criteria where criteria_number = "{data_dict["criteria"]}" ')

            # Validate the code for the criteria

            if acc_id: 
                if not criteria_id:
                    acc_id = acc_id[0][0]
                    connection.execute_query(f'insert into criteria(criteria_number, definition, accredition_id) values("{data_dict["criteria"]}", "{data_dict["definition"]}", {acc_id} )')
                    criteria_id = connection.execute_query(f'select criteria_id from criteria where criteria_number = "{data_dict["criteria"]}" ')[0][0]

                    if data_dict.get('categories'):
                        for x in data_dict.get('categories'):
                            cat_id = connection.execute_query(f'select category_id from category where category = "{x}" ')
                            if cat_id:
                                cat_id = cat_id[0][0]
                                flag = connection.execute_query(f'select criteria_id from criteria_category where criteria_id = {criteria_id} and category_id = {cat_id} ')
                                if not flag:
                                    connection.execute_query(f'insert into criteria_category values({criteria_id},{cat_id})')
                    return 1
                else:
                    return {"error":"Criteria already present"}
            else:           
                return {"error":"Accredition not present"}
        else:
            return {"error":"All the Fields are not filled"}
    
    except Exception as e:
        print("Exception while criteria_details()", e)
        return {"error":"Cannot Add new Criteria"}


@socketio.on('modify-criteria', namespace='/update')
@validate_user_access
def modify_criteria(data_dict, **kwargs):
    print("Recieved data... ,", data_dict)
    try:
        if data_dict.get('criteria') and data_dict.get('definition'):
            criteria_id = connection.execute_query(f'select criteria_id from criteria where criteria_number = "{data_dict["criteria"]}" ')

            # Validate the code for the criteria
            if criteria_id:
                criteria_id = criteria_id[0][0]
                # Updating the new definition
                connection.execute_query(f'update criteria set definition = "{data_dict["definition"]}" where criteria_id = {criteria_id} ')

                connection.execute_query(f'delete from criteria_category where criteria_id = {criteria_id}')
                rejected_categories = []

                for x in data_dict.get('categories'):
                    cat_id = connection.execute_query(f'select category_id from category where category = "{x}" ')
                    if cat_id:
                        cat_id = cat_id[0][0]
                        connection.execute_query(f'insert into criteria_category values({criteria_id},{cat_id})')
                        print("Added category...", x)
                    else:
                        rejected_categories.append(x)

                if rejected_categories:
                    return {"error":f"Category not present{rejected_categories}"}

                return 1
            else:
                return {"error":"Criteria is not present, add new Criteria"}
        else:
            return {"error":"Code and Definition are not filled"}
    except Exception as e:
        print("Exception while modifying criteria_details()", e)
        return {"error":"Cannot Modify Criteria"}

@socketio.on('remove-criteria', namespace='/update')
@validate_user_access
def remove_criteria(data_dict, **kwargs):
    print("Recieved data... ,", data_dict)
    try:
        if data_dict:
            criteria_id = connection.execute_query(f'select criteria_id from criteria where criteria_number = "{data_dict}" ')

            # Validate the code for the criteria
            if criteria_id:
                criteria_id = criteria_id[0][0]
                # Updating the new definition
                connection.execute_query(f'delete from criteria where criteria_id = {criteria_id} ')
                connection.execute_query(f'delete from criteria_category where criteria_id = {criteria_id} ')
                return 1
            else:
                return {"error":"Criteria is not present"}
        else:
            return {"error":"Cannot delete Criteria"}
    except Exception as e:
        print("Exception while modifying criteria_details()", e)
        return {"error":"Cannot delete Criteria"}


@socketio.on('change_dept_owner', namespace='/admin')
@validate_user_access
def change_owner(data_dict, **kwargs):
    print("Changing owner...", data_dict)
    try:
        dept = data_dict.get("dept")
        email = data_dict.get("email")
        if dept and email:
            if connection.execute_query(f'select * from user where email = "{email}" '):
                connection.execute_query(f'update department set owner = "{email}" where dept_name = "{dept}" ')
                connection.execute_query(f'update user set privilage="admin" where email = "{email}" ')
                print("owner changed")
                return 1
        else:
            return {'error' : "Missing data values"}
    except Exception as e:
        print("Exception...", repr(e))
        return {'error': 'Cannot change department owner'}
