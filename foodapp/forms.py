from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.utils import secure_filename
from foodapp.models import User
from flask_login import current_user
from foodapp import app


def check_contact(form, field):
    phone = str(form.contact.data)
    contact = User.query.filter_by(contact=form.contact.data).first()
    if len(phone) != 10 or phone.isnumeric()==False:
        raise ValidationError('Invalid Phone number')
    elif contact:
        raise ValidationError('Phone number already registered')

def check_num(form, field):
    num = str(field.data)
    if num.isnumeric()==False:
        raise ValidationError('Invalid Number')

def check_username(form, field):
    if form.username.data != current_user.username:
        user = User.query.filter_by(username=form.username.data).first()
        if len(form.username.data) < 3 or len(form.username.data) > 22:
            raise ValidationError('Please choose a username between 3-22 characters')
        elif user:
            raise ValidationError('Username taken')

def check_name(form, field):
    user = User.query.filter_by(username=form.username.data).first()
    if len(form.username.data) < 3 or len(form.username.data) > 22:
        raise ValidationError('Please choose a username between 3-22 characters')
    elif user:
        raise ValidationError('Username taken')


def check_email(form, field):
    if form.email.data != current_user.email:
        user = User.query.filter_by(username=form.email.data).first()
        if user:
            raise ValidationError('The email is taken')


class ProductForm(FlaskForm):
    title = StringField('Title', id="producttitle", validators=[DataRequired()])
    photo1 = FileField('Add Main Photo', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'])])
    photo2 = FileField('Add More', validators=[FileAllowed(['jpg'])])
    photo3 = FileField('Add More', validators=[FileAllowed(['jpg'])])
    photo4 = FileField('Add More', validators=[FileAllowed(['jpg'])])
    price = StringField('Price', id="pr-set", validators=[DataRequired(), check_num])
    shipping_fee = StringField('Shipping', id="ship-set", default=0, validators=[DataRequired(), check_num])
    promotion = IntegerField('Promotion', id="discount-set", default = 0)
    promotion_expire = IntegerField('Promotion Expire', default=90)
    category = SelectField('Category', id="category", choices=[(app.config['CATEGORY_1'], app.config['CAT_1']),(app.config['CATEGORY_2'], app.config['CAT_2']),(app.config['CATEGORY_3'],app.config['CAT_3'])])
    quantity = IntegerField('Inventory', default=1)
    tag = StringField('Tag', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('สร้างสินค้า')


class EditImageForm(FlaskForm):
    image  = FileField('Add Main Photo', validators=[FileRequired(), FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('ยืนยัน')

class EditPriceForm(FlaskForm):
    price = StringField('Price', validators=[DataRequired(), check_num])
    shipping_fee = StringField('Shipping', default=0, validators=[DataRequired(), check_num])
    promotion = IntegerField('Promotion', default = 0)
    promotion_expire = IntegerField('Promotion Expire', default=90)
    submit = SubmitField('ยืนยัน')

class EditDetailForm(FlaskForm):
    frame = StringField('Frame')
    tag = StringField('Tag')
    size = StringField('Size')
    description = TextAreaField('New Description')
    submit = SubmitField('ยืนยัน')

class EditStockForm(FlaskForm):
    quantity = SelectField('Inventory', choices=[('0', '0'),('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')])
    submit = SubmitField('ยืนยัน')



class MerchantRegistrationForm(FlaskForm):
    firstname = StringField('ชื่อจริง', validators=[DataRequired()])
    lastname = StringField('นามสกุล', validators=[DataRequired()])
    username = StringField('ชื่อผู้ใช้', validators=[DataRequired(),
                                        check_name])
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired(),
                                             check_contact])
    email = StringField('อีเมลล์', validators=[DataRequired(),
                                             Email(message=('not a valid email address'))])
    password = PasswordField('พาสเวิร์ด', validators=[DataRequired(),
                                                     Length(min=6, max=12,
                                                     message=('use password between 6-12 characters'))])
    confirm_password = PasswordField('ยืนยันพาสเวิร์ด',validators=[DataRequired(),
                                                         EqualTo('password',
                                                         message=('password not match'))])
    accept_terms = BooleanField('ยอมรับข้อตกลงในการใช้งาน', validators=[DataRequired()])
    submit = SubmitField('สมัครสมาชิก')



class MerchantLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('เข้าสู่ระบบ')


class Profile(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                        check_username])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address')),
                                             check_email])
    submit = SubmitField('Submit')

class AddContact(FlaskForm):
    contact = StringField('เบอร์ติดต่อสำรอง', validators=[DataRequired(),
                                             check_contact])
    submit = SubmitField('Submit')


class Password_change(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(),
                                                         Length(min=6, max=12,
                                                         message=('use password between 6-12 characters'))])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),
                                                             EqualTo('new_password',
                                                             message=('password not match'))])
    submit = SubmitField('Submit')

class Ship_Address(FlaskForm):
    fullname = StringField('ชื่อและนามสกุล', validators=[DataRequired()])
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired()])
    homeaddress = StringField('บ้านเลขที่', validators=[DataRequired()])
    housename = StringField('หมู่บ้าน/คอนโด')
    street = StringField('ถนน')
    substreet = StringField('ซอย')
    subdistrict = StringField('แขวง/ตำบล', validators=[DataRequired()])
    district = StringField('เขต/อำเภอ', validators=[DataRequired()])
    province = StringField('จังหวัด', validators=[DataRequired()])
    postcode = IntegerField('รหัสไปรษณีย์', validators=[DataRequired()])
    submit = SubmitField('ยืนยัน')

class ChoosePayment(FlaskForm):
    submit = SubmitField('confirm')
