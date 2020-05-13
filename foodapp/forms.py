from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, InputRequired
from werkzeug.utils import secure_filename
from foodapp.models import User
from foodapp.list import province_list, category_list
from flask_login import current_user
from foodapp import app




def check_contact(form, field):
    phone = str(form.contact.data)
    contact = User.query.filter_by(contact=form.contact.data).first()
    if len(phone) != 10 or phone.isnumeric()==False:
        raise ValidationError('Invalid Phone number')
    elif contact:
        raise ValidationError('Phone number already registered')



def check_validcontact(form, field):
    phone = str(form.contact.data)
    if phone.isnumeric()==False:
        raise ValidationError('invalid number')

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
    photo2 = FileField('Add More', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    photo3 = FileField('Add More', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    photo4 = FileField('Add More', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    price = StringField('Price', id="pr-set", validators=[DataRequired(), check_num])
    shipping_fee = StringField('Shipping', id="ship-set", default=0, validators=[DataRequired(), check_num])
    promotion = IntegerField('Promotion', id="discount-set", default = 0)
    promotion_expire = IntegerField('Promotion Expire', default=90)
    category = SelectField('Category', id="category", choices= category_list)
    quantity = IntegerField('Inventory', default = 0)
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
    title = StringField('Title', validators=[DataRequired()])
    tag = StringField('Tag')
    description = TextAreaField('New Description')
    submit = SubmitField('ยืนยัน')

class EditStockForm(FlaskForm):
    quantity = IntegerField('Inventory', validators=[InputRequired()])
    submit = SubmitField('ยืนยัน')



class MerchantRegistrationForm(FlaskForm):
    firstname = StringField('ชื่อจริง', validators=[DataRequired()])
    lastname = StringField('นามสกุล', validators=[DataRequired()])
    username = StringField('ชื่อแบรนด์', validators=[DataRequired(),
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
    submit = SubmitField('สมัครสมาชิก')



class MerchantLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('เข้าสู่ระบบ')


class ChangeProfile(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                        check_username])
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message=('not a valid email address')),
                                             check_email])
    submit = SubmitField('Submit')

class AddContact(FlaskForm):
    contact = StringField('เบอร์ติดต่อสำรอง', validators=[DataRequired(),
                                             check_contact])
    submit = SubmitField('ยืนยัน')


class CheckoutContact(FlaskForm):
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired(),
                                             check_validcontact])
    submit = SubmitField('ยืนยัน')


class TrackingForm(FlaskForm):
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired()])
    reference = StringField('รหัสการสั่งซื้อ',  validators=[DataRequired()])
    submit = SubmitField('ยืนยัน')


class Password_change(FlaskForm):
    otp = StringField('รหัสยืนยันตัวตน', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(),
                                                         Length(min=6, max=12,
                                                         message=('use password between 6-12 characters'))])
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(),
                                                             EqualTo('new_password',
                                                             message=('password not match'))])
    submit = SubmitField('ยืนยัน')

class Reset_Pass(FlaskForm):
    email = StringField('อีเมลล์', validators=[DataRequired(),
                                             Email(message=('not a valid email address'))])
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired()])
    submit = SubmitField('ยืนยัน')

class Ship_Address(FlaskForm):
    firstname = StringField('ชื่อ', validators=[DataRequired()])
    lastname = StringField('นามสกุล', validators=[DataRequired()])
    contact = StringField('เบอร์ติดต่อ', validators=[DataRequired()])
    homeaddress = StringField('บ้านเลขที่', validators=[DataRequired()])
    housename = StringField('หมู่บ้าน/คอนโด')
    street = StringField('ถนน')
    substreet = StringField('ซอย')
    subdistrict = StringField('แขวง/ตำบล', validators=[DataRequired()])
    district = StringField('เขต/อำเภอ', validators=[DataRequired()])
    province = SelectField('จังหวัด', choices=province_list)
    postcode = IntegerField('รหัสไปรษณีย์', validators=[DataRequired()])
    make_mainaddress = BooleanField('จดจำเป็นที่อยู่หลักในการสั่งซื้อครั้งต่อไป')
    submit = SubmitField('ยืนยัน')

class ConfirmShipmentForm(FlaskForm):
    message = StringField('ส่งข้อความขอบคุณลูกค้า')
    submit = SubmitField('ยืนยันการส่งสินค้า')

class ShopProfile(FlaskForm):
    title = StringField('ข้อความแนะนำตัวสั้นๆ', validators=[DataRequired()])
    content = TextAreaField('แนะนำสินค้าที่คุณขาย', validators=[DataRequired()])
    submit = SubmitField('ยืนยัน')

class ImageProfile(FlaskForm):
    img = FileField('รูปกิจการ', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('ยืนยัน')

class IconProfile(FlaskForm):
    icon = FileField('รูปโลโกร้านถ้ามี', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('ยืนยัน')
