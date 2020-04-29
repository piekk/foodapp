import os
import uuid
import nexmo
from PIL import Image
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from foodapp import app, db, bcrypt, margin
from flask import render_template, request, url_for, redirect, flash, jsonify, json, session, make_response
from foodapp.forms import MerchantRegistrationForm, MerchantLoginForm, Profile, AddContact, ProductForm
from foodapp.forms import EditImageForm, EditPriceForm, EditDetailForm, EditStockForm, CheckoutContact, TrackingForm
from foodapp.models import User, Products, Reviews, Cookie, Cart, CartItems, Checkout, CheckoutItems
from flask_login import login_user, current_user, logout_user, login_required
from google.cloud import storage


app.config['BUCKET'] = 'foodappproducts'
app.config['IMAGE_STORED'] = "https://storage.googleapis.com/foodappproducts/"
app.config['PROFILE_IMAGE'] = "https://storage.googleapis.com/seller_profile/"
pagename = "farmer diary"

NEXMO_API_KEY = 'ad2030ed'
NEXMO_API_SECRET = 'lo8NT1TNj6UsHz8u'



def redirect_url(default='home'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


#helper function to set cookie
@app.before_request
def before_request_func():
    user = request.cookies.get('cook_id')
    # redirect to repeat route so will not return resp and redirect back to seelf
    if not user:
        id = uuid.uuid4().hex[:12]
        resp = make_response(redirect('/repeat'))
        resp.set_cookie("cook_id", id, max_age=60*60*24*30)
        return resp
    else:
        cook = Cookie.query.filter_by(cook_id = user).first()
        if cook:
            print("")
        else:
            db.session.add(Cookie(cook_id = user))
            db.session.commit()
            print("")

def create_cart(ref):
    timecreate = datetime.now().strftime("%Y-%m-%d  %H:%M")
    expire = datetime.now() + timedelta(days=30)
    timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
    db.session.add(Cart(cartcode=ref.cook_id, date_create=timecreate, date_expire=timeexpire,cartowner=ref))
    db.session.commit()
    pass

#check for promotion return boolean
def check_promotion(p_insert):
    time = datetime.now()
    return int(p_insert.promotion)> 0 and time < p_insert.promotion_expire


#helper function to redirect to previous page
@app.route('/repeat')
def repeat():
    return redirect(redirect_url())


@app.route('/', methods=['GET', 'POST'])
def home():
    latest = Products.query.filter(Products.quantity>=0).order_by(Products.date_add.desc()).limit(12).all()
    time = datetime.now()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    if request.method == 'POST':
        # create cart if there is no cart
        if not cook.cart:
            create_cart(cook)
            pass
        additem = request.form.get('addtocart')
        cart = Cart.query.filter_by(cartcode=cook.cook_id).first()
        # check if additem is in the cart
        listofitem = [item.product for item in cart.items]
        if str(additem) not in listofitem:
            product = Products.query.get(additem)
            product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee) if check_promotion(product) else round(int(product.price)*margin)+int(product.shipping_fee)
            db.session.add(CartItems(product = product.id, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
        return redirect(redirect_url())
    else:
        return render_template("home.html", latest=latest, title = pagename, margin=margin, image_stored = app.config['IMAGE_STORED'], cook =cook)


@app.route('/<brand>', methods=['GET', 'POST'])
def dashboard(brand):
    time = datetime.now()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    if request.method == 'POST':
        if not cook.cart:
            create_cart(cook)
            pass
        additem = request.form.get('addtocart')
        cart = Cart.query.filter_by(cartcode=cook.cook_id).first()
        # check if additem is in the cart
        listofitem = [item.product for item in cart.items]
        if str(additem) not in listofitem:
            product = Products.query.get(additem)
            product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee) if check_promotion(product) else round(int(product.price)*margin)+int(product.shipping_fee)
            db.session.add(CartItems(product = product.id, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
        return redirect(redirect_url())
    elif request.method == 'GET' and current_user.is_authenticated and current_user.username == brand:
        time = datetime.now()
        product = Products.query.filter_by(owner_id=current_user.id)
        return render_template("dashboard.html",brand=brand, product=product, time=time, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        current_brand = User.query.filter_by(username=brand).first()
        if current_brand:
            return render_template("view.html", brand=current_brand, margin=margin, title = current_brand.username, time = time, image_stored = app.config['IMAGE_STORED'], seller_profile = app.config['PROFILE_IMAGE'], cook =cook)
        else:
            return redirect(url_for('home'))


@app.route('/shop/', defaults={'filter':None}, methods=['GET', 'POST'])
@app.route('/shop/<filter>', methods=['GET', 'POST'])
def shop(filter):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    page = request.args.get('page', 1,type=int)
    productcategory = [app.config['CATEGORY_1'], app.config['CATEGORY_2'], app.config['CATEGORY_3'], app.config['CATEGORY_4'], app.config['CATEGORY_5']]
    if request.method == 'POST':
        if not cook.cart:
            create_cart(cook)
            pass
        additem = request.form.get('addtocart')
        cart = Cart.query.filter_by(cartcode=cook.cook_id).first()
        # check if additem is in the cart
        listofitem = [item.product for item in cart.items]
        if str(additem) not in listofitem:
            product = Products.query.get(additem)
            product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee) if check_promotion(product) else round(int(product.price)*margin)+int(product.shipping_fee)
            db.session.add(CartItems(product = product.id, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
        return redirect(redirect_url())
    elif request.method == 'GET' and filter == None:
        time = datetime.now()
        product = Products.query.order_by(Products.view.desc()).paginate(per_page=16, page=page)
        return render_template("shop.html", title="shop", product = product, margin=margin, time=time, filter='shop', image_stored = app.config['IMAGE_STORED'], cook =cook)
    elif request.method == 'GET' and filter in productcategory:
        time = datetime.now()
        product = Products.query.filter(Products.category==filter).paginate(per_page=16, page=page)
        return render_template("shop.html", title="shop", product = product, margin=margin, time=time, filter=filter, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        time = datetime.now()
        fil = secure_filename(filter)
        searchwordlower = fil.lower()
        searchword = searchwordlower.replace(" ","")
        product = Products.query.filter(Products.tag.contains(searchword)).paginate(per_page=16, page=page)
        return render_template("shop.html", title=pagename+"ร้านค้า"+filter, product = product, margin=margin, time=time, filter=filter, image_stored = app.config['IMAGE_STORED'], cook =cook)


@app.route('/product/<product>', methods=['GET', 'POST'])
def product(product):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    time = datetime.now()
    product = Products.query.get(product)
    time = datetime.now()
    if request.method == 'POST':
        if not cook.cart:
            create_cart(cook)
            pass
        additem = request.form.get('addtocart')
        cart = Cart.query.filter_by(cartcode=cook.cook_id).first()
        # check if additem is in the cart
        listofitem = [item.product for item in cart.items]
        if str(additem) not in listofitem:
            product = Products.query.get(additem)
            product_price = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee) if check_promotion(product) else round(int(product.price)*margin)+int(product.shipping_fee)
            db.session.add(CartItems(product = product.id, img=product.imgfile1, quantity=1, price=product_price, seller=product.owner_product.username, cart=cart))
            db.session.commit()
        return redirect(redirect_url())
    elif request.method == 'GET' and product:
        return render_template("product.html", product = product, title=pagename+product.title, time=time, margin=margin, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect(url_for('home'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    time = datetime.now()
    if request.method=='POST':
        if 'todelete' in request.form:
            todelete = request.form.get('todelete')
            delete = CartItems.query.get(todelete)
            db.session.delete(delete)
            db.session.commit()
            return redirect(url_for('cart'))
        elif 'checkout' in request.form:
            return redirect(url_for('checkout'))
    elif request.method == 'GET':
        if cook.cart:
            cart = cook.cart
            product_inventory = {}
            price = {}
            product_title = {}
            for item in cart.items:
                product=Products.query.get(int(item.product))
                if product.quantity > 0 and product.quantity >= item.quantity:
                    product_inventory[product.id] = product.quantity
                    product_title[product.id] = product.title
                    if check_promotion(product):
                        price[product.id] = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    else:
                        price[product.id] = round(int(product.price)*margin)+int(product.shipping_fee)
                #ของในตะกร้ามากกว่าในสต็อก
                elif product.quantity > 0 and product.quantity < item.quantity:
                    item.quantity = product.quantity
                    db.session.commit()
                    product_title[product.id] = product.title
                    product_inventory[product.id] = product.quantity
                    if check_promotion(product):
                        price[product.id] = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                    else:
                        price[product.id] = round(int(product.price)*margin)+int(product.shipping_fee)
                #ไม่มีของในสต็อก
                else:
                    db.session.delete(item)
                    db.session.commit()
            return render_template("cart.html", cart = cart, product_title = product_title, product_inventory = product_inventory, image_stored = app.config['IMAGE_STORED'], cook=cook, price=price)
        else:
            return redirect(redirect_url())



@app.route('/cart/process', methods=['POST'])
def process():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = cook.cart
    data = request.json
    json_path = os.path.join(app.config['UPLOAD_FOLDER'], user+'item.json')
    with open(json_path, 'w') as f:
            json.dump(data, f)
    for item in cart.items:
        item.quantity = data[item.product]
        db.session.commit()
    pass

def send_message(number, text):
    client = nexmo.Client(key=NEXMO_API_KEY, secret=NEXMO_API_SECRET)
    TO_NUMBER = number
    message = text
    responseData = client.send_message({'from': 'Acme Inc','to': TO_NUMBER,'text': message,'type': 'unicode'})
    return responseData["messages"][0]["status"] == "0"


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = cook.cart
    form = CheckoutContact()
    time = datetime.now()
    reference = datetime.now().strftime("%m%d")+uuid.uuid4().hex[:6].upper()
    expire = datetime.now() + timedelta(days=3)
    timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
    if form.validate_on_submit():
        #send sms confirmation to phone number
        phone_contact = str(form.contact.data)
        db.session.add(Checkout(contact=phone_contact, reference=reference, payment_expire = timeexpire))
        db.session.commit()
        c = Checkout.query.filter_by(reference=reference).first()
        for item in cart.items:
            db.session.add(CheckoutItems(product=item.product, img=item.img, quantity=item.quantity, price=item.price, seller=item.seller, Checkout = c))
            db.session.commit()
        text = "เราได้รับการยืนยันการสั่งซื้อของคุณ รหัสการสั่งซื้อของคุณเลขที: " + reference + " ตรวจสอบการสั่งซื้อของคุณได้ที่ www.f-d-2020.appspot.com/tracking"
        to = '66' + phone_contact[1:]
        #ส่งสำเร็จ return true
        if send_message(to, text):
            for item in cart.items:
                db.session.delete(item)
                db.session.commit()
            db.session.delete(cart)
            return redirect(url_for('fasttrack'))
        else:
            flash("เบอร์ติดต่อไม่ถูกต้อง")
            return redirect(url_for('tracking'))
    else:
        return render_template("checkout.html", form=form, cook=cook)

@app.route('/fasttrack/', methods=['GET', 'POST'])
def fasttrack():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = cook.cart
    form = FastTrack()
    return render_template("fasttrack.html", form=form, cook =cook)


@app.route('/tracking', methods=['GET', 'POST'])
def tracking():
    form = TrackingForm()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    if form.validate_on_submit():
        cart = Checkout.query.filter_by(reference = form.reference.data).first()
        return render_template("order.html", cook =cook, cart=cart)
    else:
        return render_template("tracking.html", form=form, cook =cook)


@app.route('/articles/', defaults={'filter':None})
@app.route('/articles/<filter>')
def articles(filter):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    if filter == None:
        return render_template("articles.html", cook =cook)
    else:
        return render_template("articles.html", article=filter, cook =cook)



@app.route('/register', methods=['GET', 'POST'])
def register():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
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
            return redirect(url_for('dashboard', brand=current_user.username))
        except:
            flash("คุณได้เคยลงทะเบียนแล้ว")
            return redirect(url_for('login'))
    elif current_user.is_authenticated:
        return redirect (url_for('home'))
    else:
        return render_template("register.html", title='', form=form, cook =cook)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = MerchantLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Seller':
            login_user(user)
            return redirect(url_for('dashboard', brand=user.username))
        elif not user:
            flash("ไม่มีอีเมลล์ในระบบ")
            return redirect(url_for('login'))
        else:
            flash("พาสเวิร์ดไม่ถูกต้อง")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, cook =cook)

@app.route('/merchant/<name>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
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
            return render_template("edit.html", form=form, cook =cook)
    else:
        return redirect(url_for('home'))

@app.route('/merchant/<name>/contact', methods=['GET', 'POST'])
@login_required
def addcontact(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
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
            return render_template("addcontact.html", form=form, cook =cook)
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
            return render_template("addcontact.html", form=form, cook =cook)
    else:
        return redirect(url_for('home'))



def save_picture_local(form_picture,name,filetype):
    picture_fn = name + '.jpg'
    picture_path = os.path.join(app.root_path, 'static/products/'+ filetype + '/' + picture_fn)
    output_size = (1000,1000)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    path = 'products/'+filetype+'/'+picture_fn
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
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
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
                save_picture(form.photo1.data, name, category)
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
            return render_template("addproduct.html", form=form, margin=margin, cook =cook)
    elif current_user.role == 'Seller' and current_user.verified == 'no':
        return render_template("addproduct.html", form=form, margin=margin, cook =cook)
    else:
        return redirect(url_for('home'))

@app.route('/merchant/product/edit/<name>', methods=['GET', 'POST'])
@login_required
def edit_product(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    time = datetime.now()
    product=Products.query.get(name)
    if current_user.id == product.owner_id:
        in_cart = False
        #in_cart = CartItems.query.filter(CartItems.product == product.productcode).first()
        if in_cart:
            message = "มีสินค้าอยู่ในตะกร้าสินค้าของผู้ซื้อ ไม่สามารถเปลี่ยนข้อมูลสินค้านี้ได้"
            return render_template("editproduct.html", time=time,  product=product, margin=margin, message=message, image_stored = app.config['IMAGE_STORED'], cook =cook)
        else:
            return render_template("editproduct.html", time=time, product=product, margin=margin, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/image/<name>')
@login_required
def update_image(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product=Products.query.get(name)
    if product.owner_id == current_user.id:
        return render_template("updateimage.html", product=product, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/image/<name>/<file>', methods=['GET', 'POST'])
@login_required
def update_imagefile(name,file):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product=Products.query.get(name)
    form = EditImageForm()
    if form.validate_on_submit():
        name = str(current_user.id) + 'ID'+uuid.uuid4().hex[:6]
        category = product.category
        filename = 'products/'+category+'/'+ secure_filename(name+'.jpg')
        if file == '1':
            if product.imgfile1:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile1)
                product.imgfile1 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile1 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
        if file == '2':
            if product.imgfile2:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile2)
                product.imgfile2 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile2 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
        if file == '3':
            if product.imgfile3:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile3)
                product.imgfile3 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile3 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
        if file == '4':
            if product.imgfile4:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile4)
                product.imgfile4 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile4 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.productcode))
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
            return render_template("updateimagefile.html", form=form, product=product, filename=filename, image_stored = app.config['IMAGE_STORED'], cook =cook)
        else:
            return redirect(url_for('update_image', name=name))
    else:
        return redirect (url_for('dashboard', brand=current_user.username))


@app.route('/merchant/product/detail/<name>', methods=['GET', 'POST'])
@login_required
def update_detail(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product = Products.query.get(name)
    form = EditDetailForm()
    if form.validate_on_submit():
        product.title = form.title.data
        keyword = form.tag.data.lower()
        product.description = form.description.data
        product.productcode = form.title.data + str(current_user.id)
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        #in_cart = CartItems.query.filter(CartItems.product == name).first()
        in_cart = False
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:
            form.title.data = product.title
            form.tag.data = product.tag
            form.description.data = product.description
            return render_template("updatedetail.html", form=form, product=product, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/price/<name>', methods=['GET', 'POST'])
@login_required
def update_price(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product = Products.query.get(name)
    time = datetime.now()
    form = EditPriceForm()
    if form.validate_on_submit():
        noofdays = form.promotion_expire.data
        promotion_expiry_date = datetime.now() + timedelta(days=noofdays)
        expire_on = promotion_expiry_date.strftime("%Y-%m-%d")
        product.promotion_expire  = expire_on
        product.price = form.price.data
        product.promotion = form.promotion.data
        shipping_fee = form.shipping_fee.data
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        #in_cart = CartItems.query.filter(CartItems.product == name).first()
        in_cart = False
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:
            form.price.data = product.price
            form.shipping_fee.data = product.shipping_fee
            form.promotion.data = product.promotion
            return render_template("updateprice.html", form=form, time=time, product=product, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/stock/<name>', methods=['GET', 'POST'])
@login_required
def update_stock(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product = Products.query.get(name)
    form = EditStockForm(quantity = product.quantity)
    if form.validate_on_submit():
        product.quantity = form.quantity.data
        db.session.commit()
        return redirect (url_for('edit_product', name = product.productcode))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        #in_cart = CartItems.query.filter(CartItems.product == name).first()
        in_cart = False
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:

            return render_template("updatestock.html", form=form, product=product, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/edit/delete/<name>', methods=['GET', 'POST'])
@login_required
def edit_delete_product(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product = Products.query.get(name)
    if request.method == 'POST' and current_user.id == product.owner_id:
        try:
            delete_blob(product.imgfile1)
            delete_blob(product.imgfile2)
            delete_blob(product.imgfile3)
            delete_blob(product.imgfile4)
            db.session.delete(product)
            db.session.commit()
        except:
            db.session.delete(product)
            db.session.commit()
        return redirect (url_for('dashboard', brand=current_user.username))
    elif current_user.id == product.owner_id:
        #in_cart = CartItems.query.filter(CartItems.product == name).first()
        in_cart = False
        if not in_cart:
            return render_template("deleteproduct.html", product=product, image_stored = app.config['IMAGE_STORED'], cook =cook)
        else:
            return redirect(url_for("edit_product", name=product.productcode))
    else:
        return redirect(url_for("dashboard", brand = current_user.username))



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
