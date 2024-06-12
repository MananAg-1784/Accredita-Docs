# google modules for creating service
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from functools import wraps
from json import loads, dumps
from flask import request, abort, url_for, redirect, current_app
import uuid

# flask_app modules
from flask_app.other_func.global_variables import User, flow, users, priv, OAuthVariable
from flask_app.other_func.enc_dec import encrypt_fernet, decrypt_fernet
from flask_app.drive_func.google_drive import get_creds
from flask_app.database import connection

from flask_app.logger import logger

def allowed_routes(privilage, request_url):
    priv = {'admin': ['Search', 'Upload', 'Update'], 'viewer' : ['Search'], 'editor' : ['Search', 'Upload']}
    try:
        route = priv.get(privilage,[])
        route.extend(['Profile','Logout'])
        if not privilage and request_url not in ['Profile', 'Logout']: 
            raise Exception("denied")
        elif privilage:
            if request_url not in route:
                raise Exception("denied")
        else:
            pass
        return route
    except Exception as e:
        logger.warning(f"Access to route : {request_url} -> Denied")
        return None

def user_login(func):
    @wraps(func)
    def get_user_details(*args, **kwargs):
        try:
            token_response = flow.fetch_token(authorization_response=request.url)
            credentials = flow.credentials
            cred_data = credentials.to_json()
            id_info = id_token.verify_oauth2_token(credentials.id_token, Request(), credentials.client_id)

        except Exception as e:
            logger.error(f"Error while OAuth login -> {e}")
            abort(400)

        # Extract user information from the ID Token
        user_name = id_info.get('name', '')
        user_email = id_info.get('email', '')
        logger.info(f"Attempting Authentication of new user >> {user_email}")

        user_id = connection.execute_query(f"select user_id,token,resourceName from user where email = '{user_email}'")
        
        # Domain access regulator
        if not user_email.endswith(OAuthVariable.domain):
           logger.error(f"User email id out of domain req :  {user_email}")
           abort(403)

        #if user does not exists in the database
        if not user_id:
            logger.info("New User -> registering user")
            # checking if the credentials are valid otherwise register again
            try:
                if not credentials or not credentials.valid or not credentials.refresh_token:
                    logger.warning("Credentials not valid")
                    return redirect('/register')

            except Exception as e:
                logger.warning("Credentials not valid")
                return redirect('/register')

            # generate a new user_id
            user_id = str(uuid.uuid4())
            while True:
                if not connection.execute_query(f'select user_id from user where user_id = "{user_id}"'):
                    break
                user_id = str(uuid.uuid4())

            # add the new user to the database
            connection.execute_query(f"insert into user(user_id, email, name, token) values('{user_id}','{user_email}','{user_name}','{cred_data}')")

            service = build('people', 'v1', credentials= get_creds(user_id))
            response = service.people().get(resourceName = "people/me", personFields = "emailAddresses").execute()

            user_account_id = response.get("resourceName")
            if user_account_id:
                connection.execute_query(f"update user set resourceName = '{user_account_id}' where user_id = '{user_id}' ")

        else:
            user = user_id
            user_id = user_id[0][0]

            if not user[0][1]:
                try:
                    if not credentials or not credentials.valid or not credentials.refresh_token:
                        logger.warning("Credentials not valid")
                        return redirect('/register')
                except Exception as e:
                    logger.warning("Credentials not valid")
                    return redirect('/register')
                     
                connection.execute_query(f"update user set token = '{cred_data}' where user_id = '{user_id}' ")

            if not user[0][2]:
                service = build('people', 'v1', credentials= get_creds(user_id))
                response = service.people().get(resourceName = "people/me", personFields = "emailAddresses").execute()

                user_account_id = response.get("resourceName")
                if user_account_id:
                    connection.execute_query(f"update user set resourceName = '{user_account_id}' where user_id = '{user_id}' ")
                    connection.execute_query(f'')

        logger.info(f"User Successfully Logged in : {user_email}")
        return func(user_id = user_id, email = user_email)

    return get_user_details

# Authentication decorator
def login_required( request_url = None ):
    def authenticate_user(func):
        @wraps(func)
        def validate_user_id(**kwargs):
            user_id = request.cookies.get('user_id')
            user_id = decrypt_fernet(user_id, current_app.config['SECRET_KEY'])

            # user_id is wrong cannot be decrypted
            if not user_id:
                logger.warning(f"Broken Cookie Value -> {request.cookies.get('user_id')} ")
                return abort(403)
            
            user_data = connection.execute_query(f"select user_id, email,name,dept_id, privilage from user where user_id = '{user_id}'")
            # the user_id does not exists in the database
            if not user_data:
                logger.warning(f"Broken Cookie Value -> {request.cookies.get('user_id')} ")
                return abort(403)
            
            print("no of users : ", len(users))
            print(users.keys())
            user = users.get(user_id)
            user_data = user_data[0]
            # checking if user data is saved locally or not
            if user:
                pass
            else:
                # User Object not present for the user_id
                users[user_id] = User(user_id)
                user = users[user_id]

            # Checking and creating the User object
            if user_data[3]:
                dept = connection.execute_query(f'select dept_name from department where dept_id = {user_data[3]}')
                user.dept = dept[0][0] if dept else None
                user.privilage = user_data[4] if user_data[4] else None
                if user.privilage and not priv.get(user.privilage):
                    connection.execute_query(f'update user set privilage = "denied" where user_id = "{user_id}" ')
                    user.privilage = 'denied'
                    logger.warning(f"Privialge for the user : {user_data[1]} : DENIED")

            else:
                user.dept = None
                user.privilage = None

            # privilage checking
            route = allowed_routes(user.privilage, request_url)
            if not route:
                abort(401)
            return func(user =user, email = user_data[1], name = user_data[2], routes = route)

        return validate_user_id
    return authenticate_user

# decrypt the user_id and check 
def validate_user_access(func):
    @wraps(func)
    def get_user_data(data_dict):
        response = {'error' : 0, 'response' : '', 'status' : 200}
        try: 
            namespace = request.namespace.replace('/', '')
            user_id = request.cookies.get('user_id')
            user_id = decrypt_fernet(user_id, current_app.config['SECRET_KEY'])
            user = users.get(user_id)
            if not user:
                raise Exception(1)

            access_routes = priv.get(user.privilage, [])
            access_routes.extend(['Profile', 'Logout'])
            access_routes = [x.lower() for x in access_routes]

            if user.privilage != 'admin':
                event_name = request.event['message']
                if namespace == 'profile' and event_name != 'dept_access':
                    raise Exception('Unauthorised Access')

            print(namespace, access_routes)
            if namespace not in access_routes and namespace != 'admin':
                raise Exception('Unauthorised Access')
            else:
                data =  func(data_dict = data_dict, user = user)
                
                if data:
                    
                    if type(data) == str:
                        try: 
                            data = loads(data)
                        except: 
                            response['response'] = data

                    if type(data) == dict:
                        keys = list(data.keys())
                        if 'error' in keys:
                            response['error'] = data.get('error')
                            data.pop('error')

                        keys = list(data.keys())
                        if len(keys) == 1 and 'response' in keys:
                            response['response'] = data.get('response')
                        else:
                            response['response'] = data
                    
                    else:
                        response['response'] = data
                    
                # no data is recieved == None
                else:
                    
                    response['error'] = 1

        except Exception as e:
            print("Exception while validating data access", e)
            if e.args[0] == 1:
                logger.warning("----- Session Expired -----")
                response = {'status' : 400, 'error' : 'Session Expired, Please Reload'}
            else:
                logger.warning("---- Unauthorised access -----")
                response = {'status' : 400, 'error' : 'Unauthorised access, Please Login Again'}
        
        return dumps(response)
    return get_user_data
