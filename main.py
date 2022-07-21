from flask import Flask, render_template
from getInfo import *

app = Flask(__name__)

@app.route("/")
def index():
    meetings = getMonthMeetings()
    return render_template("index.html", meetings=meetings)

if __name__ == "__main__":
   app.run(debug=True)