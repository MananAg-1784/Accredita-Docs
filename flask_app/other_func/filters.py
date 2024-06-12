
from flask_app.database import connection
from json import dumps
from flask_app.other_func.global_variables import users

def dept_category_list(dept_id):
    categories = connection.dict_query('select category_id,category, definition from category')
    folders = connection.dict_query(f'select folder_id, folder_name from folder where dept_id = {dept_id}')
    dept_folder = {}
    for x in folders:
        dept_folder[x['folder_id']] = x['folder_name']
    category_list = []
    for category in categories:
        category_folder = connection.execute_query(f'select folder_id from category_folder where category_id = {category["category_id"]}')
        folders = []
        for _ in category_folder:
            if dept_folder.get(_[0]):
                folders.append(dept_folder[_[0]])
        category_list.append({
            'category': category['category'],
            'definition':category['definition'],
            'folders': folders
        })

    return category_list


def get_category_data(folder_id):
    '''
    folder_cat : Get all the categories for the folder_id
    available_cat : get all the categories available
    return => [{name, definition}]
    '''
    dept_id = connection.execute_query(f'select dept_id from folder where folder_id = {folder_id}')[0][0]
    
    categories = connection.dict_query('select category_id,category,definition from category')

    folder_cat_id = connection.execute_query(f'select category_id from category_folder where folder_id = {folder_id}')
    folder_cat_id = [ x[0] for x in folder_cat_id ]

    folder_cat = []
    available_cat =[]
    for category in categories:
        if category['category_id'] in folder_cat_id:
            del category['category_id']
            folder_cat.append(category)
        else:
            del category['category_id']
            available_cat.append(category)

    return folder_cat, available_cat


def process_categories(file_data, dept_id, fields):
    # Check which categories are not present in the database
    # create new category if definition is present
    # add categories to the folder
    try :
        categories_ = connection.execute_query('select category_id,category from category')
        categories = {}
        for x in categories_:
            categories[x[1]] = x[0]
        folders_ = connection.execute_query(f'select folder_id, folder_name from folder where dept_id = {dept_id} ')
        folders ={}
        for x in folders_:
            folders[x[1]] = x[0]
        
        response = {'error' : '', 'rejected_folders' : [], 'rejected_category' : [], 'new_cat' :0}
        for x in file_data:
            folders_ = []
            if x[fields['folder']]:
                folders_ = [ f.strip() for f in x[fields['folder']].split(',') if f.strip() ]
            category = x[fields['category']].upper()

            try:
                # if category is not present create new category
                if not categories.get(category):
                    if x[fields['definition']]:
                        connection.execute_query(f'insert into category(category, definition) values("{category}","{x[fields["definition"]]}")')
                        response['new_cat'] += 1
                        cat_id = connection.execute_query(f'select category_id from category where category = "{category}" ')[0][0]
                        categories[category] =  cat_id
                    else:
                        response['rejected_category'].append(category)

                if categories.get(category):
                    folders_present = connection.execute_query(f'select folder_id from category_folder where category_id = {categories[category]} ')
                    folders_present = [ i[0] for i in folders_present ]

                    for folder in folders_:
                        if folder not in response['rejected_folders']:
                            folder_id = folders.get(folder)
                            if folder_id and folder_id not in folders_present:
                                connection.execute_query(f'insert into category_folder values({categories[category]},{folder_id})')
                            elif not folder_id:
                                response['rejected_folders'].append(folder)

            except Exception as e:
                print("Error while updating for category : ", category, "  ", e)
                response['error'] += "\nError while updating for category : "+ category

        html_data = f'''
            <div style="color: red !important;">{response['error']}</div>
            <div>Total New Category Created are : {response['new_cat']}</div>
        '''
        if response['rejected_category']:
            html_data += "<div> Definition not mentioned for : "
            for i in response['rejected_category']:
                html_data += f"<span style='padding: 0px 5px;'>{i}</span>"
            html_data += "</div>"

        if response['rejected_folders']:
            html_data += "<div> Folder is not present (Add these Folders): "
            for i in response['rejected_folders']:
                html_data += f"<span style='padding: 0px 5px;'>{i}</span>"
            html_data += "</div>"

        return html_data
    except Exception as e:
        print("Error while processing the file .. ", e)
        return None


def get_criteria_data(acc_id):
    print("Accredition id : ", acc_id)
    try:
        criterias = connection.dict_query(f'select criteria_id, criteria_number, definition from criteria where accredition_id = {acc_id}')

        categories_ = connection.dict_query(f'select category_id, category from category')
        categories = {}
        for _ in categories_:
            categories[ _['category_id'] ] = _['category']

        response = []
        for criteria in criterias:
            data = {'criteria' : criteria["criteria_number"], 'definition' : criteria["definition"], 'category' : []}
            criteria_category = connection.execute_query(f'select category_id from criteria_category where criteria_id = {criteria["criteria_id"]}')

            for x in criteria_category:
                category = categories.get(x[0])
                if category:
                    data['category'].append(category)
                else:
                    connection.execute_query(f'delete from criteria_category where category_id = {x} and criteria_id = {criteria["criteria_id"]} ')
            
            response.append(data)
        return response
    except Exception as e:
        print("Exception while getting criteria_data...", e)
        return []


def process_criteria(file_data, dept_id, fields, acc):
    # Check which criterias are not present in the database
    # create new criteria if definition is present
    # add criterias to the folder
    try :
        print("Processing criteria file....")

        acc_id = connection.execute_query(f'select id from accreditions where accredition = "{acc}" ')
        if acc_id:
            acc_id = acc_id[0][0]
        else:
            raise Exception('Accredition no present')

        criterias_ = connection.execute_query(f'select criteria_id,criteria_number from criteria where accredition_id = {acc_id} ')
        criterias = {}
        for x in criterias_:
            criterias[x[1]] = x[0]
        
        categories_ = connection.execute_query('select category_id,category from category')
        categories = {}
        for x in categories_:
            categories[x[1]] = x[0]
        
        response = {'error' : '', 'rejected_criteria' : [], 'rejected_category' : [], 'new_criterias' :0}
        for x in file_data:
            category_ = []
            if x[fields['category']]:
                category_ = [ f.strip() for f in x[fields['category']].split(',') if f.strip() ]
            criteria = x[fields['criteria']]

            try:
                flag =1
                # Validate criteria number / code
                try:
                    float(criteria.replace('.',''))
                except:
                    response['rejected_criteria'].append(criteria)
                    flag = 0
                    
                if flag:
                    # If criteria is already present
                    if criterias.get(criteria):
                        pass
                    else:
                        if x[fields['definition']]:
                            connection.execute_query(f'insert into criteria(criteria_number,definition,accredition_id) values("{criteria}","{x[fields["definition"]]}",{acc_id})')

                            criteria_id = connection.execute_query(f'select criteria_id from criteria where criteria_number = "{criteria}" ')[0][0]
                            response['new_criterias'] += 1
                            criterias[criteria] = criteria_id
                        else:
                            response['rejected_criteria'].append(criteria)
                        
                    # adding categories to the criteria
                    if category_ and criterias[criteria]:
                        for category in category_:
                            if categories.get(category):
                                flag = connection.execute_query(f'select criteria_id from criteria_category where criteria_id = {criterias[criteria]} and category_id = {categories[category]} ')
                                if not flag:
                                    connection.execute_query(f'insert into criteria_category values({criterias[criteria]},{categories[category]})')
                            else:
                                response['rejected_category'].append(category)
                    else:
                        response['rejected_criteria'].append(criteria)

            except Exception as e:
                print("Error while updating for criteria : ", criteria, "  ", e)
                response['error'] += "\nError while updating for criteria : "+ criteria

        html_data = f'''
            <div style="color:red !important;">{response['error']}</div>
            <div>Total New Criterias Created are : {response['new_criterias']}</div>
        '''
        if response['rejected_criteria']:
            html_data += "<div>Definition not mentioned for : "
            for i in response['rejected_criteria']:
                html_data += f"<span style='padding: 0px 5px;'>{i}</span>"
            html_data += "</div>"

        if response['rejected_category']:
            html_data += "<div>Category not present (Add these category) : "
            for i in response['rejected_category']:
                html_data += f"<span style='padding: 0px 5px;'>{i}</span>"
            html_data += "</div>"


        return html_data
    except Exception as e:
        print("Error while processing the file .. ", e)
        return None


def process_file(*args, **kwargs):
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
                    error = f"Field not Present... {fields_not_present}"
                    raise Exception(f'Fields not present.. {fields_not_present}')
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
            <div>Total Files rows : {c-1}</div>
            {html_data}
        '''
        socketio.emit('processed_file_data', dumps({'data' : file_data}), namespace = '/update' )

    except Exception as e:
        print("Error while Processing the excel file :", e)
        socketio.emit('processed_file_data', dumps({'error' : error}), namespace = '/update')
    user.file = None


# remove all the data for the particular folder
def remove_folder_data(folder_id):
    connection.execute_query(f'delete from upload_activity where folder_id = {folder_id}')
    connection.execute_query(f'delete from trashed where folder_id = {folder_id}')
    connection.execute_query(f'delete from folder where folder_id = {folder_id} ')
    connection.execute_query(f'delete from category_folder where folder_id = {folder_id}')
    connection.execute_query(f'delete from ignored_files where folder_id = {folder_id}')

    files_id = connection.execute_query(f'select file_id from files where folder_id = {folder_id}')

    for file_id in files_id:
        file_id = file_id[0]        
        connection.execute_query(f'delete from file_category where file_id = {file_id}')
    connection.execute_query(f'delete from files where folder_id = {folder_id}')

# remove all the data for a category
def remove_category_data(category_id):
    connection.execute_query(f'delete from category where category_id = {category_id}')
    connection.execute_query(f'delete from file_category where category_id = {category_id}')
    connection.execute_query(f'delete from category_folder where category_id = {category_id}')
    connection.execute_query(f'delete from criteria_category where category_id = {category_id}')

