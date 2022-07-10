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

def getElems(start, end, html):
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
                elemStart = char
        else:
            if html[char:char + endLen] == end and opened == 0:
                #print("element found!")
                elems.append(html[elemStart:char+endLen])
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

def getElemValue(html):
    pass

if __name__ == "__main__":

    html = getHtml('https://pub-edmonton.escribemeetings.com/Meeting.aspx?Agenda=PostMinutes&Id=90d0b4a6-47d2-47f1-a735-9076e5a89c0f&Item=19&Tab=attachments&lang=English')

    file = open(filename, "w")
    file.write(html)
    file.close()

    elems = getElems("<LI class='AgendaItemMotion' >", "</LI>", html)

    elems = checkMotion(elems)

    for elem in elems:
        print(elem)