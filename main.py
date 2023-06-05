from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TimeField
from wtforms.validators import DataRequired, URL

app = Flask(__name__)
Bootstrap(app)

# ---------------------------- DATABASE SETUP ------------------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes-banff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "placeholder"
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


# with app.app_context():
#     db.create_all()
#     new_cafe = Cafes(
#         name="Good Earth Coffeehouse",
#         location="333 Banff Ave, Banff, AB T1L 1B1",
#         maps_url="https://goo.gl/maps/3YNCm4gDQgQt6Tb56",
#         image_url="https://streetviewpixels-pa.googleapis.com/v1/thumbnail?panoid=NJ_yR1AWRbxE7AdpKsLxeg&cb_client=search.gws-prod.gps&yaw=12.557711&pitch=0&thumbfov=100&w=80&h=80",
#         open="06:30AM",
#         close="07:00PM",
#         wifi=1,
#         mountain_views=1)
#     db.session.add(new_cafe)
#     db.session.commit()

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


def check_submit_fields(option):
    if option == "Yes":
        return 1
    elif option == "No":
        return 0
    else:
        pass


@app.route("/")
def show_all_cafes():
    cafes = db.session.query(Cafes).all()
    return render_template("index.html", all_cafes=cafes)


@app.route("/cafe/<int:cafe_id>")
def show_cafe(cafe_id):
    requested_cafe = db.session.get(Cafes, cafe_id)
    return render_template("cafe.html", cafe=requested_cafe)


@app.route("/add", methods=["GET", "POST"])
def add_cafe():
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
        return redirect(url_for('show_all_cafes'))
    else:
        return render_template('add.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)
