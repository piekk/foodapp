from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.utils import secure_filename
from flask_login import current_user


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
        if len(form.username.data) < 3 or len(form.username.data) > 12:
            raise ValidationError('Please choose a username between 3-12 characters')
        elif user:
            raise ValidationError('Username taken')

def check_name(form, field):
    user = User.query.filter_by(username=form.username.data).first()
    if len(form.username.data) < 3 or len(form.username.data) > 12:
        raise ValidationError('Please choose a username between 3-12 characters')
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
    category = SelectField('Category', id="category", choices=[('illustration', 'ภาพคอมพิวเตอร์กราฟิก อิลัสเตรชัน'),('photograph', 'ภาพถ่าย'),('painting','ภาพเขียน งานปรินท์ภาพเขียน'),('prop','ของแต่งบ้าน'),('book','หนังสือและนิตยสารศิลปะ')])
    quantity = SelectField('Inventory', choices=[('1', '1'),('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')])
    style = StringField('Tag', validators=[DataRequired()])
    size = StringField('Size')
    object_size = StringField('Size')
    frame = StringField('Frame', id="addframe")
    condition = SelectField('Condition', choices=[('New', 'ของใหม่'),('Vintage','ของ Vintage'),('NewVintage','ของใหม่สไตล์ vintage')])
    book_condition = SelectField('book_condition', choices=[('New', 'หนังสือใหม่'),('Secondhand','หนังสือมือสอง'),('Collectable','หนังสือสะสมหายาก')])
    authors = StringField('Authors', id="addauthor")
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

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                        Length(min=3, max=12,
                                        message=('username minimum 3 characters')),
                                        check_name])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address'))])
    contact = StringField('Contact Number', validators=[DataRequired(),check_contact])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=6, max=12,
                                                     message=('use password between 6-12 characters'))])
    confirm_password = PasswordField('Confirm Password',[DataRequired(),
                                                         EqualTo('password',
                                                         message=('password not match'))])
    accept_terms = BooleanField(validators=[DataRequired()])
    submit = SubmitField('Register Now')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address'))])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class MerchantRegistrationForm(FlaskForm):
    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(),
                                        check_name])
    contact = StringField('Contact Number', validators=[DataRequired(),
                                             check_contact])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address'))])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(min=6, max=12,
                                                     message=('use password between 6-12 characters'))])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),
                                                         EqualTo('password',
                                                         message=('password not match'))])
    accept_terms = BooleanField(validators=[DataRequired()])
    submit = SubmitField('Register Now')

class ChangeStatusForm(FlaskForm):
    firstname = StringField('Firstname', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    accept_terms = BooleanField(validators=[DataRequired()])
    submit = SubmitField('Confirm Change')

class MerchantLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Seller Login')


class Profile(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                        check_username])
    contact = StringField('Contact Number', validators=[DataRequired(),
                                             check_contact])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address')),
                                             check_email])
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
