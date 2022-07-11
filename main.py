import urllib.request
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
            if html[char] == '<':
                if html[char:char+2] == '</':
                    #print("closed")
                    opened -= 1
                else:
                    #print("opened")
                    opened += 1

    return elems

def checkMotion(elems):
    important = []
    for elem in elems:
        if '<strong>' in elem:
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

class motion():
    def __init__(self):
        self.name = ""
        self.movedBy = ""
        self.secondedBy = ""
        self.desc = ""
        self.inFavour = ""
        self.opposed = ""
        self.carried = False

    def createMotion(self, info):

        self.movedBy = cleanText(info[2][1])
        self.secondedBy = cleanText(info[3][1])
        self.name = cleanText(penetrate(info[4][0]))
        self.desc = cleanText(info[4][1][0])

        if len(info[4]) == 3:
            self.desc = self.desc + " " + cleanText(info[4][2][0])

        self.inFavour = cleanText(info[5][0][1])
        self.opposed = cleanText(info[5][1][1])
        if "carried" in cleanText(info[6]).lower():
            self.carried = True
        else:
            self.carried = False

    def output(self):
        print("Motion: " + self.name)
        print("Moved by: " + self.movedBy)
        print("Seconded By: " + self.secondedBy)
        print("Description: " + self.desc)
        print("In Favour: " + self.inFavour)
        print("Opposed: " + self.opposed)
        if self.carried:
            print("Carried")
        else:
            print("Defeated")

if __name__ == "__main__":

    html = getHtml('https://pub-edmonton.escribemeetings.com/Meeting.aspx?Agenda=PostMinutes&Id=90d0b4a6-47d2-47f1-a735-9076e5a89c0f&Item=19&Tab=attachments&lang=English')

    file = open(filename, "w")
    file.write(html)
    file.close()

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