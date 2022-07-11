import urllib.request
filename = "file.txt"

def getHtml(url):
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    html = mybytes.decode("utf8")
    fp.close()

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
    terms = ["be read a first time", "be read a second time", "be considered for third reading", "be read a third time", "That the minutes from the following meetings be approved"]
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

    def createMotion(self, info):

        self.movedBy = cleanText(info[2][1])
        self.secondedBy = cleanText(info[3][1])


        for text in info[4]:
            self.desc = self.desc + " " + cleanText(penetrate(text))

        self.desc = self.desc[1:]

        if len(info[4]) == 3:
            self.desc = self.desc + " " + cleanText(penetrate(info[4][2][0]))

        if len(info[5][0]) > 1:
            self.inFavour = splitVoters(cleanText(info[5][0][1]))

        if len(info[5][1]) > 1:
            self.opposed = splitVoters(cleanText(info[5][1][1]))

        if "carried" in cleanText(info[6]).lower():
            self.status = "Carried"
        elif "defeated" in cleanText(info[6]).lower():
            self.status = "Defeated"
        else:
            self.status = "Not Voted"

    def output(self):
        print("Moved by: " + self.movedBy)
        print("Seconded By: " + self.secondedBy)
        print("Description: " + self.desc)

        print("In Favour: " + outputVoters(self.inFavour))
        print("Opposed: " + outputVoters(self.opposed))
        print(self.status)

if __name__ == "__main__":
    html = getHtml('https://pub-edmonton.escribemeetings.com/Meeting.aspx?Id=af273061-b1c9-4143-a0c5-a56b48d415a4&Agenda=PostMinutes&lang=English')

    file = open(filename, "w")
    file.write(html)
    file.close()

    while "  " in html:
        html = html.replace('  ', '')

    html = html.replace('\n', '')

    elems = getElemValue("<LI class='AgendaItemMotion' >", "</LI>", html)
    elems = checkMotion(elems)

    motions = []
    for elem in elems:
        info = getElems(elem)
        newMotion = motion()
        newMotion.createMotion(info)
        motions.append(newMotion)

    for motion in motions:
        motion.output()
        print("\n")