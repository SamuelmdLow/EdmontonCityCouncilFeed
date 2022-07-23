from flask import Flask, render_template
from getInfo import *

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/<year>")
def year(year):
    meetings = retrieveMeetingsFromDatabase(int(year))
    years = getAllYears()
    print(years)
    return render_template("meetings.html", meetings=meetings, year=year, years=years)

if __name__ == "__main__":
   app.run(debug=True)