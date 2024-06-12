
from flask import Blueprint, abort
error_handler = Blueprint('error_handling', __name__)

@error_handler.app_errorhandler(404)
def not_found(e):
    return '''
        Page Not Found 
        <br> 
        Return to Home Page
        <a href="/profile">
            Profile
        </a>'''

@error_handler.app_errorhandler(400)
def not_found(e):
    return '''
        Bad Request
        <br> 
        Please 
        <a href='/login'> 
            Login or Register 
        </a>'''

@error_handler.app_errorhandler(401)
def not_found(e):
    return '''
        Access Unauthorised 
        <br> 
        Contact the Admin 
        <br> 
        <a href="/profile"> 
            Go to Profile
        </a>
        '''

@error_handler.app_errorhandler(403)
def not_found(e):
    return '''
        Access Denied 
        <br> 
        Please 
        <a href='/login'> 
            Login or Register 
        </a>'''

@error_handler.app_errorhandler(500)
def server_error(e):
    return "Server Error <br> Retry after some time ..."
