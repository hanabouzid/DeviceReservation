from __future__ import print_function
import json
import sys
from adapt.intent import IntentBuilder
from adapt.engine import IntentDeterminationEngine
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.messagebus.message import Message
from mycroft.util.parse import extract_datetime
from datetime import datetime, timedelta
import httplib2
from googleapiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools

import string
import pytz
#in the raspberry we add __main__.py for the authorization
UTC_TZ = u'+00:00'
FLOW = OAuth2WebServerFlow(
    client_id='73558912455-smu6u0uha6c2t56n2sigrp76imm2p35j.apps.googleusercontent.com',
    client_secret='0X_IKOiJbLIU_E5gN3NefNns',
    scope=['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/contacts.readonly'],
    user_agent='Smart assistant box')
# TODO: Change "Template" to a unique name for your skill
class DeviceReservationSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(DeviceReservationSkill, self).__init__(name="DeviceReservationSkill")

    @property
    def utc_offset(self):
        return timedelta(seconds=self.location['timezone']['offset'] / 1000)

    def recherche(self,list1,list2,l):
        for i in range(len(list1)):
            if list1[i] == l:
                mail = list2[i]
        return mail

    def freebusy(self, mail, datestart, datend, service):
        body = {
            "timeMin": datestart,
            "timeMax": datend,
            "timeZone": 'America/Los_Angeles',
            "items": [{"id": mail}]
        }
        eventsResult = service.freebusy().query(body=body).execute()
        cal_dict = eventsResult[u'calendars']
        print(cal_dict)
        for cal_name in cal_dict:
            print(cal_name, ':', cal_dict[cal_name])
            statut = cal_dict[cal_name]
            for i in statut:
                if (i == 'busy' and statut[i] == []):
                    return True

                    # ajouter l'email de x ala liste des attendee
                elif (i == 'busy' and statut[i] != []):
                    return False

    @intent_handler(IntentBuilder("add_device_intent").require('Add').require('device').optionally('time').build())
    def handle_device(self, message):
        storage1 = Storage('/opt/mycroft/skills/devicereservation.hanabouzid/info.dat')
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
        results = people_service.people().connections().list(resourceName='people/me', pageSize=100,
                                                             personFields='names,emailAddresses',
                                                             fields='connections,totalItems,nextSyncToken').execute()
        connections = results.get('connections', [])
        print("authorized")
        listdiv=[]
        utt = message.data.get("utterance", None)
        liste1 = utt.split(" a ")
        liste2=liste1[1].split(" for ")
        if ("and") in liste2[0]:
            listdiv = liste2[0].split(" and ")
        else:
            listdiv.append(liste2[0])
        print(listdiv)
        date1 = liste2[1]
        st = extract_datetime(date1)
        st = st[0] - self.utc_offset
        datestart = st.strftime('%Y-%m-%dT%H:%M:00')
        datestart += UTC_TZ
        print(datestart)
        date2=self.get_response('when will you return the device?')
        et = extract_datetime(date2)
        et = et[0] - self.utc_offset
        dater = et.strftime('%Y-%m-%dT%H:%M:00')
        dater += UTC_TZ
        print(dater)

        nameListe = []
        adsmails = []
        # attendee est la liste des invités qui sont disponibles
        attendees = []

        for person in connections:
            emails = person.get('emailAddresses', [])
            names = person.get('names', [])
            adsmails.append(emails[0].get('value'))
            nameListe.append(names[0].get('displayName'))
        print(nameListe)
        print(adsmails)
        nameEmp=self.get_response('What is your name please?')
        mailEmp=self.recherche(nameListe,adsmails,nameEmp)
        #service.list(customer='my_customer' , orderBy=None, pageToken=None, maxResults=None, query=None)
        #.get(customer=*, calendarResourceId=*)
        listD=['pcfocus']
        listDmails=['c_1882n3ruihk0qj7nnpqdpqhl5h4um4glcpnm6tbj5lhmusjgdtp62t39dtn2sorfdk@resource.calendar.google.com']
        freeDevices=[]
        freemails=[]
        for i in range(len(listDmails)):
            x=self.freebusy(i,datestart,dater,service)
            if x==True:
                freeDevices.append(listD[i])
                freemails.append(listDmails[i])
        print(freemails)
        print(freeDevices)

        s = ",".join(freeDevices)
        print( 'free devices'+ s)
        for device in listdiv:
            l=[]
            for i in freeDevices:
                print(i)
                if device in i.lower():
                    l.append(i)
                    print(l)
            if l != []:
                self.speak_dialog('free', data={"device": device, "s": s})
                choice = self.get_response('what is your choice?')
                email = self.recherche(freeDevices, freemails, choice)
                attendees.append({'email': email})
                summary = choice + "reservation for Mr/Ms" + nameEmp
                description = "Mr/Ms" + nameEmp + "'s email:" + mailEmp
                reservation = {
                    'summary': summary,
                    'description': description,
                    'location': 'Focus corporation',
                    'start': {
                        'dateTime': datestart,
                        'timeZone': 'America/Los_Angeles',
                    },
                    'end': {
                        'dateTime': dater,
                        'timeZone': 'America/Los_Angeles',
                    },
                    'recurrence': [
                        'RRULE:FREQ=DAILY;COUNT=1'
                    ],
                    'attendees': attendees,
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 10},
                        ],
                    },
                }
                reservation = service.events().insert(calendarId='primary', sendNotifications=True,
                                                      body=reservation).execute()
                print('Event created: %s' % (reservation.get('htmlLink')))
                self.speak_dialog('deviceReserved', data={"device": device})
            else:
                self.speak_dialog('busy', data={"device": device})

def create_skill():
    return DeviceReservationSkill()
