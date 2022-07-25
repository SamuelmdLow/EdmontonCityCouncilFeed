from flask import Flask, render_template
from getInfo import *

app = Flask(__name__)

@app.route("/")
def index():
    years = getAllYears()
    return render_template("home.html", years=years)

@app.route("/year/<year>")
def year(year):
    meetings = retrieveMeetingsFromDatabase(int(year))
    years = getAllYears()
    print(years)
    return render_template("meetings.html", meetings=meetings, title=year, years=years)

@app.route("/search")
def search():
    years = getAllYears()
    return render_template("search.html", years=years)

@app.route("/search/<term>")
def retrieve(term):
    meetings = searchForTerm(term)
    years = getAllYears()
    return render_template("meetings.html", meetings=meetings, title=term, years=years)

if __name__ == "__main__":
   app.run(debug=True)