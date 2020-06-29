from __future__ import print_function
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
FLOW = OAuth2WebServerFlow(
    client_id='73558912455-smu6u0uha6c2t56n2sigrp76imm2p35j.apps.googleusercontent.com',
    client_secret='0X_IKOiJbLIU_E5gN3NefNns',
    scope=['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/contacts.readonly'],
    user_agent='Smart assistant box')
storage1 = Storage('/opt/mycroft/skills/devicereservationskill.hanabouzid/info.dat')
credentials = storage1.get()
if credentials is None or credentials.invalid == True:
  credentials = tools.run_flow(FLOW, storage1)
print(credentials)
# Create an httplib2.Http object to handle our HTTP requests and
# authorize it with our good Credentials.
http = httplib2.Http()
http = credentials.authorize(http)
service = build('calendar', 'v3', http=http)
people_service = build(serviceName='people', version='v1', http=http)
print("authorized")