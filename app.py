from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import sqlalchemy
from sqlalchemy.ext.serializer import dumps

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
from datetime import datetime
from flask_wtf.csrf import CSRFProtect


BACKUP_PATH = open("backup_path").read().strip()

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


class Sticker(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    entry_time = db.Column(db.DateTime, nullable=True)


class Entry(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class EntryLog(db.Model):
    __tablename__ = "entry_log"
    registration_number = db.Column(
        db.CHAR(9),
        # db.ForeignKey("entry.registration_number"),
        nullable=False,
        # primary_key=True,
    )
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)

    # __table_args__ = (
    #     db.PrimaryKeyConstraint(
    #         registration_number,
    #         time,
    #     ),
    #


class Concert(db.Model):
    registration_number = db.Column(db.CHAR(9), primary_key=True)
    is_in = db.Column(db.Boolean, default=False)
    last_scanned = db.Column(db.DateTime, nullable=True)


class ConcertLog(db.Model):
    __tablename__ = "concert_log"
    registration_number = db.Column(
        db.CHAR(9),
        # db.ForeignKey("concert.registration_number"),
        nullable=False,
        # primary_key=True,
    )
    is_entry = db.Column(db.Boolean, default=False)
    time = db.Column(db.DateTime, nullable=True, primary_key=True)

    # __table_args__ = (
    #     db.PrimaryKeyConstraint(
    #         registration_number,
    #         time,
    #     ),
    # )


table_map = {
    "sticker": Sticker,
    "entry": Entry,
    "sadhya": Sadhya,
    "concert": Concert,
}
log_map = {"entry": EntryLog, "concert": ConcertLog}


get_total_counts = lambda: {
    "sticker": db.session.query(Sticker).count(),
    "entry": db.session.query(Entry).count(),
    "sadhya": db.session.query(Sadhya).count(),
    "concert": db.session.query(Concert).count(),
}


# Create the database and table
with app.app_context():
    db.create_all()
    TOTAL_COUNTS = get_total_counts()


# admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "pbkdf2:sha256:260000$pyJqKiGxx513y4b6$1e40141f424908076a239af573d039e0182d28cd6d6acec2dcee4d26e1b6470b"

# volunteer credentials
VOLUNTEER_USERNAME = "volunteer"
VOLUNTEER_PASSWORD_HASH = "pbkdf2:sha256:260000$3ilfqNWJEXCD33Zy$c8b1c01b201250c21f2a8b2c827b6ac7d205206e8b54aeff3a9bdfd61d52380e"


@app.route("/reset/<string:table>")
def reset(table):
    if "admin" not in session:
        return {"error": "not an admin"}, 401

    if not table:
        return {"error": "no table provided"}, 400

    if table not in table_map:
        return {"error": "invalid table"}, 404

    table_obj = table_map[table]

    q = db.session.query(table_obj)
    serialized_data = dumps(q.all())
    backup_file = open(BACKUP_PATH + f"{table}.table", "wb")
    backup_file.write(serialized_data)
    backup_file.close()

    for i in db.session.query(table_obj):
        i.is_in = False
    db.session.commit()

    return {"error": ""}, 200


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
    # if table == "sadhya" and in_count and in_count % 300 == 0:
    #     flash(
    #         "The 300th person has entered. In-count display has been reset to zero.",
    #         "error",
    #     )
    return {
        "in_count": in_count,
        "out_count": TOTAL_COUNTS[table] - in_count,
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
    reg_number = ""

    if request.method == "POST":
        reg_number = request.form["registration_number"].strip().upper()
        table_obj = table_map[table]
        student = table_obj.query.filter_by(registration_number=reg_number).first()

        if not student:
            flash("Not registered", "error")
        else:
            if table in ["sadhya", "sticker"]:
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
        reg_no=reg_number,
    )


@app.route("/verify", methods=["GET", "POST"])
# @limiter.limit("200 per minute")
def verify():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    log = []
    table = request.args.get("table", None)
    reg_number = ""

    if request.method == "POST":
        reg_number = request.form["registration_number"].strip().upper()
        table_obj = table_map[table]
        student = table_obj.query.filter_by(registration_number=reg_number).first()

        if not student:
            flash("Not registered", "error")
        else:
            flash("Registered", "success")
            if table == "sadhya":
                if student.is_in:
                    flash(
                        f'Already scanned at {student.entry_time.strftime("%H:%M:%S")}',
                        "error",
                    )
                else:
                    flash("Not scanned yet.", "success")

                log = get_log(reg_number, table)

    for i, r in enumerate(log):
        log[i].time = r.time.strftime("%H:%M:%S")

    return render_template(
        "verify.html",
        tables=table_map.keys(),
        table=table,
        log=log[::-1],
        reg_no=reg_number,
    )


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "admin" not in session:
        return redirect(url_for("index"))

    success_responses, failure_responses = [], []
    reg_no = ""
    if request.method == "POST":
        reg_no = request.form["registration_number"].upper()

        for key in request.form.keys():
            if table_obj := table_map.get(key, None):
                if request.form["action"] == "remove":
                    record = table_obj.query.filter_by(registration_number=reg_no)
                    if record.count() > 0:
                        record.delete()
                        success_responses += [
                            f"Successfully removed from '{key.capitalize()}'"
                        ]
                    else:
                        failure_responses += [f"Was not in '{key.capitalize()}'"]
                else:
                    record = table_obj.query.filter_by(registration_number=reg_no)
                    if record.count() == 0:
                        new_record = table_obj(registration_number=reg_no)
                        db.session.add(new_record)
                        success_responses += [
                            f"Successfully added to '{key.capitalize()}'"
                        ]
                    else:
                        failure_responses += [f"Already in '{key.capitalize()}'"]

        db.session.commit()

    global TOTAL_COUNTS
    TOTAL_COUNTS = get_total_counts()

    return render_template(
        "edit.html",
        reg_no=reg_no,
        success_responses=success_responses,
        failure_responses=failure_responses,
    )


@app.route("/login", methods=["GET", "POST"])
# @limiter.limit("20 per minute")
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == VOLUNTEER_USERNAME and check_password_hash(
            VOLUNTEER_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            flash("Logged in as volunteer", "success")
            return redirect(url_for("index"))
        elif username == ADMIN_USERNAME and check_password_hash(
            ADMIN_PASSWORD_HASH, password
        ):
            session["logged_in"] = True
            session["admin"] = True
            flash("Logged in as admin", "success")
            return redirect(url_for("edit"))
        else:
            flash("Invalid login credentials", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("admin", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
