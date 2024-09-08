from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from datetime import datetime
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.config["SECRET_KEY"] = open("secret").read().strip()
app.config["SQLALCHEMY_DATABASE_URI"] = open("db_url").read().strip()
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
# limiter = Limiter(get_remote_address, app=app)


class Sadhya(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime, nullable=True)


class Entry(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class EntryLog(db.Model):
    __tablename__ = "entry_log"
    registration_number = db.Column(db.CHAR(9))
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)


class Concert(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class ConcertLog(db.Model):
    __tablename__ = "concert_log"
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)


table_map = {
    "sadhya": Sadhya,
    "entry": Entry,
    "concert": Concert,
}
log_map = {"entry": EntryLog, "concert": ConcertLog}

# Create the database and table
with app.app_context():
    db.create_all()

# admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:260000$qEVfYZHe7Kn5hOib$7eefd86c39af2e23f9cc0d2ed53bff5633e0d13a0611ef01f8f6598ead513972"

TOTAL_COUNT = db.session.query(Entry).count()


@app.route("/getCount/<string:table>")
def get_count(table):
    if "logged_in" not in session:
        return {"count": "", "error": "not logged in"}

    if not table:
        return {"count": "", "error": "no table provided"}

    if table not in table_map:
        return {"count": "", "error": "invalid table"}

    table_obj = table_map[table]
    in_count = db.session.query(table_obj).filter(table_obj.is_in == True).count()
    if table == "sadhya" and in_count and in_count % 300 == 0:
        flash(
            "The 300th person has entered. In-count display has been reset to zero.",
            "error",
        )
    return {
        "in_count": in_count,
        "out_count": TOTAL_COUNT - in_count,
        "error": "",
    }


def get_log(reg_number, table):
    table_obj = log_map[table]
    return (
        db.session.query(table_obj)
        .filter(table_obj.registration_number == reg_number)
        .all()
    )


@app.route("/", methods=["GET", "POST"])
# @limiter.limit("200 per minute")
def index():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    log = []
    table = request.args.get("table", None)

    if request.method == "POST":
        reg_number = request.form["registration_number"].strip().upper()
        table_obj = table_map[table]
        student = table_obj.query.filter_by(registration_number=reg_number).first()

        if not student:
            flash("Not registered", "error")
        else:
            if table == "sadhya":
                if student.is_in:
                    flash(
                        f'Already scanned at {student.entry_time.strftime("%H:%M:%S")}',
                        "error",
                    )
                else:
                    student.is_in = True
                    student.entry_time = datetime.now()
                    db.session.commit()
                    flash("Successfully scanned.", "success")
            else:
                student.is_in = not student.is_in
                record = log_map[table](
                    registration_number=reg_number, time=datetime.now()
                )

                if not student.is_in:
                    record.is_entry = False
                    # flash(f"Left", "error")
                else:
                    record.is_entry = True
                    # flash("Entered", "error")

                student.last_scanned = datetime.now()
                db.session.add(record)
                db.session.commit()

                log = get_log(reg_number, table)

    count_response = get_count(table=table)

    if count_response["error"]:
        print("count error:", count_response["error"])
        in_count = ""
        out_count = ""
    else:
        in_count = count_response["in_count"]
        out_count = count_response["out_count"]

    for i, r in enumerate(log):
        log[i].time = r.time.strftime("%H:%M:%S")

    return render_template(
        "index.html",
        tables=table_map.keys(),
        table=table,
        in_count=in_count,
        out_count=out_count,
        log=log[::-1],
    )


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
            flash("Logged in", "success")
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
