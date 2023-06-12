from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TimeField, SelectField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField

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


class CommentForm(FlaskForm):
    user_name = StringField('Name', validators=[DataRequired()])
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
