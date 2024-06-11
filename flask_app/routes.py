
from flask import Blueprint, request, url_for, render_template, current_app, redirect, flash, abort
from datetime import timedelta

from flask_app.database import connection
from flask_app.drive_func.google_drive import Create_Service, get_creds

from flask_app.other_func.global_variables import users, flow, accreditions, User, date_now
from flask_app.other_func.authentication import user_login, login_required
from flask_app.other_func.enc_dec import encrypt_fernet, decrypt_fernet
from flask_app.other_func.filters import dept_category_list

from flask_app.logger import logger

main = Blueprint('main', __name__)

@main.before_request
def before_request_func():
    logger.info(
        "URL : %s | method : %s",
        request.path,
        request.method
    )

@main.route('/')
def home_page():
    user_id = request.cookies.get('user_id')
    if user_id is not None:
        return redirect('/profile')
    else:
        logger.info('New User has visted the site')
    return render_template('home.html')

@main.route('/login')
def login():
    authorization_url, state = flow.authorization_url(access_type='offline',prompt = 'select_account')
    # prompt='consent'
    return redirect(authorization_url)

@main.route('/register')
def register():
    authorization_url, state = flow.authorization_url(access_type='offline',prompt = 'consent')
    # prompt='consent'
    return redirect(authorization_url)

@main.route('/callback')
@user_login
def callback(user_id, email):
    logger.info(f"Logged in new user >> {email}")
    if not users.get(user_id):
        users[user_id] = User(id= user_id)
    else:
        pass

    # making the user_id cookie 
    expire_date = date_now(onlyDate=False)
    expire_date = expire_date + timedelta(days=365)

    response = redirect('/profile')
    cookie_id = encrypt_fernet(data = user_id, key = current_app.config['SECRET_KEY']).decode()
    response.set_cookie('user_id', cookie_id, expires= expire_date)
    return response


@main.route('/logout')
@login_required('Logout')
def logout(user, **kwags):
    email = connection.execute_query(f"select email from user where user_id = '{user.id}' ")[0][0]
    logger.info(f"Log-out user >> {email}")

    users.pop(user.id)
    response = redirect('/')
    response.set_cookie('user_id', '', expires=0)
    return response


@main.route('/profile')
@login_required('Profile')
def user_profile(user,**kwargs):
    data = connection.execute_query('select dept_name from department')
    depts = []
    for _ in data:
        depts.append(_[0])
    return render_template('profile.html', user = user, depts=depts, **kwargs)


@main.route('/search')
@login_required('Search')
def search_files(user, **kwargs):
    dept_id = connection.execute_query(f'select dept_id from department where dept_name = "{user.dept}" ')[0][0]
    folders = connection.dict_query(f'select folder_name as folder, accredition from folder where dept_id = {dept_id}') 
    return render_template('search.html', user = user, **kwargs, folders= folders, accreditions =accreditions)


@main.route('/upload')
@login_required('Upload')
def upload_files(user, **kwargs):
    _ = connection.dict_query('select * from mimeType')
    mimeTypes = {}
    for x in _:
        mimeTypes[x['mimeType']] = x['iconLink']

    data = {}
    dept_id = user.dept
    dept_id = connection.execute_query(f'select dept_id from department where dept_name ="{dept_id}" ')
    if dept_id:
        dept_id = dept_id[0][0]
        data['category'] = dept_category_list(dept_id)
        d_ = connection.execute_query(f'select folder_name from folder where dept_id = {dept_id}')
        data['folder'] = [ x[0] for x in d_ ]

    return render_template('upload.html', user = user,mimeType = mimeTypes,categories = data['category'], folders = data['folder'], **kwargs)

@main.route('/update')
@login_required('Update')
def update_(user, **kwargs):
    data_dict = {}
    data_dict['folders'] = connection.dict_query(f'select folder_name, accredition from folder where dept_id = (select dept_id from department where dept_name = "{user.dept}" )')
    data_dict['categories'] = connection.dict_query('select category,definition from category')
    data_dict['accredition'] = accreditions
    return render_template('update.html', user = user, data_dict = data_dict, **kwargs)

@main.route('/admin')
@login_required('Profile')
def admin_page(user, **kwargs):
    user_email = connection.execute_query(f'select email from user where user_id = "{user.id}" ')[0][0]
    admin_email = connection.execute_query('select admin_email from setup')[0][0]
    if user_email == admin_email:
        depts = connection.execute_query(f'select dept_name, dept_id, owner from department')
        dept_data = []
        for dept in depts:
            users = connection.execute_query(f'select email from user where dept_id = {dept[1]}')
            users = [x[0] for x in users]
            dept_data.append({
                'name': dept[0],
                'owner': dept[2],
                'id':dept[1],
                'users': users 
            })
        return render_template('admin.html',dept = dept_data,acc = accreditions, user = user, **kwargs)
    else:
        abort(404)

@main.route('/add_acc', methods=['POST'])
def admin_page_actions():
    print(request.form)
    try:
        acc = request.form.get('acc')
        if acc and acc not in accreditions:
            connection.execute_query(f'insert into accreditions(accredition)values("{acc}") ')
            accreditions.append(acc)
            flash("Accredition Added")
        else:
            flash("No Accredition Mentioned")
    except Exception as e:
        print("Add accreditions : ", repr(e))
        flash("Error, Try Again")

    return redirect('/admin')

@main.route('/add_dept', methods=['POST'])
def _admin_page_actions():
    print(request.form)
    try:
        dept = request.form.get('dept')
        if dept:
            depts = connection.execute_query('select dept_name from department')
            depts = [x[0] for x in depts]
            connection.execute_query(f'insert into department(dept_name)values("{dept}") ')
            flash("New Department Added")
        else:
            flash("No Department Mentioned")
    except Exception as e:
        print("Add department : ", repr(e))
        flash("Error, Try Again")

    return redirect('/admin')
