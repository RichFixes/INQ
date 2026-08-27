from app import create_app
from flask import Blueprint, render_template, request
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

@main.route("/")
def index():
    return render_template("inquiry.html")

@main.route("/inquiry", methods=["GET", "POST"])
def inquiry():
    if request.method == "POST":
        # your processing logic goes here
        return render_template("thank_you.html")
    return render_template("inquiry.html")

@main.route("/schedule")
def schedule():
    return render_template("schedule.html")
