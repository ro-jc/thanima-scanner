from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from datetime import datetime
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.config["SECRET_KEY"] = open("secret").read()
app.config["SQLALCHEMY_DATABASE_URI"] = open("db_url").read()
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
# limiter = Limiter(get_remote_address, app=app)


class Wristband(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_scanned = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class Culturals(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_scanned = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class Sadhya(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_scanned = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class Concert(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_scanned = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


table_map = {
    "wristband": Wristband,
    "culturals": Culturals,
    "sadhya": Sadhya,
    "concert": Concert,
}

# Create the database and table
with app.app_context():
    db.create_all()

# admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:260000$WQNyaZ4k8tNHu6uf$4e471f012f9fbbede80d263c9deba4cfa264808455635f6240a05f5c8da2d234"


@app.route("/getCount/<string:table>")
def count(table):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    table_obj = table_map[table]
    return {
        "count": db.session.query(table_obj)
        .filter(table_obj.is_scanned == True)
        .count()
    }


@app.route("/", methods=["GET", "POST"])
# @limiter.limit("200 per minute")
def index():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # print(request.form)
        reg_number = request.form["registration_number"]
        table = table_map[request.form["table"]]
        student = table.query.filter_by(registration_number=reg_number).first()

        if student:
            if student.is_scanned:
                flash(
                    f'Already scanned at {student.last_scanned.strftime("%H:%M:%S")}',
                    "error",
                )
            else:
                student.is_scanned = True
                if not student.last_scanned:
                    student.last_scanned = datetime.now()
                db.session.commit()
                flash("Successfully scanned.", "success")
        else:
            flash("Not registered.", "error")

        db.session.commit()

    table = request.args.get("table", None)
    return render_template("index.html", table=table, count=count(table)["count"])


@app.route("/login", methods=["GET", "POST"])
# @limiter.limit("20 per minute")
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            flash("Invalid login credentials", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
