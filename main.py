from flask import Flask, render_template, redirect, url_for, request, jsonify
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

    def __repr__(self):
        """returns name of Cafe when printed instead of <Cafes ID>"""
        return f"<Cafe> {self.name}"

    def to_dict(self):
        """converts DB-row Object to Dictionary"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


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


@app.route("/update-cafe")
def update_cafe():
    return render_template("update-cafe.html")



# ---------------------------- CREATE RESTful API ------------------------------- #
# ---HTTP GET - Read Record(s)--- #
@app.route("/get_all_cafes")
def get_all_cafes():
    """gets all Cafes Objects from DB and returns the Cafes Objects as JSON Objects"""
    all_cafes = db.session.query(Cafes).all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


@app.route("/search_cafe")
def get_cafe_by_name():
    """searches DB for a Cafes Object with a specific name and returns the Cafe Object as JSON Object, if no Cafes
    Object is found, returns error 'Not found' message"""
    query_name = request.args.get("name")
    cafe = db.session.query(Cafes).filter_by(name=query_name).first()
    if cafe:
        return jsonify(cafe=cafe.to_dict())
    else:
        return jsonify(error={"Not found": "Sorry, we don't have a cafe with that name."})


# ---HTTP POST - Create Record(s)--- #
@app.route("/add-api", methods=["POST"])
def add_api_new_cafe():
    """takes user JSON input and saves it as Cafes Object to DB, returns response 'success' message"""
    new_cafe = Cafes(
        name=request.form.get("name"),
        location=request.form.get("location"),
        maps_url=request.form.get("maps_url"),
        image_url=request.form.get("image_url"),
        open=request.form.get("open"),
        close=request.form.get("close"),
        wifi=bool(request.form.get("wifi")),
        sockets=bool(request.form.get("sockets")),
        mountain_views=bool(request.form.get("mountain_views"))
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added a new cafe"})


# ---HTTP PATCH - Update Record--- #
@app.route("/update-open/<cafe_id>", methods=["PATCH"])
def update_open(cafe_id):
    """gets data from requested Cafes Object and changes open attribute, returns 200 HTTP Code with 'success' message or
    returns 404 HTTP Code with error message 'Not found' if requested Cafes Object does not exist"""
    cafe_to_update = Cafes.query.get(cafe_id)
    if cafe_to_update:
        cafe_to_update.open = request.args.get("open")
        db.session.commit()
        return jsonify({"Success": "You successfully updated the opening time."}), 200
    else:
        return jsonify(error={"Not found": "The cafe you are looking for doesn't exist."}), 404


@app.route("/update-close/<cafe_id>", methods=["PATCH"])
def update_close(cafe_id):
    """gets data from requested Cafes Object and changes close attribute, returns 200 HTTP Code with 'success' message or
    returns 404 HTTP Code with error message 'Not found' if requested Cafes Object does not exist"""
    cafe_to_update = Cafes.query.get(cafe_id)
    if cafe_to_update:
        cafe_to_update.close = request.args.get("close")
        db.session.commit()
        return jsonify({"Success": "You successfully updated the closing time."}), 200
    else:
        return jsonify(error={"Not found": "The cafe you are looking for doesn't exist."}), 404


# ---HTTP DELETE - Delete Record--- #
@app.route("/report-closed/<cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    """checks if user has the API key, returns HTTP Code 403 and error message 'Forbidden' if not, if API key is valid,
     deletes requested Cafes Object from DB and returns 200 HTTP Code and success message, returns 404 HTTP Code and
     error 'Not found' message if requested Cafes Object does not exist."""
    if request.args.get("api_key") == "TopSecretAPIKey":
        cafe_to_delete = Cafes.query.get(cafe_id)
        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return jsonify(success={"Success": "You successfully reported the cafe as closed."}), 200
        else:
            return jsonify(error={"Not found": "The cafe you are looking for doesn't exist."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed, make sure you have the right api-key."}), 403







if __name__ == "__main__":
    app.run(debug=True)
