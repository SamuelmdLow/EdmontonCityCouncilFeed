import json
import urllib.request
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import pathlib

database = 'database.db'


FIRST_RUN = True
if (pathlib.Path.cwd() / database).exists():
    FIRST_RUN = False

con = sqlite3.connect(database)
cur = con.cursor()

def resetDatabase():
    global con, cur

    cur.execute('''
    CREATE TABLE meetings(
        name text,
        ID text,
        date text,
        url text
    );''')

    cur.execute('''
    CREATE TABLE agendas(
        ID text,
        text text
    );''')

    cur.execute('''
    CREATE TABLE bylaws(
        ID text,
        name text,
        text text
    );''')

    cur.execute('''
    CREATE TABLE motion(
        ID text,
        movedBy text,
        secondedBy text,
        desc text,
        inFavour integer,
        opposed integer,
        result text,
        status integer
    );''')

    cur.execute('''
    CREATE TABLE groups(
        ID integer primary key,
        people text
    );''')

    con.commit()

def uploadMeeting(meeting):
    global con, cur

    if cur.execute("select ID from meetings where ID=?", [meeting.ID, ]).fetchone() != None:

        cur.execute('''
        INSERT INTO meetings
            (name, ID, date, url)
        values
            (?,?,?,?)
        ;''', [meeting.name, meeting.ID, meeting.date, meeting.url])

        for item in meeting.agenda:
            cur.execute('''
            INSERT INTO agendas
                (ID, text)
            values
                (?,?)
            ;''', [meeting.ID, item])

        for item in meeting.bylaws:
            cur.execute('''
            INSERT INTO bylaws
                (ID, name, text)
            values
                (?,?,?)
            ;''', [meeting.ID, item[0], item[1]])

        for motion in meeting.motions:


            inFavourID = cur.execute("select ID from groups where people=?", [motion.inFavour,]).fetchone()
            if inFavourID == None:
                cur.execute('''
                INSERT INTO groups
                    (people)
                values
                    (?);''', [motion.inFavour,])

                con.commit()
                inFavourID = cur.execute("select ID from groups where people=?", [motion.inFavour, ]).fetchone()

            inFavourID = inFavourID[0]

            opposedID = cur.execute("select ID from groups where people=?", [motion.opposed,]).fetchone()
            if opposedID == None:
                cur.execute('''
                INSERT INTO groups
                    (people)
                values
                    (?);''', [motion.opposed, ])

                con.commit()
                opposedID = cur.execute("select ID from groups where people=?", [motion.opposed, ]).fetchone()
            opposedID = opposedID[0]

            cur.execute('''
            INSERT INTO bylaws
                (ID, movedBy, secondedBy, desc, inFavour, opposed, result, status)
            values
                (?,?,?,?,?,?,?,?)
            ;''', [meeting.ID, motion.movedBy, motion.secondedBy, motion.desc, inFavourID, opposedID, motion.result, motion.status])

        con.commit()
filename = "file.txt"

class Meeting():
    def __init__(self, name, ID, date):
        self.name = name
        self.ID = ID
        self.date = date
        self.url = 'https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id='+self.ID+"&Agenda=PostMinutes&lang=English"
        self.motions = parseMotions(self.url)
        self.agenda = []

        html = getHtml(self.url)
        #+ 'style="display:inline-block;" >'
        items = getElemValue("<DIV class='AgendaItemTitle' ", "</DIV>", html)
        for item in items:
            self.agenda.append(cleanText(getElems(item)[0]))

        terms = ["Budget and Planning Discussion - Verbal report", "Vote on Reports not Selected for Debate", "Reports to be Dealt with at a Different Meeting", "Explanation of Public Hearing Process", "Bylaws and Related Reports", "Call for Persons to Speak", "Call to Order", "Land Acknowledgement", "Roll Call", "Adoption of Agenda", "Requests for Specific Time on Agenda", "Approval of Minutes", "Items for Discussion and Related Business", "Vote on Bylaws not Selected for Debate", "Protocol Items", "Select Items for Debate", "Public Reports", "Requests to", "Councillor Inquiries", "Adjournment", "Motions Pending", "Private Reports", "Notices of Motion and Motions without Customary Notice"]
        self.agenda = filterInterest(self.agenda, terms, ["Bylaws"])

        self.bylaws, self.agenda = splitAgenda(self.agenda)

    def output(self):
        print(self.name + " " + self.date)
        print(self.url)
        print("Agenda:")
        for item in self.agenda:
            print("* " + item)
        print("Motions:")
        for item in self.motions:
            print(item.desc)
            print(item.status)
            print("---------")

class motion():
    def __init__(self):
        self.movedBy = ""
        self.secondedBy = ""
        self.desc = ""
        self.inFavour = ""
        self.opposed = ""
        self.result = ""
        self.status = False
        self.url = ""

    def createMotion(self, info, url):
        self.url = url

        if "MovedBy" in info:
            self.movedBy = cleanText(penetrate(getElems(getElemValue("<DIV class='MovedBy' >", "</DIV>", info)[0])[1]))
        else:
            self.movedBy = None

        if "SecondedBy" in info:
            self.secondedBy = cleanText(penetrate(getElems(getElemValue("<DIV class='SecondedBy' >", "</DIV>", info)[0])[1]))
        else:
            self.secondedBy = None

        if "MotionText" in info:
            self.desc = cleanText(getElemValue("<DIV class='MotionText RichText' >", "</DIV>", info)[0])
        else:
            self.desc = None

        if "MotionVoters" in info:
            votes = getElems(getElemValue("<TABLE class='MotionVoters' >", "</TABLE>", info)[0])

            while len(votes) > 0:
                if "In Favour" in votes[0][0]:
                    self.inFavour = cleanText(votes[0][1])
                elif "Opposed" in votes[0][0]:
                    self.inFavour = cleanText(votes[0][1])
                votes.pop(0)

        if "MotionResult" in info:
            self.result = cleanText(getElems(getElemValue("<DIV class='MotionResult' >", "</DIV>", info)[0]))

            if "Carried" in self.result:
                self.status = True
            elif self.result == "":
                self.result = "Not voted"

    def output(self):
        print("Url: " + self.url)
        if self.movedBy:
            print("Moved by: " + self.movedBy)
        if self.secondedBy:
            print("Seconded By: " + self.secondedBy)
        if self.desc:
            print("Description: " + self.desc)

        print("In Favour: " + outputVoters(self.inFavour))
        print("Opposed: " + outputVoters(self.opposed))
        print(self.result)

def splitAgenda(agenda):
    bylaws = []
    others = []
    for item in agenda:
        if item[0:6] == "Bylaw " or item[0:14] == "Charter Bylaw ":
            bylaws.append(item.split(" - "))
        else:
            others.append(item)

    return bylaws, others

def getHtml(url):
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    html = mybytes.decode("utf8")
    fp.close()

    while "  " in html:
        html = html.replace('  ', '')

    html = html.replace('\n', '')

    html = removeElement("<script", "</script>", html)
    html = removeElement("<style", "</style>", html)
    html = removeElement("<html", '"en">', html)
    html = removeElement("<!DOC", "html>", html)
    html = removeElement("<!--", "-->", html)


    #file = open(filename, "w")
    #file.write(html)
    #file.close()

    return html

def getElemValue(start, end, html):
    startLen = len(start)
    endLen = len(end)

    hasStart = False
    opened = 0

    elems = []
    elemStart = 0

    for char in range(len(html)):
        if hasStart == False:
            if html[char:char+startLen] == start:
                hasStart = True
                opened = 0
                elemStart = char + startLen
        else:

            if html[char:char + endLen] == end and opened == 0:
                #print("element found!")
                elems.append(html[elemStart:char])
                hasStart = False
            elif html[char] == '<':
                if html[char:char+2] == '</':
                    opened -= 1
                    #print(opened)
                elif html[char:char + 4] not in ['<br>', '<BR ', '<img', '<hr>', '<col', '<inp', '<lin']:
                    opened += 1

    return elems

def removeElement(startElem, endElem, html):
    while startElem in html:
        start = html.index(startElem)
        end = html.index(endElem)
        #print(html[start:end+len(endElem)])
        html = html[:start] + html[end+len(endElem):]
    return html

def filterInterest(elems, boringTerms, boringLines):

    important = []
    for elem in elems:
        #if "<strong>" in elem:
        #    print(elem)
        good = True
        for term in boringTerms:
            if term in elem:
                good = False
                break
        for line in boringLines:
            if line == elem:
                good = False
                break
        if good == True:
            important.append(elem)

    return important

def getElems(html):
    elems = getElemValue('<', '</', html)
    #print(elems)
    #print(len(elems))
    if len(elems) == 0:
        return html
    else:
        newElems = []
        for elem in elems:
            #print(elem)
            newElems.append(getElems(elem))
        return newElems

def penetrate(value):
    while isinstance(value, list):
        value = value[0]
    return value

def fullPenetration(value):
    if isinstance(value, list):
        text = ""
        for i in value:
            text += "\n" + fullPenetration(i)
        return text[1:]
    else:
        return cleanText(value)

def cleanText(text):
    if ">" in text:
        return str(BeautifulSoup(text[text.index(">")+1:len(text)]))
    return text

def splitVoters(votes):
    votes = votes.replace(" and ", " ")
    return votes.split(", ")

def outputVoters(votes):
    output = ""
    for voter in votes:
        output = output + ", " + voter

    return output[2:]

def parseMotions(url):
    html = getHtml(url)

    elems = getElemValue("<LI class='AgendaItemMotion' >", "</LI>", html)
    terms = ["meeting minutes be approved", "That Community and Public Services Committee hear from the following speakers", "2nd round", "That the following items be dealt with at a specific time on the agenda:", "read a first time", "read a second time", "third reading", "read a third time", "That the minutes from the following meetings be approved", "That the Public Hearing on","meeting agenda be adopted", "Agenda Review Committee", "Office of the City Clerk report"]
    elems = filterInterest(elems, terms, [])

    motions = []
    for elem in elems:
        #info = getElems(elem)
        newMotion = motion()
        newMotion.createMotion(elem, url)
        motions.append(newMotion)

    #i = 0
    #while i < len(motions):
    #    if motions[i].movedBy == "":
    #        motions.pop(i)
    #    else:
    #        i += 1

    return motions

def getMeetings(startDate, endDate):

    BASE_URL = 'https://pub-edmonton.escribemeetings.com'
    headers = {"Content-Type": "application/json"}
    data = "{'calendarStartDate':'"+startDate+"','calendarEndDate':'" +endDate + "'}"
    response = requests.post(f"{BASE_URL}/MeetingsCalendarView.aspx/GetAllMeetings", data=data, headers=headers)

    x = response.json()

    meetings = []
    for meeting in x['d']:
        meetings.append(Meeting(meeting['MeetingName'], meeting['ID'], meeting['StartDate']))

    i = 0
    while i < len(meetings):
        if len(meetings[i].agenda) == 0 and len(meetings[i].motions) == 0:
            meetings.pop(i)
        else:
            i = i +1
    return meetings

def getAllMeetings():
    date = datetime.datetime.now()
    startDate = "2022-01-01"
    endDate = date.strftime("%Y") + "-" + date.strftime("%m") + "-" + date.strftime("%d")

    meetings = getMeetings(startDate, endDate)
    return meetings

def getMonthMeetings():
    date = datetime.datetime.now()
    if date.strftime("%m") == "01":
        startDate = str(int(date.strftime("%Y")-1)) + "-12-01"
    else:
        startDate = date.strftime("%Y") + "-" + str(int(date.strftime("%m"))-1) + "-01"

    endDate = date.strftime("%Y") + "-" + date.strftime("%m") + "-" + date.strftime("%d")

    meetings = getMeetings(startDate, endDate)
    return meetings

#def retrieveMeetingsFromDatabase():
#    global cur, con
#    rawMeetings = cur.execute("select * from meetings").fetchall()
#    newMeetings = Meeting()

if FIRST_RUN == True:
    resetDatabase()

if __name__ == "__main__":

    #file = open(filename, "w")
    #file.write(html)
    #file.close()

    meetings = getMonthMeetings()
    print("got meetings")
    for meeting in meetings:
        uploadMeeting(meeting)

    #motions = parseMotions("https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id=ed3fc862-3398-4e59-97d5-69e4e9aee352&Agenda=PostMinutes&lang=English")

    #for motion in motions:
    #    motion.output()