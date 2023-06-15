from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import os
from sqlalchemy.orm import relationship
from datetime import date
from functools import wraps

from forms import CafeForm, ReviewForm, SignUpForm, LoginForm

# set info for smtp as environmental variable to keep safe
USER = os.environ["USER"]
PASSWORD = os.environ["PASSWORD"]

# ---------------------------- START FLASK FRAMEWORK ------------------------------- #
app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
login_manager = LoginManager()
login_manager.init_app(app)

# ---------------------------- CONNECT TO DATABASE ------------------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes-banff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ---------------------------- SETUP LOGIN-MANAGER------------------------------- #
@login_manager.user_loader
def load_user(id):
    return db.session.get(Users, id)


# ---------------------------- DATABASE SETUP ------------------------------- #
class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    reviews = relationship("Reviews", back_populates="review_author")


class Cafes(db.Model):
    __tablename__ = "cafes"
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
    reviews = relationship("Reviews", back_populates="parent_cafe")

    def __repr__(self):
        """returns name of Cafe when printed instead of <Cafes ID>"""
        return f"<Cafe> {self.name}"

    def to_dict(self):
        """converts DB-row Object to Dictionary"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Reviews(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_author = relationship("Users", back_populates="reviews")
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id"))
    parent_cafe = relationship("Cafes", back_populates="reviews")
    date = db.Column(db.String(250), nullable=False)
    text = db.Column(db.Text, nullable=False)


# # only run the first time to create DBs
# with app.app_context():
#     db.create_all()
#     new_cafe = Cafes(
#         name="Good Earth Coffee House",
#         location="333 Banff Ave, Banff, AB T1L 1B1",
#         maps_url="https://goo.gl/maps/aVTe7x2hdw4iu3NX7",
#         image_url="https://lh5.googleusercontent.com/p/AF1QipMMgkOZNGreHF6na3qtMDInvNj_IY_VhCJ1MbRE=w408-h306-k-no",
#         open="06:30AM",
#         close="09:00PM",
#         wifi=1,
#         sockets=1,
#         mountain_views=1)
#     db.session.add(new_cafe)
#     db.session.commit()


# ---------------------------- CREATE FUNCTIONS ------------------------------- #
def admin_only(f):
    """creates decorator that checks if the current_user.id equals 1, carries on with functions if it is, if not,
    returns an error page with the HTTP code 403"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        else:
            return f(*args, **kwargs)
    return decorated_function


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
    return render_template('index.html', all_cafes=cafes)


@app.route('/sign-up', methods=["GET", "POST"])
def sign_up():
    """renders sign-up.html, with SignUpForm, checks if submitted email address already exists in Users DB, if so,
    redirects to login page, if not, saves user data in Users DB and redirects to homepage"""
    form = SignUpForm()
    if form.validate_on_submit():
        if Users.query.filter_by(email=form.email.data).first():
            flash("This email already exists, please login")
            return redirect(url_for('login'))
        else:
            password = form.password.data
            # hash and salt password
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)
            new_user = Users(
                email=form.email.data,
                password=hashed_password,
                name=form.name.data
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('show_overview'))
    return render_template('sign-up.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """renders login.html, with LoginForm, checks if submitted email address exists in Users DB and password is
    matching, if so, redirects to Homepage, if not, redirects to sign-up.html"""
    form = LoginForm()
    if form.validate_on_submit():
        user_email = form.email.data
        user_password = form.password.data
        user = Users.query.filter_by(email=user_email).first()
        if user is None:
            flash("Sorry, this email doesn't exist, please register first.")
            return redirect(url_for('sign_up'))
        else:
            if check_password_hash(user.password, user_password):
                login_user(user)
                return redirect(url_for('show_overview'))
            else:
                flash("Sorry, wrong password, please try again!")
                return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """logs out user"""
    logout_user()
    return redirect(url_for('show_overview'))


@app.route("/cafe/<int:cafe_id>", methods=["GET", "POST"])
def show_cafe(cafe_id):
    """renders cafe.html, calls the data of the requested Cafe (Cafe clicked on by User) from the DB and shows this
    info, shows reviews, gives option of submitting review, when signed in """
    requested_cafe = db.session.get(Cafes, cafe_id)
    form = ReviewForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            new_review = Reviews(
                review_author=current_user,
                date=date.today().strftime("%B %d, %Y"),
                text=form.review_text.data,
                parent_cafe=requested_cafe
            )
            db.session.add(new_review)
            db.session.commit()
        else:
            flash("You need to login or register to submit a review.")
            return redirect(url_for("login"))
    return render_template('cafe.html', cafe=requested_cafe, form=form)


@app.route("/add", methods=["GET", "POST"])
@login_required
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
    return render_template('all_cafes.html', all_cafes=cafes)


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
    """renders update-cafe.html"""
    return render_template("update-cafe.html")


@app.route("/delete/<int:cafe_id>")
@admin_only
def delete_cafe(cafe_id):
    """finds current Cafe in DB and deletes it off DB, redirects to Homepage"""
    cafe_to_delete = db.session.get(Cafes, cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('show_overview'))


@app.route("/delete-review/<int:review_id>")
@admin_only
def delete_review(review_id):
    """finds requested review by ID and deletes it from DB"""
    review_to_delete = db.session.get(Reviews, review_id)
    cafe_id = review_to_delete.cafe_id
    db.session.delete(review_to_delete)
    db.session.commit()
    return redirect(url_for('show_cafe', cafe_id=cafe_id))


@app.route("/show-users")
@admin_only
def show_users():
    """renders users.html, calls all users from DB and renders info in a table"""
    users = db.session.query(Users).all()
    return render_template('users.html', all_users=users)


@app.route("/delete-user/<int:user_id>")
@admin_only
def delete_user(user_id):
    """finds requested user and deletes it off the DB"""
    user_to_delete = db.session.get(Users, user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    return redirect(url_for('show_users'))


@app.route("/show-reviews/<int:user_id>")
@admin_only
def show_user_reviews(user_id):
    """renders user-reviews.html, finds all reviews in DB left by requested user and renders table with infos"""
    requested_user = db.session.get(Users, user_id)
    return render_template('user-reviews.html', user=requested_user)


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
    """gets data from requested Cafes Object and changes close attribute, returns 200 HTTP Code with 'success'
    message or returns 404 HTTP Code with error message 'Not found' if requested Cafes Object does not exist"""
    cafe_to_update = Cafes.query.get(cafe_id)
    if cafe_to_update:
        cafe_to_update.close = request.args.get("close")
        db.session.commit()
        return jsonify({"Success": "You successfully updated the closing time."}), 200
    else:
        return jsonify(error={"Not found": "The cafe you are looking for doesn't exist."}), 404


# ---HTTP DELETE - Delete Record--- #
@app.route("/report-closed/<cafe_id>", methods=["DELETE"])
def delete_cafe_api(cafe_id):
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
