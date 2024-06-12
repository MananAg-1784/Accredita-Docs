
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

action_cases = ['CREATE', 'MOVE', 'EDIT', 'DELETE', 'RENAME', 'RESTORE']

# Returns the name of a set property in an object, or else None.
def getOneOf(obj):
  for key in obj:
    return key
  return None

def getUserInfo(actors, user_id, peoples_service = None):
  # Returns user information, or the type of user if not a known user
  for actor in actors:  
    if actor.get('user'):
      user_ = actor['user']
      if user_.get("knownUser"):
        knownUser = user_["knownUser"]["personName"]
        return knownUser
  return None

# Returns the type of a target and an associated title.
def getTargetInfo(targets):
  for target in targets:
    if target.get("driveItem"):
      file_name = target["driveItem"].get("title", None)
      file_id = target["driveItem"].get("name", None)
      return file_name, file_id.replace('items/', '')
  return None

def formated_activity_data(activities, user_id):
  formated_activity = []
  for activity in activities:
    # get the primary - main action
    try:
      print(activity)
      action = getOneOf(activity["primaryActionDetail"]).lower()
      if action.upper() in action_cases:
        # get the timestamp
        timestamp = None
        if activity.get("timestamp"):
          timestamp = activity["timestamp"]
        elif activity.get("timeRange"):
          timestamp = activity["timeRange"]["endTime"]

        # user email id for the action
        account_id = getUserInfo(activity["actors"], user_id)
        
        # get the details about the file
        file_name, file_id = getTargetInfo(activity["targets"])

        # get the required details based on the type of action_case
        # Create - copy, upload, new
        # Edit / Delete / Restore
        # Move - addedParent, removedParents
        # Rename - oldTitle, NewTitle

        action_details = None
        try:
          action_details = activity['primaryActionDetail'].get(action)    
        except:
          pass

        formated_activity.append({
          "action" : action,
          "action_details" : action_details,
          "timestamp": timestamp,
          "account_id" : account_id,
          "file_name" : file_name,
          "file_id" : file_id
        })
      else:
        print("Action not of any need...", action)

    except Exception as e:
        print("Exception in formating activity :",e)
  print("Formatted activities...")
  return formated_activity

def get_activity(creds, user_id, folder_id, **kwargs):
    print(kwargs)
    service = build('driveactivity', 'v2', credentials=creds)
    if service:

      # Call the Drive Activity API
      page_token = None
      filter_ = {"ancestorName": f"items/{folder_id}", "filter" : ""}

      # time in milliseconds since the epoch => 1 Jan, 1970
      if kwargs.get('after_time'):
          filter_['filter'] += f'time >= {kwargs.get("after_time")} '
      elif kwargs.get('befor_time'):
          filter_['filter'] += f'time <= {kwargs.get("before_time")} '

      if kwargs.get('action_case'):
          action_case = ""
          if len(kwargs.get('action_case')) == 1:
              action_case = kwargs.get('action_case')[0]
          else:
            action_case = "("
            for _ in kwargs.get('action_case'):
              action_case += _ + " "
            action_case += ")"
          filter_["filter"] += f"detail.action_detail_case: {action_case} "

      if kwargs.get('page_size'):
        filter_['pageSize'] = kwargs['page_size']

      print(filter_)

      try:
        # "filter": "time >= \"2023-03-01T00:00:00-05:00\" detail.action_detail_case:(MOVE RENAME CREATE EDIT DELETE RESTORE) "
        results = service.activity().query(
            body=filter_).execute()
        activities = results.get("activities", [])

        if not activities:
          return None
        else:
          print("Recent activity : ", len(activities))
          return formated_activity_data(activities, user_id)     

      except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    else:
      return None
