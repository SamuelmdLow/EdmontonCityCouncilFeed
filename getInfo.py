import json
import urllib
import requests
from bs4 import BeautifulSoup
import datetime
import sqlite3
import pathlib
from threading import Lock

lock = Lock()

database = 'database.db'

FIRST_RUN = True
if (pathlib.Path.cwd() / database).exists():
    FIRST_RUN = False

con = sqlite3.connect(database, check_same_thread=False)
cur = con.cursor()


def resetDatabase():
    global con, cur

    cur.execute('''
    CREATE TABLE meetings(
        name text,
        ID text,
        date text,
        url text,
        year integer
    );''')

    cur.execute('''
    CREATE TABLE agendas(
        ID text,
        text text,
        attachmentID integer
    );''')

    cur.execute('''
    CREATE TABLE attachments(
        meetingID text,
        attachmentID integer,
        name text,
        link text 
    );''')

    cur.execute('''
    CREATE TABLE bylaws(
        ID text,
        name text,
        text text,
        attachmentID integer
    );''')

    cur.execute('''
    CREATE TABLE motions(
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

    cur.execute('''
    CREATE TABLE years(
        year integer
    );''')

    con.commit()


def uploadMeeting(meeting):
    global con, cur
    if cur.execute("select ID from meetings where ID=?", [meeting.ID, ]).fetchone() == None:
        if cur.execute("select year from years where year=?", [int(meeting.date[0:4]), ]).fetchone() == None:
            cur.execute('''
            INSERT INTO years
                (year)
            values
                (?)
            ;''', [meeting.date[0:4], ])
        cur.execute('''
        INSERT INTO meetings
            (name, ID, date, url, year)
        values
            (?,?,?,?,?)
        ;''', [meeting.name, meeting.ID, meeting.date, meeting.url, int(meeting.date[0:4])])
        num = 0
        for item in meeting.agenda:

            for attachment in item[1]:
                cur.execute('''
                INSERT INTO attachments
                    (meetingID, attachmentID, name, link)
                values
                    (?,?,?,?)
                ;''', [meeting.ID + "A", num, attachment[0], attachment[1]])

            cur.execute('''
            INSERT INTO agendas
                (ID, text, attachmentID)
            values
                (?,?,?)
            ;''', [meeting.ID, item[0], num])

            num = num + 1
        num = 0
        for item in meeting.bylaws:
            # print(meeting.ID)
            # print(item[2])
            for attachment in item[2]:
                # print(attachment)
                cur.execute('''
                INSERT INTO attachments
                    (meetingID, attachmentID, name, link)
                values
                    (?,?,?,?)
                ;''', [meeting.ID + "B", num, attachment[0], attachment[1]])
            cur.execute('''
            INSERT INTO bylaws
                (ID, name, text, attachmentID)
            values
                (?,?,?,?)
            ;''', [meeting.ID, item[0], item[1], num])
            num = num + 1

        for motion in meeting.motions:

            inFavourID = cur.execute("select ID from groups where people=?", [motion.inFavour, ]).fetchone()
            if inFavourID == None:
                cur.execute('''
                INSERT INTO groups
                    (people)
                values
                    (?);''', [motion.inFavour, ])
                con.commit()
                inFavourID = cur.execute("select ID from groups where people=?", [motion.inFavour, ]).fetchone()

            inFavourID = inFavourID[0]

            opposedID = cur.execute("select ID from groups where people=?", [motion.opposed, ]).fetchone()
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
            INSERT INTO motions
                (ID, movedBy, secondedBy, desc, inFavour, opposed, result, status)
            values
                (?,?,?,?,?,?,?,?)
            ;''', [meeting.ID, motion.movedBy, motion.secondedBy, motion.desc, inFavourID, opposedID, motion.result,
                   motion.status])
        con.commit()


filename = "file.txt"


class Meeting():
    def __init__(self):
        self.name = ""
        self.ID = ""
        self.date = ""
        self.url = ""
        self.motions = []
        self.agenda = []
        self.bylaws = []

    def creteFromParse(self, name, ID, date):
        self.name = name
        self.ID = ID
        self.date = date
        self.url = 'https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id=' + self.ID + "&Agenda=PostMinutes&lang=English"
        self.motions = parseMotions(self.url)
        self.agenda = []

        html = getHtml(self.url)
        # + 'style="display:inline-block;" >'
        items = getElemValue("<DIV class='AgendaItemTitle' ", "</DIV>", html)
        for item in items:
            num = getElemValue("SelectItem(", ");", item)[0]
            rawAttachments = getElemValue("AgendaItemAttachment" + num, "</DIV>", html)
            attachments = []
            for attachment in rawAttachments:
                link = getElemValue('href="', '" ', attachment)[0]
                name = getElemValue("title='", "' ", attachment)[0]
                attachments.append([name, link])

            self.agenda.append([cleanText(getElems(item)[0]), attachments])

        terms = ["Budget and Planning Discussion - Verbal report", "Vote on Reports not Selected for Debate",
                 "Reports to be Dealt with at a Different Meeting", "Explanation of Public Hearing Process",
                 "Bylaws and Related Reports", "Call for Persons to Speak", "Call to Order", "Land Acknowledgement",
                 "Roll Call", "Adoption of Agenda", "Requests for Specific Time on Agenda", "Approval of Minutes",
                 "Items for Discussion and Related Business", "Vote on Bylaws not Selected for Debate",
                 "Protocol Items", "Select Items for Debate", "Public Reports", "Requests to", "Councillor Inquiries",
                 "Adjournment", "Motions Pending", "Private Reports",
                 "Notices of Motion and Motions without Customary Notice"]
        self.agenda = filterInterest(self.agenda, terms, ["Bylaws"])
        # print(self.agenda)
        self.bylaws, self.agenda = splitAgenda(self.agenda)

    def createFromDatabase(self, raw):
        global con, cur

        self.name = raw[0]
        self.ID = raw[1]
        self.date = raw[2]
        self.url = raw[3]

        self.motions = []

        rawMotions = cur.execute(
            "select movedBy, secondedBy, desc, inFavour, opposed, result, status from motions where ID=?",
            [raw[1], ]).fetchall()

        for rawMotion in rawMotions:
            newMotion = motion()
            newMotion.createFromDatabase(rawMotion)
            self.motions.append(newMotion)

        self.agenda = []

        rawAgenda = cur.execute("select text, attachmentID from agendas where ID=?", [raw[1], ]).fetchall()
        for rawItem in rawAgenda:
            attachmentID = rawItem[1]
            agendaAttachments = cur.execute("select name, link from attachments where meetingID=? and attachmentID=?",
                                            [raw[1] + "A", attachmentID]).fetchall()
            self.agenda.append([rawItem[0], agendaAttachments])

        self.bylaws = []
        rawBylaws = cur.execute("select name, text, attachmentID from bylaws where ID=?", [raw[1], ]).fetchall()
        for rawBylaw in rawBylaws:
            attachmentID = rawBylaw[2]
            bylawAttachments = cur.execute("select name, link from attachments where meetingID=? and attachmentID=?",
                                           [raw[1] + "B", attachmentID]).fetchall()
            self.bylaws.append([rawBylaw[0], rawBylaw[1], bylawAttachments])

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

    def createFromDatabase(self, data):
        global con, cur

        '''
        ID text,
        movedBy text,
        secondedBy text,
        desc text,
        inFavour integer,
        opposed integer,
        result text,
        status integer
        :param data: 
        :return: 
        '''
        self.movedBy = data[0]
        self.secondedBy = data[1]
        self.desc = data[2]
        self.inFavour = cur.execute("select people from groups where ID = ?", [data[3], ]).fetchone()[0]
        self.opposed = cur.execute("select people from groups where ID = ?", [data[4], ]).fetchone()[0]
        self.result = data[5]
        if data[6] == 1:
            self.status = True
        else:
            self.status = False

        self.url = ""

    def createFromParse(self, info, url):
        self.url = url

        if "MovedBy" in info:
            self.movedBy = cleanText(penetrate(getElems(getElemValue("<DIV class='MovedBy' >", "</DIV>", info)[0])[1]))
        else:
            self.movedBy = None

        if "SecondedBy" in info:
            self.secondedBy = cleanText(
                penetrate(getElems(getElemValue("<DIV class='SecondedBy' >", "</DIV>", info)[0])[1]))
        else:
            self.secondedBy = None

        if "MotionText" in info:
            # self.desc = cleanText(getElemValue("<DIV class='MotionText RichText' >", "</DIV>", info)[0])
            self.desc = getElemValue("<DIV class='MotionText RichText' >", "</DIV>", info)[0]
        else:
            self.desc = None

        if "MotionVoters" in info:
            votes = getElems(getElemValue("<TABLE class='MotionVoters' >", "</TABLE>", info)[0])

            while len(votes) > 0:
                if "In Favour" in votes[0][0]:
                    self.inFavour = cleanText(votes[0][1])
                elif "Opposed" in votes[0][0]:
                    self.opposed = cleanText(votes[0][1])
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

        if item[0][0:6] == "Bylaw " or item[0][0:14] == "Charter Bylaw ":

            if "-" in item[0]:
                bylaw = [item[0][:item[0].index("-") - 1], item[0][item[0].index("-") + 2:]]
            elif item[0][0:6] == "Bylaw ":
                x = item[0][item[0].index(" ") + 1:].index(" ")
                bylaw = [item[0][:x], item[0][x:]]
            elif item[0][0:14] == "Charter Bylaw ":
                x = item[0][item[0][item[0].index(" ") + 1:].index(" ") + 1:].index(" ")
                bylaw = [item[0][:x], item[0][x:]]
            else:
                print(item[0])
                bylaw = ["", item[0]]
            bylaw.append(item[1])
            bylaws.append(bylaw)
        else:
            others.append(item)

    return bylaws, others


def getHtml(url):
    fp = urllib.urlopen(url)
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

    # file = open(filename, "w")
    # file.write(html)
    # file.close()

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
            if html[char:char + startLen] == start:
                hasStart = True
                opened = 0
                elemStart = char + startLen
        else:

            if html[char:char + endLen] == end and opened == 0:
                # print("element found!")
                elems.append(html[elemStart:char])
                hasStart = False
            elif html[char] == '<':
                if html[char:char + 2] == '</':
                    opened -= 1
                    # print(opened)
                elif html[char:char + 4] not in ['<br>', '<BR ', '<img', '<hr>', '<col', '<inp', '<lin']:
                    opened += 1

    return elems


def removeElement(startElem, endElem, html):
    while startElem in html:
        start = html.index(startElem)
        end = html.index(endElem)
        # print(html[start:end+len(endElem)])
        html = html[:start] + html[end + len(endElem):]
    return html


def filterInterest(elems, boringTerms, boringLines):
    important = []
    for elem in elems:
        # if "<strong>" in elem:
        #    print(elem)

        if not isinstance(elem, str):
            tested = elem[0]
        else:
            tested = elem

        good = True
        for term in boringTerms:
            if term in tested:
                good = False
                break
        for line in boringLines:
            if line == tested:
                good = False
                break
        if good == True:
            important.append(elem)

    return important


def getElems(html):
    elems = getElemValue('<', '</', html)
    # print(elems)
    # print(len(elems))
    if len(elems) == 0:
        return html
    else:
        newElems = []
        for elem in elems:
            # print(elem)
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
        return str(BeautifulSoup(text[text.index(">") + 1:len(text)]))
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
    terms = ["meeting minutes be approved",
             "That Community and Public Services Committee hear from the following speakers", "2nd round",
             "That the following items be dealt with at a specific time on the agenda:", "read a first time",
             "read a second time", "third reading", "read a third time",
             "That the minutes from the following meetings be approved", "That the Public Hearing on",
             "meeting agenda be adopted", "Agenda Review Committee", "Office of the City Clerk report"]
    elems = filterInterest(elems, terms, [])

    motions = []
    for elem in elems:
        # info = getElems(elem)
        newMotion = motion()
        newMotion.createFromParse(elem, url)
        motions.append(newMotion)

    # i = 0
    # while i < len(motions):
    #    if motions[i].movedBy == "":
    #        motions.pop(i)
    #    else:
    #        i += 1

    return motions


def getMeetings(startDate, endDate):
    BASE_URL = 'https://pub-edmonton.escribemeetings.com'
    headers = {"Content-Type": "application/json"}
    data = "{'calendarStartDate':'" + startDate + "','calendarEndDate':'" + endDate + "'}"
    response = requests.post(BASE_URL + "/MeetingsCalendarView.aspx/GetAllMeetings", data=data, headers=headers)

    x = response.json()

    meetings = []
    for meeting in x['d']:
        newMeeting = Meeting()
        newMeeting.creteFromParse(meeting['MeetingName'], meeting['ID'], meeting['StartDate'])
        meetings.append(newMeeting)
    print(len(meetings))
    i = 0
    while i < len(meetings):
        if len(meetings[i].agenda) == 0 and len(meetings[i].motions) == 0:
            meetings.pop(i)
        else:
            i = i + 1
    return meetings


def getAllMeetings():
    date = datetime.datetime.now()

    year = 2020
    while year < int(date.strftime("%Y")) + 1:
        print(year)
        newMeetings = getMeetings(str(year) + "-01-01", str(year + 1) + "-01-01")
        print(len(newMeetings))
        for meeting in newMeetings:
            uploadMeeting(meeting)

        year = year + 1


def getMonthMeetings():
    date = datetime.datetime.now()
    if date.strftime("%m") == "01":
        startDate = str(int(date.strftime("%Y") - 1)) + "-12-01"
    else:
        startDate = date.strftime("%Y") + "-" + str(int(date.strftime("%m")) - 1) + "-01"

    endDate = date.strftime("%Y") + "-" + date.strftime("%m") + "-" + date.strftime("%d")

    meetings = getMeetings(startDate, endDate)

    for meeting in meetings:
        uploadMeeting(meeting)

    return meetings


def getPastMeetings():
    date = datetime.datetime.now()
    if date.strftime("%m") == "01":
        startDate = str(int(date.strftime("%Y") - 1)) + "-12-30"
    elif date.strftime("%d") == "01" or date.strftime("%d") == "02":
        startDate = date.strftime("%Y") + "-" + str(int(date.strftime("%m")) - 1) + "-28"
    else:
        startDate = date.strftime("%Y") + "-" + date.strftime("%m") + "-" + str(int(date.strftime("%d")) - 2)

    endDate = date.strftime("%Y") + "-" + date.strftime("%m") + "-" + date.strftime("%d")

    meetings = getMeetings(startDate, endDate)

    for meeting in meetings:
        uploadMeeting(meeting)

    return startDate


def getAllYears():
    global con, cur

    rawYears = con.execute("select year from years order by year desc").fetchall()
    years = []
    for year in rawYears:
        years.append(year[0])

    return years


def searchForTerm(terms):
    global con, cur

    meetings = []

    rawMeetings = cur.execute("select * from meetings order by date desc").fetchall()

    for rawMeeting in rawMeetings:

        rawMotions = cur.execute(
            "select movedBy, secondedBy, desc, inFavour, opposed, result, status from motions where ID=?",
            [rawMeeting[1], ]).fetchall()
        rawAgendas = cur.execute("select * from agendas where ID=?", [rawMeeting[1], ]).fetchall()
        rawBylaws = cur.execute("select * from bylaws where ID=?", [rawMeeting[1], ]).fetchall()

        motions = []
        for rawMotion in rawMotions:
            for term in terms:
                if term.lower() in rawMotion[2].lower():
                    newMotion = motion()
                    newMotion.createFromDatabase(rawMotion)
                    motions.append(newMotion)
                    break

        agendas = []
        for rawItem in rawAgendas:
            for term in terms:
                if term.lower() in rawItem[1].lower():
                    attachmentID = rawItem[2]
                    agendaAttachments = cur.execute(
                        "select name, link from attachments where meetingID=? and attachmentID=?",
                        [rawMeeting[1] + "A", attachmentID]).fetchall()

                    agendas.append([rawItem[1], agendaAttachments])
                    break

        bylaws = []
        for rawBylaw in rawBylaws:
            for term in terms:
                if term.lower() in rawBylaw[2].lower():
                    attachmentID = rawBylaw[3]
                    bylawAttachments = cur.execute(
                        "select name, link from attachments where meetingID=? and attachmentID=?",
                        [rawMeeting[1] + "B", attachmentID]).fetchall()

                    bylaws.append([rawBylaw[1], rawBylaw[2], bylawAttachments])
                    break

        if len(motions) > 0 or len(agendas) > 0 or len(bylaws) > 0:
            newMeeting = Meeting()
            newMeeting.createFromDatabase(rawMeeting)
            newMeeting.motions = motions
            newMeeting.agenda = agendas
            newMeeting.bylaws = bylaws

            meetings.append(newMeeting)

    return meetings


def getRecentMeetings():
    global con, cur

    meetings = []
    rawMeetings = cur.execute("select * from meetings order by date desc").fetchall()

    if len(rawMeetings) > 10:
        rawMeetings = rawMeetings[0:10]
    else:
        rawMeetings = rawMeetings

    for rawMeeting in rawMeetings:
        newMeeting = Meeting()
        newMeeting.createFromDatabase(rawMeeting)

        meetings.append(newMeeting)

    return meetings


def retrieveMeetingsFromDatabase(year):
    global con, cur

    rawMeetings = cur.execute("select * from meetings where year=? order by date desc", [year, ]).fetchall()

    meetings = []

    # print(rawMeetings)

    for raw in rawMeetings:
        newMeeting = Meeting()
        newMeeting.createFromDatabase(raw)
        meetings.append(newMeeting)

    return meetings


def arrangeRss(meetings):
    items = ""
    for meeting in meetings:
        description = ""

        if len(meeting.agenda) > 0:
            description += "<h3>Agenda</h3>"
            for item in meeting.agenda:
                description += item[0].decode('utf-8')
                if len(item[1]) > 0:
                    description += "<ul>"
                    for attachment in item[1]:
                        description += '<li class="attachment"><a href="https://pub-edmonton.escribemeetings.com/' + \
                                       attachment[1] + '" target="_blank">' + attachment[0] + '</a></li>'
                    description += "</ul>"

        if len(meeting.bylaws) > 0:
            description += "<h3>Bylaws</h3>"
            description += "<table>"
            for bylaw in meeting.bylaws:
                description += "<tr><td>" + bylaw[0] + "</td><td>" + bylaw[1]
                if len(bylaw[2]) > 0:
                    description += "<ul>"
                    for attachment in bylaw[2]:
                        description += '<li class="attachment"><a href="https://pub-edmonton.escribemeetings.com/' + \
                                       attachment[1] + '" target="_blank">' + attachment[0] + '</a></li>'
                    description += "</ul>"
                description += "</td>"
            description += "</table>"

        if len(meeting.motions) > 0:
            description += "<h3>Motions</h3><ul>"

            for motion in meeting.motions:
                description += "<li><p>" + motion.result + "</p><ul><li>In Favour:" + motion.inFavour + "</li><li>Opposed:" + motion.opposed + "</li></ul><p>" + motion.desc + "</p></li>"
            description += "</ul>"

        items += '''<item>
        <title><![CDATA[''' + meeting.name + ''']]></title>
        <link><![CDATA[''' + meeting.url + ''']]></link>
        <pubDate><![CDATA[''' + meeting.date + ''']]></pubDate>

        <description><![CDATA[''' + description + ''']]></description>
        </item>'''

    return items

def pagify(meetings, max=15):
    if len(meetings) < max:
        pagify = meetings
    else:
        pagify = []
        p=0
        while p < len(meetings)/max:
            pagify.append(meetings[p*max:(p+1)*max])
            p = p + 1

    return pagify

if FIRST_RUN == True:
    resetDatabase()
    getAllMeetings()

if __name__ == "__main__":
    pass
    # file = open(filename, "w")
    # file.write(html)
    # file.close()

    # meetings = getMonthMeetings()
    # print("got meetings")
    # for meeting in meetings:
    #    uploadMeeting(meeting)

    getAllMeetings()

    # getAllYears()

    # motions = parseMotions("https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id=ed3fc862-3398-4e59-97d5-69e4e9aee352&Agenda=PostMinutes&lang=English")

    # for motion in motions:
    #    motion.output()

    # meetings = retrieveMeetingsFromDatabase(2022)

    # for meeting in meetings:
    #    meeting.output()