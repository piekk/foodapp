import os
import uuid
from PIL import Image
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from foodapp import app, db, bcrypt, margin
from flask import render_template, request, url_for, redirect, flash, jsonify, json, session
from foodapp.forms import MerchantRegistrationForm, MerchantLoginForm, Profile, AddContact, ProductForm
from foodapp.forms import EditImageForm, EditPriceForm, EditDetailForm, EditStockForm
from foodapp.models import User, Products, Reviews
from flask_login import login_user, current_user, logout_user, login_required
from google.cloud import storage

app.config['BUCKET'] = 'foodappproducts'
app.config['IMAGE_STORED'] = "https://storage.googleapis.com/foodappproducts/"

@app.route('/')
def home():
    user = request.cookies.get('user')
    if user:
        return render_template("user.html", user=user)
    else:
        return render_template("home.html")
    #if user:
        #check db for cart
    #else:
        #do nothing


@app.route('/<brand>')
def dashboard(brand):
    if current_user.is_authenticated and current_user.username == brand:
        time = datetime.now()
        product = Products.query.filter_by(owner_id=current_user.id)
        return render_template("dashboard.html",brand=brand, product=product, time=time, image_stored = app.config['IMAGE_STORED'])
    else:
        current_brand = User.query.filter_by(username=brand).first()
        if current_brand:
            return render_template("view.html",brand=current_brand)
        else:
            return redirect(url_for('home'))

@app.route('/shop')
def shop():
    return render_template("shop.html")

@app.route('/articles/', defaults={'filter':None})
@app.route('/articles/<filter>')
def articles(filter):
    if filter == None:
        return render_template("articles.html")
    else:
        return render_template("articles.html", article=filter)

@app.route('/product')
def product():
    return render_template("product.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = MerchantRegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        phone = str(form.contact.data)
        time = datetime.now()
        try:
            db.session.add(User(firstname=form.firstname.data, lastname=form.lastname.data, username=form.username.data, email=form.email.data, password=hashed_pw, verified='no', contact=phone, role='Seller', date_register=time.strftime("%Y-%m-%d  %H:%M")))
            db.session.commit()
            user = User.query.filter_by(email=form.email.data).first()
            login_user(user)
            session.permanent = True
            return redirect(url_for('dashboard', brand=current_user.username))
        except:
            flash("Email  is already registered")
            return redirect(url_for('login'))
    elif current_user.is_authenticated:
        return redirect (url_for('home'))
    else:
        return render_template("register.html", title='', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = MerchantLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Seller':
            login_user(user)
            session.permanent = True
            return redirect(url_for('dashboard', brand=user.username))
        elif not user:
            flash("ไม่มีอีเมลล์ในระบบ")
            return redirect(url_for('login'))
        else:
            flash("พาสเวิร์ดไม่ถูกต้อง")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)

@app.route('/merchant/<name>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(name):
    form = Profile()
    user = User.query.filter_by(username=name).first()
    if current_user.role == 'Seller' and current_user.username == name:
        if request.method == 'POST' and form.validate():
            current_user.username = form.username.data
            current_user.email  = form.email.data
            try:
                db.session.commit()
                return redirect(url_for('dashboard', brand=current_user.username))
            except:
                flash("ข้อมูลไม่ถูกต้อง")
                return render_template("edit.html", form=form)
        elif request.method == 'POST':
            flash("ข้อมูลไม่ถูกต้อง")
            return render_template("edit.html", form=form)
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            return render_template("edit.html", form=form)
    elif current_user.role == 'admin':
        if request.method == 'POST' and form.validate():
            user.username = form.username.data
            user.email  = form.email.data
            db.session.commit()
            return redirect(url_for('dashboard', brand=current_user.username))
        elif request.method == 'GET':
            form.username.data = user.username
            form.email.data = user.email
            return render_template("edit.html", form=form)
    else:
        return redirect(url_for('home'))

@app.route('/merchant/<name>/contact', methods=['GET', 'POST'])
@login_required
def addcontact(name):
    form = AddContact()
    user = User.query.filter_by(username=name).first()
    if current_user.role == 'Seller' and current_user.username == name:
        if request.method == 'POST' and form.validate():
            current_user.alter_contact  = form.contact.data
            try:
                db.session.commit()
                return redirect(url_for('dashboard', brand=current_user.username))
            except:
                flash("ข้อมูลไม่ถูกต้อง")
                return redirect(url_for('addcontact', name=current_user.username))
        elif request.method == 'POST':
            flash("ข้อมูลไม่ถูกต้อง")
            return redirect(url_for('addcontact', name=current_user.username))
        elif request.method == 'GET':
            form.contact.data = current_user.alter_contact
            return render_template("addcontact.html", form=form)
    elif current_user.role == 'admin':
        if request.method == 'POST' and form.validate():
            current_user.alter_contact  = form.contact.data
            try:
                db.session.commit()
                return redirect(url_for('dashboard', brand=current_user.username))
            except:
                flash("ข้อมูลไม่ถูกต้อง")
                return redirect(url_for('addcontact', name=user.username))
        elif request.method == 'POST':
            flash("ข้อมูลไม่ถูกต้อง")
            return redirect(url_for('addcontact', name=user.username))
        elif request.method == 'GET':
            form.contact.data = user.alter_contact
            return render_template("addcontact.html", form=form)
    else:
        return redirect(url_for('home'))



def save_picture_local(form_picture,name,filetype):
    picture_fn = name + '.jpg'
    picture_path = os.path.join(app.root_path, 'static/products/'+ filetype + '/' + picture_fn)
    output_size = (1000,1000)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    path = 'product/'+filetype+'/'+picture_fn
    return path


def save_picture(form_picture,name,filetype):
    picture_fn = secure_filename(name + '.jpg')
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    output_size = (1000,1000)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(app.config['BUCKET'])
    blob = bucket.blob('products/'+filetype+'/'+picture_fn)
    blob.upload_from_filename(picture_path)

    return picture_path

def delete_blob(blob_name):
    bucket_name = app.config['BUCKET']
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    return blob_name


@app.route('/merchant/product', methods=['GET', 'POST'])
@login_required
def addproduct():
    form = ProductForm()
    if current_user.role == 'Seller' and current_user.verified == 'y':
        if form.validate_on_submit():
            name = str(current_user.id) + 'ID'+uuid.uuid4().hex[:6]
            category = form.category.data
            filename = 'products/'+category+'/'+ secure_filename(name+'.jpg')
            productcode = form.title.data + str(current_user.id)
            keyword = form.tag.data.lower()
            time = datetime.now()
            noofdays = form.promotion_expire.data
            promotion_expiry_date = datetime.now() + timedelta(days=noofdays)
            expire_on = promotion_expiry_date.strftime("%Y-%m-%d")
            try:
                save_picture_local(form.photo1.data, name, category)
                db.session.add(Products(productcode=productcode, date_add=time.strftime("%Y-%m-%d, %H:%M"),
                                        title=form.title.data, price=form.price.data, shipping_fee=form.shipping_fee.data,
                                        imgfile1=filename, quantity=form.quantity.data, category=category, promotion=form.promotion.data,
                                        promotion_expire=expire_on, tag=keyword, description=form.description.data, owner_product=current_user))
                db.session.commit()
                return redirect(url_for('dashboard', brand=current_user.username))
            except:
                delete_blob(filename)
                flash("unsuccess")
                return redirect(url_for('addproduct'))
        else:
            return render_template("addproduct.html", form=form, margin=margin)
    elif current_user.role == 'Seller' and current_user.verified == 'no':
        return render_template("addproduct.html", form=form, margin=margin)
    else:
        return redirect(url_for('home'))

@app.route('/merchant/product/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_product(name):
    time = datetime.now()
    product=Products.query.filter_by(productcode=name).first()
    if current_user.id == product.owner_id:
        in_cart = False
        #in_cart = CartItems.query.filter(CartItems.product == product.productcode).first()
        if in_cart:
            message = "มีสินค้าอยู่ในตะกร้าสินค้าของผู้ซื้อ ไม่สามารถเปลี่ยนข้อมูลสินค้านี้ได้"
            return render_template("editproduct.html", time=time,  product=product, margin=margin, message=message, image_stored = app.config['IMAGE_STORED'])
        else:
            return render_template("editproduct.html", time=time, product=product, margin=margin, image_stored = app.config['IMAGE_STORED'])
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/image/<name>')
@login_required
def update_image(name):
    product=Products.query.filter_by(productcode=name).first()
    if product.owner_id == current_user.id:
        return render_template("updateimage.html", product=product, image_stored = app.config['IMAGE_STORED'])
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/image/<name>/<file>', methods=['GET', 'POST'])
@login_required
def update_imagefile(name,file):
    product=Products.query.filter_by(productcode=name).first()
    form = EditImageForm()
    if form.validate_on_submit():
        name = str(current_user.id) + 'ID'+uuid.uuid4().hex[:6]
        category = product.category
        filename = 'products/'+category+'/'+ secure_filename(name+'.jpg')
        try:
            save_picture_local(form.image.data, name, category)
            return render_template('test.html', filename =filename)
        except:
            return "incomplete"
    elif request.method == 'GET' and product.owner_id == current_user.id:
        #in_cart = CartItems.query.filter(CartItems.product == name).first()
        in_cart = False
        if in_cart:
            return redirect(url_for('edit_product', name=product.productcode))
        elif file in {'1','2','3','4'}:
            if file == '1':
                filename = product.imgfile1
            elif file == '2':
                filename = product.imgfile2
            elif file == '3':
                filename = product.imgfile3
            elif file == '4':
                    filename = product.imgfile4
            return render_template("updateimagefile.html", form=form, product=product, filename=filename, image_stored = app.config['IMAGE_STORED'])
        else:
            return redirect(url_for('update_image', name=name))
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
