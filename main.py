from flask import Flask, Response, render_template, request
from getInfo import *

app = Flask(__name__)


@app.route("/")
def index():
    years = getAllYears()
    return render_template("home.html", years=years)


meetingsPerPage = 15

@app.route("/year/<year>")
def year(year):
    meetings = retrieveMeetingsFromDatabase(int(year))
    years = getAllYears()

    pages = pagify(meetings)
    page = int(request.args.get("page", 1))

    pageMeetings = pages[page-1]

    print(years)
    return render_template("meetings.html", meetings=pageMeetings, pageNum=page, pageCount=len(pages), title=year, years=years, rss="all")


@app.route("/search")
def search():
    years = getAllYears()
    return render_template("search.html", years=years)


@app.route("/search/<strterms>")
def retrieve(strterms):
    terms = strterms.split(",")
    meetings = searchForTerm(terms)
    years = getAllYears()

    pages = pagify(meetings)
    page = int(request.args.get("page", 1))

    pageMeetings = pages[page-1]

    return render_template("meetings.html", meetings=pageMeetings, pageNum=page, pageCount=len(pages), title="Terms: " + strterms, years=years, rss=strterms)


@app.route("/updateMonth")
def updateMonth():
    message = getMonthMeetings()
    return "<p>thanks for updating me!</p>" + message


@app.route("/update")
def update():
    message = getPastMeetings()
    return "<p>thanks for updating me!</p>" + message


@app.route("/rss/all")
def allRss():
    meetings = getRecentMeetings()

    items = arrangeRss(meetings)

    xml = '''
    <rss version = "2.0">
    <channel>
    <title> Unofficial Records of YEG City Council | All</title>
    <link> https://yegrecords.glitch.me </link>
    <description>Parses contents of Edmonton City Council Meeting Minutes found here: https://pub-edmonton.escribemeetings.com.</description>
    ''' + items + '''
    </channel>
    </rss>
    '''

    return Response(xml, mimetype='text/xml')


@app.route("/rss/<strterm>")
def customRss(strterm):
    terms = strterm.split(",")
    meetings = searchForTerm(terms)[0:10]

    items = arrangeRss(meetings)

    xml = '''
    <rss version = "2.0">
    <channel>
    <title> Unofficial Records of YEG City Council | ''' + strterm + '''</title>
    <link> https://yegrecords.glitch.me </link>
    <description>Parses contents of Edmonton City Council Meeting Minutes found here: https://pub-edmonton.escribemeetings.com. This is a custom feed which only includes meetings with mention of these terms: ''' + strterm + '''</description>
    ''' + items + '''
    </channel>
    </rss>
    '''

    return Response(xml, mimetype='text/xml')


if __name__ == "__main__":
    app.run(debug=True)