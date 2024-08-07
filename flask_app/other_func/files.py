
from datetime import datetime, timedelta
from time import sleep
import concurrent.futures

from flask_app.database import connection
from flask_app.other_func.global_variables import activity_flag, Insights, date_now
from flask_app.other_func.update_data import get_file_name_data,update_file_data,add_upload_activity, delete_file_data

from flask_app.drive_func.google_drive import get_creds, Create_Service, get_files
from flask_app.drive_func.drive_activity import get_activity

def convert_bytes(size_bytes):
    # Define the units and their respective sizes
    units = ['B', 'KB', 'MB']
    # Initialize variables
    index = 0
    size = 0
    try:
        size = float(size_bytes)
    except:
        return ''
    # Convert bytes to larger units
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    # Return the formatted result
    return f"{round(size)} {units[index]}"

def check_filters(data, dept_id):
    try:
        keys = data.keys()
        # check if all keys contains value in it
        for key in keys:
            if not data[key]:
                print("Keys do not have value")
                return 1
        
        # checking for all the folders selected
        folders = connection.execute_query(f'select folder_name from folder where accredition = "{data["accredition"]}" and dept_id = {dept_id} ')
        folders = [ x[0] for x in folders ]
        for x in data['folders']:
            if x not in folders:
                print("Folders broken value")
                return 1
        
        # checking for all the categories
        if data.get('category'):
            categories = connection.execute_query(f'select category from category')
            categories = [ x[0] for x in categories ]
            for x in data['category']:
                if x not in categories:
                    print("Category brokwn value")
                    return 1

        # checking for all the criteria
        if data.get('criteria'):
            try:
                acc_id = connection.execute_query(f'select id from accreditions where accredition = "{data["accredition"]}" ')[0][0]
                criterias = connection.execute_query(f'select criteria_number from criteria where accredition_id = {acc_id}')
                criterias = [ x[0] for x in criterias ]
                for x in data['criteria']:
                    if x not in criterias:
                        print("Criteria broken value")
                        return 1
            except: 
                return 1

        # checking for datetime for academic year
        today_date = date_now()
        if data['year'] > today_date.year:
            print("Academic year broken value")
            return 1
        else:
            if data['year'] == today_date.year and data['month'] > today_date.month:
                print("Academic year broken value")
                return 1

    except Exception as e:
        print("Exception in checking the filters...", e)
        return 1

def new_file_details(file_name, file_id, drive_id, folder_id, service, action = None):
    try:
        # retriving the data for the file
        file_data = None
        flag = 0
        files_data = get_files(parent_id=drive_id, service=service, name = file_name)
        print('Drive_id to be checked : ',file_id )
        print("Files data :", len(files_data))
        for file_data in files_data:
            print("Files data_id :", file_data['id'])
            if file_data["id"] == file_id:
                print("New file is created...")
                update_file_data(file_data, folder_id, newEntry =True)
                flag = 1
                break
        if flag == 0:
            print("File not found in the drive, Not to be Added...")
    except Exception as e:
        print("Exception in adding new file_data :",e)

def delete_file_data_for_folder(drive_id, file_id=None):
    if drive_id: 
        file_id = connection.execute_query(f'select file_id from files where drive_id = "{drive_id}" ')
        if file_id:
            file_id = file_id[0][0]
    if file_id:
        connection.execute_query(f'delete from file_category where file_id = {file_id}')
        connection.execute_query(f'delete from files where drive_id = "{drive_id}" ')
        connection.execute_query(f'delete from upload_activity where file_id = "{file_id}" ')
        connection.execute_query(f'delete from ignored_files where file_id = {file_id}')
        if trash:
            connection.execute_query(f'delete from trashed where drive_id = "{drive_id}" ')
    else:
        print("File data not present...")

# checks for the activity of the folder and stash changes accordinly
def check_actitivty(drive_id, folder_id, lastCheckTime, user, forceExec=False):
    flag = 0
    service = None
    sleep(1)
    while True:
        print(activity_flag.folder_id)
        if drive_id in activity_flag.folder_id:
           #  print("Activity for the file is already checking... wait")
            flag += 1
            sleep(1)
            return 0
        else:
            print("Flag : ",flag)
            if flag > 0:
                print("Function that had been executing finished......")
                try:
                    del activity_flag.folder_id[activity_flag.folder_id.index(drive_id)]
                except:
                    pass
                # the function has waited for the func to finish
                return connection.execute_query(f'select updated from folder where folder_id = {folder_id}')[0][0]
            else:
                print("---- Function is to be executed for the folder ----")
                break
    
    activity_updated = 0
    activity_flag.folder_id.append(drive_id)
    today_date = date_now()
    try:
        # lock to the folder
        service = Create_Service(user.id)
        creds = get_creds(user.id)
        checked = 1
        # activity has not been checked till now
        # update data into the database
        print("Last activiy checked time : ",lastCheckTime)

        if not lastCheckTime:
            print("Files are not scanned once also .....")
            files_data = get_files(drive_id, service)
            print(len(files_data))
            if files_data:
                activity_updated= 1
            
            for file_data in files_data:
                try:
                    # update the file data into the database
                    update_file_data(file_data, folder_id, newEntry = True)
                except Exception as e:
                    print("Exception in adding file data for file : ", file_data['name'], " ", e)

            # remove all the files that are extra in the database
            drive_ids = [ x['id'] for x in files_data ]
            print("Files present in drive : ",len(drive_ids))
            files_in_database = connection.execute_query(f'select drive_id from files where folder_id = {folder_id} ')

            files_to_be_deleted = []
            for x in files_in_database:
                if x[0] not in drive_ids:
                    print("file to be deleted : ", x[0])
                    files_to_be_deleted.append(x[0])
                    
            for x in files_to_be_deleted:
                file_id = connection.execute_query(f'select file_id from files where drive_id = "{x}" ')
                if file_id:
                    file_id = file_id[0][0]
                    # remove the file data from every where
                    delete_file_data_for_folder(x, file_id)
                
            # find the activity of the last 7 days and update in the tables
            # just update the activity data in the tables
            week_ago =  today_date - timedelta(days=7)
            date = week_ago.replace(hour=0, minute=0, second=0, microsecond=0)
            current_time_milliseconds = int(date.timestamp() * 1000)
            activities = get_activity(
                creds = creds,
                user_id = user.id,
                folder_id =  drive_id,
                after_time = current_time_milliseconds,
                action_case= ['CREATE','DELETE','RESTORE']
                )  

            if not activities:
                print("No activities for the folder within the last 7 days")
            
            else:
                activity_updated +=1
                print("Updating upload activities....")
                activities.reverse()
                for activity in activities:
                    print(activity)
                    action = activity["action"]
                    try:
                        if action == 'create' or action == 'restore':
                            print("Create / Restored...")
                            new_file_details(activity["file_name"], activity["file_id"], drive_id, folder_id, service, action = action)
                            
                            add_upload_activity(folder_id, activity['file_id'], action=action, type_=activity.get('action_details', None), time=activity['timestamp'])
                        
                        elif action == 'delete':
                            # if the file is trashed
                            if activity['action_details']['type'].lower() == 'trash':
                                print("Details of the file trashed...")

                                delete_file_data(service,activity['action_details'],activity['file_id'],activity['timestamp'], folder_id)
                            # the file was deleted completely
                            else:
                                print("Permanently Deleted...")
                                pass
                    
                    except Exception as e:
                        print("Exception while entering record for activity.. ", e)

        else:
            datetime_object = datetime.strptime(lastCheckTime, "%Y-%m-%d %H:%M:%S.%f")
            today_date_ = date_now(onlyDate = False)
            if forceExec or (datetime_object < today_date_ and today_date_ - datetime_object >= timedelta(minutes = 15)):
                print("Checking activity...")
                current_time_seconds = datetime_object.timestamp()
                current_time_milliseconds = int(current_time_seconds * 1000)

                try:
                    recent_activities = get_activity(
                        creds = creds,
                        user_id = user.id,
                        folder_id= drive_id,
                        after_time = current_time_milliseconds
                        )
                except Exception as e:
                    print("Exception while getting activities...",e)
                    checked = 0

                # going through each activity that occured and changing it in the database
                if not recent_activities:
                    recent_activities = []
                    print("No new Activities")
                
                else:
                    activity_updated += 1
                    recent_activities.reverse()
                    for activity in recent_activities:
                        action = activity["action"]
                        print(activity)
                        try:
                            # NEW file details in the database
                            if action == "create" or action == 'restore':
                                print("Adding new file...")
                                new_file_details(activity["file_name"], activity["file_id"], drive_id, folder_id, service, action = action)
                                
                                # activity['file_id] -> file_drive_id
                                add_upload_activity(folder_id, activity['file_id'], action=action, type_=activity.get('action_details', None), time=activity['timestamp'])
                                activity_updated +=1
                            
                            # DELETE file details
                            elif action == 'delete':
                                print("deleting files data...", activity["file_name"])
                                print(activity.get('action_details',None), activity['file_id'], activity['timestamp'], folder_id)
                                
                                delete_file_data(service = service,action = activity.get('action_details',None) ,file_drive_id = activity['file_id'], time=activity['timestamp'], folder_id= folder_id)
                                activity_updated +=1
                                
                            # NEW file_details / DELETE file_details
                            elif action == 'move':
                                print("File is moved...")
                                flag = 0
                                # check if the file ids added to the folder
                                added_parents = activity.get("action_details").get("addedParents")
                                print(added_parents)
                                if added_parents:
                                    for parent in added_parents:
                                        try:
                                            parent = parent.get('driveItem')
                                            folder_id_ = parent.get('name','').replace('items/', '')
                                            if folder_id_ == drive_id:
                                                print("Adding new file..")
                                                new_file_details(activity["file_name"], activity["file_id"], drive_id, folder_id, service)
                                                flag = 1
                                                break
                                        except:
                                            pass

                                # file is not added to the folder --> removed
                                if flag == 0:
                                    removed_parents =  activity.get("action_details").get("removedParents")
                                    print(removed_parents)
                                    if removed_parents:
                                        for parent in removed_parents:
                                            try:
                                                parent = parent.get('driveItem')
                                                folder_id_ = parent.get('name','').replace('items/', '')
                                                if folder_id_ == drive_id:
                                                    print("deleting file data...")
                                                    delete_file_data_for_folder(drive_id = activity['file_id'])
                                                    break
                                            except:
                                                pass

                            # UPDATE the file details --> NAME
                            elif action == 'rename':
                                old_file_ids = connection.execute_query(f'select drive_id from files where file_name = "{activity["action_details"]["oldTitle"]}" ')

                                if old_file_ids:
                                    for old_file in old_file_ids:
                                        id_ = old_file[0]
                                        if id_ == activity['file_id']:
                                            print("renaming file...")
                                            update_file_data(
                                                file_data = {"id" : id_, "name": activity["file_name"]},
                                                folder_id = folder_id,
                                                action = 'rename'
                                            )
                                            break
                                else:
                                    new_file_details(activity["file_name"], activity["file_id"], drive_id, folder_id, service)

                            # GET The file_data and check if any changes are there
                            # change the size of the file
                            elif action == 'edit':
                                file_data = get_files(drive_id, service, name=activity["file_name"])
                                for _ in file_data:
                                    connection.execute_query(f'update files set size = {_["size"]} where drive_id = "{_["id"]}" ')
                        
                        except Exception as e:
                            print("Exception action data update :",e)

            else:
                print("Recent Activities already checked...")
                checked = 0

        #update the lastActivityCheckedTime to now()  
        if checked:
            date_string = date_now(True, False)
            print("updating lastactivity check : ", date_string)
            connection.execute_query(f'update folder set lastActivityCheckTime = "{date_string}" where folder_id = {folder_id} ')

            # update the table wether the folder data was updated or not
            connection.execute_query(f'update folder set updated = {activity_updated} where folder_id = {folder_id} ')
    
    except Exception as e:
        print("Exception while activity check....", e)
    finally:
        user.service = service
        print("deleting the folder_id from activity flag.....")
        del activity_flag.folder_id[activity_flag.folder_id.index(drive_id)]
        return activity_updated
        
# Searching the files for each folder
def search_folder_files(folders, user, **kwargs):
    response_data = {}
    error = ''
    data_item = 1
    response_filter_data = []

    if kwargs.get('category'):
        for x in kwargs['category']:
            response_filter_data.append(
                connection.dict_query(f'select category, definition from category where category = "{x}" ')[0]
            )
    
    elif kwargs.get('criteria'):
        category_ = set()
        for x in kwargs['criteria']:
            desc = connection.execute_query(f'select criteria_id,definition from criteria where criteria_number = "{x}" ')[0]
            resp = {'criteria' : x, 'definition' : desc[1], 'category' : []}
            # adding the categories of the criteria
            criteria_category = connection.execute_query(f'select category, definition from criteria_category join category on criteria_category.category_id = category.category_id where criteria_id = "{desc[0]}" ')
            for category in criteria_category:
                category_.add(category[0])
                resp['category'].append({'category' :category[0], 'def' : category[1]})
            kwargs['category'] = list(category_)
            response_filter_data.append(resp)

    else:
        return None

    folder_data = []
    for folder in folders:
        folder_details = connection.execute_query(f'select folder_id, drive_id, lastActivityCheckTime from folder where folder_name = "{folder}" ')
        folder_data.append({
            'folder': folder,
            'folder_id': folder_details[0][0],
            'drive_id': folder_details[0][1],
            'last_check_time': folder_details[0][2]
        })

    print("Category : ", kwargs.get('category'))
    print("Folder data : ", folder_data)
    
    data_item_list = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(folders)) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {
            executor.submit(filter_files,
                            folder_id = x['folder_id'], category = kwargs.get('category'), year = kwargs.get('year'), month = kwargs.get('month')
                            ) : x['folder'] for x in folder_data}

        for future in concurrent.futures.as_completed(future_to_url):
            folder_name = future_to_url[future]
            print("searched files for folder : ", folder_name)
            try:
                data = future.result()
                file_data = data
                # print("Total files found for folder : ", folder_name , " : ", len(file_data))
                print(file_data)
                if file_data:
                    for x in file_data.keys():
                        for y in file_data[x]:
                            print(y)
                            y["data_item"] = data_item
                            data_item_list[data_item] = y["drive_id"]
                            data_item += 1
                            del y["drive_id"]

                    for x in kwargs['category']:
                        if response_data.get(x):
                            response_data[x].extend(file_data.get(x))
                        else:
                            response_data[x] = file_data.get(x)
                else:
                    error += f'No files for folder : {folder_name}'

            except Exception as e:
                print("Exception at folder search for... ",folder," ", e)
                error += f'Error while seraching for files in folder : {folder_name}'

    # returns the list of all the files
    if not error:
        error = None
    return {'data':response_data,'filter_data': response_filter_data, 'error' : error, 'data_item' :data_item_list}

# start and end dates for the academic year
def academic_year_dates(start_year, start_month):
    # Start of academic year
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(start_year+1, start_month, 1) - timedelta(days=1)
    return start_date, end_date

# filter file data based on the criterias
def filter_files(folder_id, **kwargs):
    try:
        categories = kwargs['category']
        start_date, end_date = academic_year_dates(kwargs['year'], kwargs['month'])
        print(start_date, end_date)
        print("Academic start and end_date :",start_date, end_date)
    except Exception as e:
        print("All filters are not present ...")
        return None
    
    files_data = connection.dict_query(f'select * from files where folder_id = {folder_id}')
    print("Total Fies in folder : ", len(files_data))

    iconLinks_ = connection.execute_query('select mimeType_id, iconLink from mimeType')
    iconLinks = {}
    for _ in iconLinks_:
        iconLinks[_[0]] = _[1]

    response = {}
    for x in categories:
        response[x] = []
    remove_index = []
    
    try:
        # filter the files based on the filters... ofc
        for file in files_data:
            try:
                # check if the file lies in the given academic year or not
                createdTime = file['creationTime']
                createdTime = datetime.strptime(createdTime, "%Y-%m-%d")

                # check if between the academic year
                if createdTime < start_date or createdTime > end_date:
                    remove_index.append( files_data.index(file) )

                else:
                    # check if it contains the category
                    file_cat = connection.execute_query(f'''
                        select category from file_category 
                        join category 
                        on file_category.category_id = category.category_id
                        where file_id = {file["file_id"]}
                        ''')
                    if file_cat:
                        # check if category present in the file or not
                        flag = 0
                        for x in file_cat:
                            if x[0] in categories:
                                flag = 1
                                try:
                                    file["creationTime"] = f'{createdTime.strftime("%B")}, {createdTime.year}'
                                except: 
                                    pass
                                file_owner = file["owner_email"][:file['owner_email'].find('@')].replace('.',' ')

                                response[x[0]].append({
                                    "data_item": 0,
                                    "drive_id": file["drive_id"],
                                    "name" : file["file_name"],
                                    "time" : file["creationTime"],
                                    "size" : convert_bytes(file["size"]),
                                    "icon" : iconLinks[int(file["mimeType_id"])] if iconLinks[int(file["mimeType_id"])] else "/static?file_name=file-regular-24.png",
                                    "email" : file_owner,
                                    "link" : file["driveLink"] 
                                })
                            
                        if flag == 0:
                            remove_index.append( files_data.index(file) )
                    else:
                        remove_index.append( files_data.index(file) )
            except Exception as e:
                print("Exception while filtering for file...", file, e)
                return None

        return response

    except Exception as e:
        print("Exception while filtering the files for the folder...", e)
        return None


def check_files_integrity(folder_id, insights):
    folder_category = connection.execute_query(f'select category from category_folder join category on category.category_id = category_folder.category_id where folder_id = {folder_id} ')
    # getting the categories for the folder
    if folder_category:
        folder_category = [x[0] for x in folder_category]
        print(folder_category)
    else:
        folder_category = []
        insights.error.add('No Categories Assigned to the folder')

    # getting all the files for the folder
    folder_files = connection.dict_query(f'select file_id,file_name from files where folder_id = {folder_id}')

    # getting all the ignored files for the folder
    ignored_files = connection.execute_query(f'select file_id from ignored_files where folder_id = {folder_id}')
    ignored_files = [x[0] for x in ignored_files]

    iconLinks_ = connection.execute_query('select mimeType_id, iconLink from mimeType')
    iconLinks = {}
    for _ in iconLinks_:
        iconLinks[_[0]] = _[1]

    if folder_files:
        for file in folder_files:
            get_data = 0
            file_name = file['file_name'] 
            file_id = file['file_id']

            # if the file is not ignored then continue with all the checks
            if file_id in ignored_files:
                reason = connection.execute_query(f'select reason from ignored_files where file_id = {file_id}')[0][0]
                insights.ignored_files.append({
                    'id' : file_id,
                    'reason' : reason
                })
                get_data = 1

            else:
                try:
                    name_format = get_file_name_data(file_name)
                    creationTime = name_format[0]
                    categories = name_format[1]
                    # checks for creation time
                    flag = 0
                    try:
                        if len(creationTime) == 8 and creationTime.isdigit():
                            date_object = datetime(int(creationTime[:4]), int(creationTime[4:6]), int(creationTime[6:8]))
                            if date_object > date_now():
                                flag =1
                        else: flag = 1
                    except ValueError as e:
                        flag = 1
                    if flag == 1:
                        insights.wrong_file_format.append({
                            'id' : file_id,
                            'reason' : 'Incorrect Date Format'
                        })
                        get_data = 1
                    
                    # checks for category
                    if not categories:
                        connection.execute_query(f'delete from file_category where file_id = {file["file_id"]}')
                        insights.wrong_file_format.append({
                            'id' : file_id,
                            'reason' : 'Category Code not present'
                        })
                        get_data = 1

                    else:
                        file_category = connection.execute_query(f'select category from file_category join category on category.category_id = file_category.category_id where file_id = {file["file_id"]} ')
                        if file_category:
                            file_category = [x[0] for x in file_category]
                        else:
                            file_category = []

                        categories = categories.split(',')
                        for cat in categories:
                            if cat:
                                if cat not in file_category:
                                    cat_id = connection.execute_query(f'select category_id from category where category = "{cat}" ')
                                    if not cat_id and (len(cat) <=5 and len(cat) >= 3):
                                        insights.new_category.append({
                                            'id' : file_id,
                                            'category' : cat
                                        })
                                        get_data = 1
                                    else:
                                        connection.execute_query(f'insert into file_category values({file["file_id"]}, {cat_id[0][0]})')

                                if cat not in folder_category and cat not in insights.new_category and (len(cat) <=5 and len(cat) >= 3):
                                    if insights.missing_category.get(cat):
                                        insights.missing_category[cat] += 1
                                    else:
                                        insights.missing_category[cat] = 1

                except Exception as e:
                    print(f"Exception wile checking file integrity....{e} for {file_name}")
            
            # get and store the details of the file in the file_data using id
            if get_data:
                file_data = connection.dict_query(f'select * from files where file_id = {file_id}')
                if file_data:
                    file_data = file_data[0]
                    file_owner = file_data["owner_email"][:file_data['owner_email'].find('@')].replace('.',' ')
                    file_data = {
                                "drive_id": file_data['drive_id'],
                                "name" : file_name,
                                "time" : file_data["creationTime"],
                                "size" : convert_bytes(file_data["size"]),
                                "icon" :  iconLinks[int(file_data["mimeType_id"])] if iconLinks[int(file_data["mimeType_id"])] else "/static?file_name=file-regular-24.png",
                                "email" : file_owner,
                                "link" : file_data["driveLink"] 
                            }
                insights.file_data[file_id] = file_data
    
    else:
        insights.error.add('Folder not scanned for files')


def get_insights(folders):
    insights = {}
    folder_data = []
    for folder in folders:
        folder_details = connection.execute_query(f'select folder_id, drive_id from folder where folder_name = "{folder}" ')
        folder_data.append({
            'folder': folder,
            'folder_id': folder_details[0][0],
            'drive_id': folder_details[0][1],
        })
        insights[folder] = Insights()

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(folders)) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = {executor.submit(check_files_integrity, x['folder_id'], insights[x['folder']]): x['folder'] for x in folder_data}

        for future in concurrent.futures.as_completed(future_to_url):
            folder_name = future_to_url[future]
            print("Folder : ", folder)
            try:
                data = future.result()
                insights[folder_name].remove_duplicate()

                print('File data : ',len(insights[folder_name].file_data))
                print('Category data : ',len(insights[folder_name].new_category))
                print('Category data : ',len(insights[folder_name].missing_category))

                if not insights[folder_name].wrong_file_format and not insights[folder_name].new_category and not insights[folder_name].file_data and not insights[folder_name].ignored_files and not insights[folder_name].error and not insights[folder_name].missing_category:
                    print('No insights...')
                    insights[folder_name] = 1

            except Exception as exc:
                print("Exception while Insights call...", exc)
                insights[folder_name] = None
    
    return insights
           