import json
import urllib.request
import requests
from bs4 import BeautifulSoup

filename = "file.txt"

def getHtml(url):
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    html = mybytes.decode("utf8")
    fp.close()

    while "  " in html:
        html = html.replace('  ', '')

    html = html.replace('\n', '')

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
                elif html[char:char+4] != '<br>':
                    opened += 1
                    #print(opened)
                #print(html[char:char + 20] + " " + str(opened))

    return elems

def checkMotion(elems):
    terms = ["be read a first time", "be read a second time", "be considered for third reading", "be read a third time", "That the minutes from the following meetings be approved", "That the Public Hearing on", "City Council meeting agenda be adopted"]
    important = []
    for elem in elems:
        good = True
        for term in terms:
            if term in elem:
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
            text += " " + fullPenetration(i)
        return text[1:]
    else:
        return cleanText(value)

def cleanText(text):
    if ">" in text:
        return text[text.index(">")+1:len(text)]
    return text

def splitVoters(votes):
    votes = votes.replace(" and ", " ")
    return votes.split(", ")

def outputVoters(votes):
    output = ""
    for voter in votes:
        output = output + ", " + voter

    return output[2:]

class motion():
    def __init__(self):
        self.movedBy = ""
        self.secondedBy = ""
        self.desc = ""
        self.inFavour = []
        self.opposed = []
        self.status = ""
        self.url = ""

    def createMotion(self, info, url):
        if len(info[2]) > 1:
            self.movedBy = cleanText(penetrate(info[2][1]))
            if len(info[3]) > 1:
                self.secondedBy = cleanText(penetrate(info[3][1]))

            self.url = url

            self.desc = str(BeautifulSoup(fullPenetration(info[4]), features="html.parser"))

            if len(info[5][0]) > 1:
                self.inFavour = splitVoters(cleanText(penetrate(info[5][0][1])))

            if len(info[5][1]) > 1:
                self.opposed = splitVoters(cleanText(penetrate(info[5][1][1])))

            if len(info) > 6:

                if "carried" in cleanText(penetrate(info[6])).lower():
                    self.status = "Carried"
                elif "defeated" in cleanText(penetrate(info[6])).lower():
                    self.status = "Defeated"
                else:
                    self.status = "Not Voted"
            else:
                self.status = "Not Voted"

    def output(self):
        print("Url: " + self.url)
        print("Moved by: " + self.movedBy)
        print("Seconded By: " + self.secondedBy)
        print("Description: " + self.desc)
        print("In Favour: " + outputVoters(self.inFavour))
        print("Opposed: " + outputVoters(self.opposed))
        print(self.status)

def parseMotions(url):
    html = getHtml(url)

    #file = open(filename, "w")
    #file.write(html)
    #file.close()

    elems = getElemValue("<LI class='AgendaItemMotion' >", "</LI>", html)
    elems = checkMotion(elems)

    motions = []
    for elem in elems:
        info = getElems(elem)
        newMotion = motion()
        newMotion.createMotion(info, url)
        motions.append(newMotion)

    return motions

def getMeetings():
    BASE_URL = 'https://pub-edmonton.escribemeetings.com'
    headers = {"Content-Type": "application/json"}
    data = "{'calendarStartDate':'2022-07-01','calendarEndDate':'2022-08-01'}"
    response = requests.post(f"{BASE_URL}/MeetingsCalendarView.aspx/GetAllMeetings", data=data, headers=headers)

    x = response.json()

    ids = []
    for meeting in x['d']:
        ids.append(meeting['ID'])

    return(ids)

if __name__ == "__main__":

    ids = getMeetings()
    motions = []
    for id in ids:
        url = 'https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id='+id+"&Agenda=PostMinutes&lang=English"
        #print(url)
        motions += parseMotions(url)

    i = 0
    while i < len(motions):
        if motions[i].movedBy == "":
            motions.pop(i)
        else:
            i += 1

    for motion in motions:
        motion.output()
