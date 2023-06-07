from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TimeField
from wtforms.validators import DataRequired, URL
import smtplib
import os

# set info for smtp as environmental variable to keep safe
USER = os.environ["USER"]
PASSWORD = os.environ["PASSWORD"]

# ---------------------------- START FLASK FRAMEWORK ------------------------------- #
app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]

# ---------------------------- DATABASE SETUP ------------------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes-banff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Cafes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    location = db.Column(db.String(250), unique=True, nullable=False)
    maps_url = db.Column(db.VARCHAR(500), unique=True, nullable=False)
    image_url = db.Column(db.VARCHAR(500), unique=True, nullable=False)
    open = db.Column(db.String(7), nullable=False)
    close = db.Column(db.String(7), nullable=False)
    wifi = db.Column(db.Boolean)
    sockets = db.Column(db.Boolean)
    mountain_views = db.Column(db.Boolean)

    # allows each Cafe Object to be identified by its name when printed
    # otherwise it will only print out "<Cafes 1>"
    def __repr__(self):
        return f"<Cafe> {self.cafe}"


# ---------------------------- SETUP FLASK FORM TO ADD CAFES ------------------------------- #
select_choices = ["Yes", "No", "I don't know"]


class CafeForm(FlaskForm):
    name = StringField('Cafe Name', validators=[DataRequired()])
    location = StringField('Address', validators=[DataRequired()])
    maps_url = StringField('Cafe Location on Google Maps (URL)', validators=[URL(message="Please provide a URL")])
    image_url = StringField('Cafe Image (URL)', validators=[URL(message="Please provide a URL")])
    open = TimeField('Opening Time')
    close = TimeField('Closing Time')
    wifi = SelectField('Wifi available?', choices=select_choices, default="I don't know")
    sockets = SelectField('Power Sockets available?', choices=select_choices, default="I don't know")
    mountain_views = SelectField('Mountain Views?', choices=select_choices, default="I don't know")
    submit = SubmitField('Submit')


# ---------------------------- CREATE FUNCTIONS ------------------------------- #
def check_submit_fields(option):
    """checks if option from SelectField is Yes or No and returns Boolean Value to be saved in the database"""
    if option == "Yes":
        return 1
    elif option == "No":
        return 0
    else:
        pass


# ---------------------------- CREATE ROUTES ------------------------------- #
@app.route("/")
def show_overview():
    """renders index.html, calls all Cafes saved in the DB and shows an overview of the Cafes"""
    cafes = db.session.query(Cafes).all()
    return render_template("index.html", all_cafes=cafes)


@app.route("/cafe/<int:cafe_id>")
def show_cafe(cafe_id):
    """renders cafe.html, calls the data of the requested Cafe (Cafe clicked on by User) from the DB and shows this
    info"""
    requested_cafe = db.session.get(Cafes, cafe_id)
    return render_template("cafe.html", cafe=requested_cafe)


@app.route("/add", methods=["GET", "POST"])
def add_cafe():
    """renders add.html, if form is filled out and submitted, gets data from user input and saves it as new Cafe in the
    DB, redirects to index.html"""
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafes(
            name=form.name.data,
            location=form.location.data,
            maps_url=form.maps_url.data,
            image_url=form.image_url.data,
            open=form.open.data.strftime("%I:%M%p"),
            close=form.close.data.strftime("%I:%M%p"),
            wifi=check_submit_fields(form.wifi.data),
            sockets=check_submit_fields(form.sockets.data),
            mountain_views=check_submit_fields(form.mountain_views.data))
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('show_overview'))
    else:
        return render_template('add.html', form=form)


@app.route("/all_cafes")
def show_all_cafes():
    """renders all_cafes.html and calls all Cafes saved in the DB and shows a detailed list of the Cafes """
    cafes = db.session.query(Cafes).all()
    return render_template("all_cafes.html", all_cafes=cafes)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """renders contact.html, shows a contact form, if submitted automatically sends an email to the creator of the
    website with the data from the form"""
    message_sent = None
    if request.method == "POST":
        data = request.form
        message = f'Name: {data["name"]}\nEmail: {data["email"]}\nPhone-Number: {data["phone"]}\nMessage: ' \
                  f'{data["message"]}'
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=USER, password=PASSWORD)
            connection.sendmail(from_addr=USER, to_addrs=USER,
                                msg=f'Subject: New Contact from Cafe&WiFi\n\n{message}')
        return render_template("contact.html", message_sent=True)
    else:
        return render_template("contact.html", message_sent=False)


if __name__ == "__main__":
    app.run(debug=True)
