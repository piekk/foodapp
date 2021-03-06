import os
import uuid
import nexmo
from PIL import Image
import time
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from foodapp import app, db, bcrypt, margin
from flask import render_template, request, url_for, redirect, flash, jsonify, json, session, make_response
from foodapp.forms import MerchantRegistrationForm, MerchantLoginForm, ChangeProfile, AddContact, ProductForm, ShopProfile, ImageProfile, IconProfile, Reset_Pass, Password_change
from foodapp.forms import EditImageForm, EditPriceForm, EditDetailForm, EditStockForm, CheckoutContact, TrackingForm, Ship_Address, ConfirmShipmentForm, Add_articles
from foodapp.models import User, Products, Reviews, Cookie, Cart, CartItems, Checkout, CheckoutItems, ShipAddress, MainAddress, PaymentDue, Profile, PasswordChange, Nex
from foodapp.models import Articles
from foodapp.list import category_list
from flask_login import login_user, current_user, logout_user, login_required
from google.cloud import storage


pagename = "farmstory"


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


def send_sms(number, text):
    n = Nex.query.first()
    client = nexmo.Client(key= n.nex_ap + app.config['SM_KEY'], secret= n.nex_key+app.config['SM_SCR'])
    TO_NUMBER = number
    message = text
    responseData = client.send_message({'from': pagename,'to': TO_NUMBER,'text': message,'type': 'unicode'})
    return responseData["messages"][0]["status"] == "0"






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
    articles = Articles.query.order_by(Articles.date_publish.desc()).limit(4).all()
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
        return render_template("home.html", latest=latest, title = pagename, category_list= category_list, margin=margin, time=time, image_stored = app.config['IMAGE_STORED'], cook =cook, articles=articles)


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
        product = Products.query.filter_by(owner_id=current_user.id).all()
        # แสดงสินค้าที่จ่ายเงินแล้ว
        product_confirm = CheckoutItems.query.filter(CheckoutItems.seller == current_user.username, CheckoutItems.status == "รอการจัดส่ง").all()
        return render_template("dashboard.html",brand=brand, category_list= category_list, product=product, time=time, image_stored = app.config['IMAGE_STORED'], cook =cook, product_confirm=product_confirm)
    else:
        current_brand = User.query.filter_by(username=brand).first()
        if current_brand:
            return render_template("view.html", brand=current_brand, category_list= category_list, margin=margin, title = current_brand.username, time = time, image_stored = app.config['IMAGE_STORED'], cook =cook)
        else:
            return redirect(url_for('home'))

@app.route('/view')
def view():
    time = datetime.now()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    return render_template('viewshop.html', category_list=category_list, margin=margin, cook=cook, time=time)

@app.route('/confirmshipment/<brand>/<c_id>', methods=['GET','POST'])
def confirmshipment(brand,c_id):
    time = datetime.now()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = Checkout.query.filter_by(reference = c_id).first()
    product = cart.items
    form = ConfirmShipmentForm()
    if form.validate_on_submit():
        text = form.message.data
        for p in product:
            due = datetime.now() + timedelta(days=3)
            stock = Products.query.get(int(p.product))
            if p.seller == brand:
                p.status = 'จัดส่งแล้ว'
                # track จำนวนที่ขายได้
                stock.number_bought += p.quantity
                db.session.add(PaymentDue(buyer_firstname = p.Checkout.shippingaddress.firstname, buyer_lastname = p.Checkout.shippingaddress.lastname,
                                          item = p.product, order_no = p.Checkout.reference, paid_on = time, due_date = due, amount = p.seller_price, owner_paymentdue = current_user ))
                db.session.commit()
        if text:
            try:
                to = '66'+cart.contact[1:]
                send_sms(to, text)
                return redirect(url_for('dashboard', brand = current_user.username))
            except:
                return redirect(url_for('dashboard', brand = current_user.username))
        else:
            text = "Farmstory ขอบคุณสำหรับการสั่งซื้อสินค้าจากเรา สินค้าของคุณถูกจัดส่งแล้ว ตรวจสอบได้ที่สถานะการสั่งซื้อของคุณ"
            try:
                to = '66'+cart.contact[1:]
                send_sms(to, text)
                return redirect(url_for('dashboard', brand = current_user.username))
            except:
                return redirect(url_for('dashboard', brand = current_user.username))
    elif current_user.is_authenticated and current_user.username == brand and product:
        return render_template("confirmshipment.html", cook=cook, category_list= category_list, product=product, cart=cart, image_stored = app.config['IMAGE_STORED'], form=form)
    else:
        return render_template('404.html', category_list= category_list)



@app.route('/<brand>/profile', methods=['GET','POST'])
@login_required
def myprofile(brand):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = ShopProfile()
    if request.method == 'POST' and form.validate_on_submit and current_user.username == brand:
        if current_user.o_profile:
            current_user.o_profile.title = form.title.data
            current_user.o_profile.content = form.content.data
            db.session.commit()
            return redirect(url_for('dashboard', brand = brand))
        else:
            try:
                db.session.add(Profile(title=form.title.data, content = form.content.data, owner_profile=current_user))
                db.session.commit()
                return redirect(url_for('dashboard', brand = brand))
            except:
                return redirect(url_for('dashboard', brand = brand))
    elif request.method == 'GET' and current_user.is_anonymous:
        return render_template('404.html')
    elif request.method == 'GET' and current_user.username == brand:
        if current_user.o_profile:
            form.title.data = current_user.o_profile.title
            form.content.data = current_user.o_profile.content
            return render_template('addprofile.html', category_list= category_list, cook = cook, form = form)
        else:
            return render_template('addprofile.html', category_list= category_list, cook = cook, form = form)
    else:
        return render_template('404.html', category_list= category_list)


@app.route('/<brand>/imageprofile', methods=['GET','POST'])
@login_required
def myimageprofile(brand):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = ImageProfile()
    if request.method == 'POST' and form.validate_on_submit and current_user.username == brand:
        profile = Profile.query.filter_by(profile_owner = current_user.id).first()
        if profile and profile.image1 is None:
            try:
                name = str(current_user.id) + uuid.uuid4().hex[:4]
                category = 'main'
                filename = 'products/'+category+ '/'+ secure_filename(name+'.jpg')
                save_picture(form.img.data, name, category)
                profile.image1 = filename
                db.session.commit()
                return redirect(url_for('dashboard', brand = brand))

            except:
                return redirect(url_for('dashboard', brand = brand))
        elif profile and profile.image1:
            try:
                name = str(current_user.id) + uuid.uuid4().hex[:4]
                category = 'main'
                filename = 'products/'+category+ '/'+ secure_filename(name+'.jpg')
                save_picture(form.img.data, name, category)
                delete_blob(profile.image1)
                profile.image1 = filename
                db.session.commit()
                return redirect(url_for('dashboard', brand = brand))
            except:
                return redirect(url_for('dashboard', brand = brand))
        else:
            return redirect(url_for('myprofile', brand = brand))
    elif request.method == 'GET' and current_user.is_anonymous:
        return render_template('404.html')
    elif request.method == 'GET' and current_user.username == brand:
        profile = Profile.query.filter_by(profile_owner = current_user.id).first()
        if profile:
            return render_template('addimageprofile.html', category_list= category_list, cook = cook, form = form)
        else:
            return redirect(url_for('myprofile', brand = brand))
    else:
        return render_template('404.html')


@app.route('/<brand>/iconprofile', methods=['GET','POST'])
@login_required
def myiconprofile(brand):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = IconProfile()
    if request.method == 'POST' and form.validate_on_submit and current_user.username == brand:
        profile = Profile.query.filter_by(profile_owner = current_user.id).first()
        if profile and profile.icon is None:
            try:
                name = str(current_user.id) + uuid.uuid4().hex[:4]
                category = 'icon'
                filename = 'products/'+category+ '/'+ secure_filename(name+'.jpg')
                save_picture(form.icon.data, name, category)
                profile.icon = filename
                db.session.commit()
                return redirect(url_for('dashboard', brand = brand))
            except:
                return redirect(url_for('dashboard', brand = brand))
        elif profile and profile.icon:
            try:
                name = str(current_user.id) + uuid.uuid4().hex[:4]
                category = 'icon'
                filename = 'profile/'+category+ '/'+ secure_filename(name+'.jpg')
                save_picture(form.icon.data, name, category)
                delete_blob(profile.icon)
                profile.icon = filename
                db.session.commit()
                return redirect(url_for('dashboard', brand = brand))
            except:
                return redirect(url_for('dashboard', brand = brand))
        else:
            return redirect(url_for('myprofile', brand = brand))
    elif request.method == 'GET' and current_user.is_anonymous:
        return render_template('404.html')
    elif request.method == 'GET' and current_user.username == brand:
        profile = Profile.query.filter_by(profile_owner = current_user.id).first()
        if profile:
            return render_template('addiconprofile.html', category_list= category_list, cook = cook, form = form)
        else:
            return redirect(url_for('myprofile', brand = brand))
    else:
        return render_template('404.html')


@app.route('/shop/', defaults={'filter':None}, methods=['GET', 'POST'])
@app.route('/shop/<filter>', methods=['GET', 'POST'])
def shop(filter):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    page = request.args.get('page', 1,type=int)
    productcategory = [i[0] for i in category_list]
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
        return render_template("shop.html", title=pagename+" ร้านค้า", product = product, category_list= category_list, margin=margin, time=time, filter='shop', image_stored = app.config['IMAGE_STORED'], cook =cook)
    elif request.method == 'GET' and filter in productcategory:
        time = datetime.now()
        product = Products.query.filter(Products.category==filter).paginate(per_page=16, page=page)
        return render_template("shop.html", title=pagename+" ร้านค้า"+" "+filter, product = product, category_list= category_list, margin=margin, time=time, filter=filter, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        time = datetime.now()
        fil = secure_filename(filter)
        searchwordlower = fil.lower()
        searchword = searchwordlower.replace(" ","")
        product = Products.query.filter(Products.tag.contains(searchword)).paginate(per_page=16, page=page)
        if product:
            return render_template("shop.html", title=pagename+" "+filter, product = product, category_list= category_list, margin=margin, time=time, filter=filter, image_stored = app.config['IMAGE_STORED'], cook =cook)
        else:
            return render_template('404.html', category_list= category_list)


@app.route('/product/<product>', methods=['GET', 'POST'])
def product(product):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    time = datetime.now()
    product = Products.query.get(product)
    time = datetime.now()
    suggest = Products.query.filter(Products.quantity>=0).order_by(Products.view.desc()).limit(9).all()
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
        return render_template("product.html", product = product, suggest=suggest, title=pagename+product.title, time=time, category_list= category_list, margin=margin, image_stored = app.config['IMAGE_STORED'], cook =cook)
    else:
        return render_template('404.html', category_list= category_list)


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
            # สำหรับ เช็คสินค้าตาม minimum_shippingfee ของ Seller แต่ละราย
            seller = []
            qualify_seller = {}
            # list ผู้ขายที่ราคาสินค้าเกิน shipping_fee ที่ตั้งไว้
            q_seller =[]
            for item in cart.items:
                if item.seller not in seller:
                    seller.append(item.seller)
            for i in seller:
                s = User.query.filter_by(username = i).first()
                seller_minimum = int(s.minimum_shippingfee)
                total = 0
                for item in cart.items:
                    p = Products.query.get(int(item.product))
                    if i == item.seller:
                        if check_promotion(p):
                            total += round(((int(p.price)*(1-int(p.promotion)/100))*margin)+int(p.shipping_fee))*item.quantity
                            qualify_seller[i] = total
                        else:
                            total += round((int(p.price)*margin)+int(p.shipping_fee))*item.quantity
                            qualify_seller[i] = total
                if qualify_seller[i] > seller_minimum:
                    q_seller.append(i)

            for item in cart.items:
                product=Products.query.get(int(item.product))
                if product.quantity > 0 and product.quantity >= item.quantity:
                    product_inventory[product.id] = product.quantity
                    product_title[product.id] = product.title
                    # อยู่ใน list ไม่คิดค่า shipping
                    if item.seller in q_seller:
                        if check_promotion(product):
                            price[product.id] = round((int(product.price)*(1-int(product.promotion)/100))*margin)
                        else:
                            price[product.id] = round(int(product.price)*margin)
                    else:
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
                    # อยู่ใน list ไม่คิดค่า shipping
                    if item.seller in q_seller:
                        if check_promotion(product):
                            price[product.id] = round((int(product.price)*(1-int(product.promotion)/100))*margin)
                        else:
                            price[product.id] = round(int(product.price)*margin)
                    else:
                        if check_promotion(product):
                            price[product.id] = round((int(product.price)*(1-int(product.promotion)/100))*margin)+int(product.shipping_fee)
                        else:
                            price[product.id] = round(int(product.price)*margin)+int(product.shipping_fee)
                #ไม่มีของในสต็อก
                else:
                    db.session.delete(item)
                    db.session.commit()
            return render_template("cart.html", seller=q_seller, cart = cart, category_list= category_list,  product_title = product_title, product_inventory = product_inventory, image_stored = app.config['IMAGE_STORED'], cook=cook, price=price, m_name="robots", m_content="noindex")
        else:
            return redirect(redirect_url())



@app.route('/cart/process', methods=['POST'])
def process():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = cook.cart
    data = request.json
    name = secure_filename(user + '.json')
    json_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER']+'/'+name)
    with open(json_path, 'w') as f:
            json.dump(data, f)
    for item in cart.items:
        item.quantity = data[item.product]
        db.session.commit()
    return redirect(url_for('cart'))



@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = cook.cart
    form = CheckoutContact()
    time = datetime.now()
    reference = datetime.now().strftime("%m%d")+uuid.uuid4().hex[:6].upper()
    expire = datetime.now() + timedelta(days=1)
    timeexpire = expire.strftime("%Y-%m-%d  %H:%M")
    if form.validate_on_submit() and cart and cart.items:
        #send sms confirmation to phone number
        phone_contact = str(form.contact.data)
        db.session.add(Checkout(contact=phone_contact, reference=reference, payment_expire = timeexpire))
        db.session.commit()
        c = Checkout.query.filter_by(reference=reference).first()
        # สำหรับ เช็คสินค้าตาม minimum_shippingfee ของ Seller แต่ละราย
        seller = []
        qualify_seller = {}
        # list ผู้ขายที่ราคาสินค้าเกิน shipping_fee ที่ตั้งไว้
        q_seller =[]
        text = "Farmstory เราได้รับการยืนยันการสั่งซื้อของคุณ รหัสการสั่งซื้อของคุณเลขที: " + reference + " ตรวจสอบการสั่งซื้อของคุณได้ที farmerdiary"
        to = '66' + phone_contact[1:]
        #ส่งสำเร็จ return true ตรวจ log ใน Nexmo สำหรับกรณีไม่ได้รับรหัส
        try :
            send_sms(to, text)
            message = "เราได้ส่งรหัสการสั่งซื้อไปยังหมายเลขโทรศัพท์ที่คุณให้ไว้เบอร์: " + form.contact.data + " หากคุณไมไ่ด้รับข้อภายใน 10 นาทีเพื่อความรวดเร็วสามารถติดต่อเราทางไลน์ "
        except:
            message = "เราได้ส่งรหัสการสั่งซื้อไปยังหมายเลขโทรศัพท์ที่คุณให้ไว้เบอร์: " + form.contact.data + " หากคุณไมไ่ด้รับข้อภายใน 10 นาทีเพื่อความรวดเร็วสามารถติดต่อเราทางไลน์ "

        for item in cart.items:
            if item.seller not in seller:
                seller.append(item.seller)
        for i in seller:
            s = User.query.filter_by(username = i).first()
            seller_minimum = int(s.minimum_shippingfee)
            total = 0
            for item in cart.items:
                p = Products.query.get(int(item.product))
                if i == item.seller:
                    if check_promotion(p):
                        total += round(((int(p.price)*(1-int(p.promotion)/100))*margin)+int(p.shipping_fee))*item.quantity
                        qualify_seller[i] = total
                    else:
                        total += round((int(p.price)*margin)+int(p.shipping_fee))*item.quantity
                        qualify_seller[i] = total
            if qualify_seller[i] > seller_minimum:
                q_seller.append(i)
        for item in cart.items:
            p = Products.query.get(int(item.product))
            if item.seller in q_seller:
                if check_promotion(p):
                    price_total = round((int(p.price)*(1-int(p.promotion)/100))*margin) * item.quantity
                    seller_price = round(int(p.price)*(1-int(p.promotion)/100)) * item.quantity
                else:
                    price_total = round(int(p.price)*margin) * item.quantity
                    seller_price = round(int(p.price)) * item.quantity
            else:
                if check_promotion(p):
                     price_total = round((int(p.price)*(1-int(p.promotion)/100))*margin)+int(p.shipping_fee) * item.quantity
                     seller_price = round((int(p.price)*(1-int(p.promotion)/100))+int(p.shipping_fee)) * item.quantity
                else:
                     price_total = round((int(p.price)*margin)+int(p.shipping_fee)) * item.quantity
                     seller_price = round((int(p.price))+int(p.shipping_fee)) * item.quantity
            # อัเดทสต้อก ลบจากจำนวนที่จัดส่ง
            p.quantity -= item.quantity
            db.session.add(CheckoutItems(product=item.product, img=item.img, quantity=item.quantity, price=str(price_total), seller_price = str(seller_price) , seller=item.seller, Checkout = c))
            db.session.commit()
        #รวมราคา
        tt_p = 0
        for item in c.items:
            tt_p += round(int(item.price))
        c.totalprice = str(tt_p)
        db.session.commit()
        flash(message)
        return redirect(url_for('tracking'))
    else:
        return render_template("checkout.html", form=form, cook=cook, category_list= category_list, m_name="robots", m_content="noindex")



@app.route('/tracking', methods=['GET', 'POST'])
def tracking():
    form = TrackingForm()
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    # cart ที่สร้างชั่วคราวจากคุกกี
    cart_temp = cook.cart
    if form.validate_on_submit():
        cart = Checkout.query.filter_by(reference = form.reference.data).first()
        if cart and cart.contact == form.contact.data:
            # สร้าง cart สำหรับเช็คเอาท์แล้วลบของเดิม
            if cart_temp:
                for item in cart_temp.items:
                    db.session.delete(item)
                    db.session.commit()
                db.session.delete(cart_temp)
            # ตั้งค่าคุ้กกี้ใหม่ ใช้ reference เชคตะกร้าแทนล้อกอิน
            resp = make_response(redirect('/order'))
            resp.set_cookie('I_D', cart.reference, max_age=60*30)
            return resp
        else:
            flash('ข้อมูลไม่ถูกต้อง')
            return redirect(url_for('tracking'))
    else:
        return render_template("tracking.html", form=form, cook =cook, category_list= category_list, m_name="robots", m_content="noindex")


@app.route('/order', methods=['GET', 'POST'])
def order():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    user_id = request.cookies.get('I_D')
    # get data send to order page view
    product_title = {}
    total_price = 0
    cart = Checkout.query.filter_by(reference = user_id).first()
    if request.method == 'POST' and 'confirm_address' in request.form:
        cart.confirm_address = 'y'
        db.session.commit()
        return redirect(url_for('order'))
    elif request.method=='GET' and cart:
        # query db for ccontact check if existing main address
        main_address = MainAddress.query.filter_by(contact = cart.contact).first()
        if main_address:
            db.session.add(ShipAddress(firstname=main_address.firstname, lastname=main_address.lastname, contact=main_address.contact,
                                       homeaddress=main_address.homeaddress, housename=main_address.housename,
                                       street=main_address.street, sub_street=main_address.sub_street,
                                       subdistrict=main_address.subdistrict, district=main_address.district,
                                       province=main_address.province, country='Thailand', postcode=main_address.postcode, CheckoutAddress = cart))
            db.session.commit()
        # เอาชื่อสินค้้า
        for item in cart.items:
            product=Products.query.get(int(item.product))
            product_title[product.id] = product.title
            total_price += int(item.price)
        return render_template("order.html", cook = cook, cart=cart, category_list= category_list, product_title = product_title, image_stored = app.config['IMAGE_STORED'], total_price = total_price, m_name="robots", m_content="noindex", main_contact = app.config['MAIN_CONTACT'],
                                contact_email = app.config['CONTACT_EMAIL'], account_name = app.config['A_NAME'], account_no = app.config['A_NO'], account_bank = app.config['A_BANK'] )
    else:
        return redirect(url_for('tracking'))

@app.route('/address', methods=['GET', 'POST'])
def address():
    user_id = request.cookies.get('I_D')
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    cart = Checkout.query.filter_by(reference = user_id).first()
    form = Ship_Address()
    if form.validate_on_submit():
        # ใส่เป็นที่อยู่ประจำ
        if form.make_mainaddress.data == True:
            # ถ้ามีที่อยู่ประจำอยู่แล้ว เปลี่ยนที่อยู่เปลี่ยนที่อยู่ประจำ
            main_address = MainAddress.query.filter_by(contact = cart.contact).first()
            # ยังไม่เคยมีที่อยู่ประจำ
            if main_address:
                try:
                    main_address.firstname = form.firstname.data
                    main_address.lastname = form.lastname.data
                    main_address.contact = form.contact.data
                    main_address.homeaddress = form.homeaddress.data
                    main_address.housename = form.housename.data
                    main_address.street = form.street.data
                    main_address.sub_street = form.substreet.data
                    main_address.subdistrict = form.subdistrict.data
                    main_address.district = form.district.data
                    main_address.province = form.province.data
                    main_address.postcode = form.postcode.data

                    db.session.add(ShipAddress(firstname=form.firstname.data, lastname=form.lastname.data, contact=form.contact.data,
                                               homeaddress=form.homeaddress.data, housename=form.housename.data,
                                               street=form.street.data, sub_street=form.substreet.data,
                                               subdistrict=form.subdistrict.data, district=form.district.data,
                                               province=form.province.data, country='Thailand', postcode=form.postcode.data, CheckoutAddress = cart))

                    # เปลี่ยนสถานะ ของ confirm address ใน cart เป็น confirm
                    cart.confirm_address = 'y'
                    db.session.commit()
                    return redirect(url_for('order'))
                except:
                    flash('ข้อมูลไม่ถูกต้อง')
                    return redirect(url_for('address'))
            # ยังไม่เคยมีที่อยู่ประจำ
            else:
                try:
                    db.session.add(MainAddress(firstname=form.firstname.data, lastname=form.lastname.data, contact=cart.contact,
                                               homeaddress=form.homeaddress.data, housename=form.housename.data,
                                               street=form.street.data, sub_street=form.substreet.data,
                                               subdistrict=form.subdistrict.data, district=form.district.data,
                                               province=form.province.data, country='Thailand', postcode=form.postcode.data))
                    db.session.add(ShipAddress(firstname=form.firstname.data, lastname=form.lastname.data, contact=form.contact.data,
                                               homeaddress=form.homeaddress.data, housename=form.housename.data,
                                               street=form.street.data, sub_street=form.substreet.data,
                                               subdistrict=form.subdistrict.data, district=form.district.data,
                                               province=form.province.data, country='Thailand', postcode=form.postcode.data,
                                               CheckoutAddress = cart))
                    cart.confirm_address = 'y'
                    db.session.commit()
                    return redirect(url_for('order'))
                except:
                    flash('ข้อมูลไม่ถูกต้อง')
                    return redirect(url_for('address'))
        # จัดส่งไปที่อยู่ชั่วคราว สำหรับครั้งนี้เท่านั้น
        else:
            try:
                db.session.add(ShipAddress(firstname=form.firstname.data, lastname=form.lastname.data, contact=form.contact.data,
                                           homeaddress=form.homeaddress.data, housename=form.housename.data,
                                           street=form.street.data, sub_street=form.substreet.data,
                                           subdistrict=form.subdistrict.data, district=form.district.data,
                                           province=form.province.data, country='Thailand', postcode=form.postcode.data,
                                           CheckoutAddress = cart))

                cart.confirm_address = 'y'
                db.session.commit()
                return redirect(url_for('order'))
            except:
                flash('ข้อมูลไม่ถูกต้อง')
                return redirect(url_for('address'))
    elif request.method == 'GET' and cart:
        form.contact.data = cart.contact
        main_address = MainAddress.query.filter_by(contact = cart.contact).first()
        # เคยใส่ที่อยู่แล้ว ใส่ชื่อนามสกุลลงใน field ก่อน
        if main_address:
            form.firstname.data = main_address.firstname
            form.lastname.data = main_address.lastname
            return render_template('address.html', cook=cook, category_list= category_list, form=form, m_name="robots", m_content="noindex")
        else:
            return render_template('address.html', cook=cook, category_list= category_list, form=form, m_name="robots", m_content="noindex")
    else:
        return redirect(url_for('order'))


@app.route('/articles/', defaults={'filter':None})
@app.route('/articles/<filter>')
def articles(filter):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    if filter == None:
        articles = Articles.query.order_by(Articles.date_publish.desc()).limit(4).all()
        return render_template("articles.html", category_list= category_list, cook =cook, title = 'บทความจาก -farmstory',image_stored = app.config['IMAGE_STORED'], articles = articles)
    else:
        article = Articles.query.get(filter)
        return render_template("article.html", category_list= category_list, cook =cook, title = article.title, article=article, image_stored = app.config['IMAGE_STORED'])



@app.route('/register', methods=['GET', 'POST'])
def register():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = MerchantRegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        phone = str(form.contact.data)
        time = datetime.now()
        send_sms('66814219606', "มีผู้สมัครใหม่")
        send_sms('66'+ phone[1:], "Farmstory เราได้รับการสมัครสมาชิกของคุณแล้ว กรุณารอการติดต่อจากเราเพื่อยืนยันตัวตน")
        try:
            db.session.add(User(firstname=form.firstname.data, lastname=form.lastname.data, username=form.username.data, email=form.email.data, password=hashed_pw, verified='no', contact=phone, role='Seller', date_register=time.strftime("%Y-%m-%d  %H:%M")))
            db.session.commit()
            user = User.query.filter_by(email=form.email.data).first()
            login_user(user)
            session.permanent = True
            return redirect(url_for('dashboard', brand=current_user.username))
        except:
            flash("คุณได้เคยลงทะเบียนแล้ว")
            return redirect(url_for('login'))
    elif current_user.is_authenticated:
        return redirect (url_for('home'))
    else:
        return render_template("register.html", title='', category_list= category_list, form=form, cook =cook, m_name="robots", m_content="noindex")

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = MerchantLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='Seller':
            login_user(user)
            session.permanent = True
            return redirect(url_for('dashboard', brand=user.username))
        if user and bcrypt.check_password_hash(user.password, form.password.data) and user.role=='admin':
            login_user(user)
            session.permanent = True
            return redirect(url_for('manage', user = current_user))
        elif not user:
            flash("ไม่มีอีเมลล์ในระบบ")
            return redirect(url_for('login'))
        else:
            flash("พาสเวิร์ดไม่ถูกต้อง")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, category_list= category_list, cook =cook, m_name="robots", m_content="noindex")


@app.route('/admin')
def admin():
    return render_template('404.html')


@app.route('/manage')
def manage():
    if current_user.is_authenticated and current_user.role == 'admin':
        return render_template('manage.html')
    else:
        return render_template('404.html')

@app.route('/manage/user_verify' , methods=['GET', 'POST'])
def user_verify():
    if request.method == 'POST':
        if 'confirm_user' in request.form:
            confirm_user = request.form.get('confirm_user')
            user = User.query.get(confirm_user)
            user.verified = 'y'
            db.session.commit()
        return redirect(url_for('user_verify'))
    elif current_user.is_authenticated and current_user.role =='admin':
        pending_user = User.query.filter(User.role=='Seller',User.verified=='no').order_by(User.date_register.desc()).all()
        return render_template('verifyuser.html', pending_user=pending_user)
    else:
        return render_template('404.html')

@app.route('/manage/payment_verify')
def payment_verify():
    if current_user.is_authenticated and current_user.role == 'admin':
        order = Checkout.query.filter_by(payment = 'n').all()
        return render_template("verifypayment.html", order = order)
    else:
        return render_template('404.html')


@app.route('/manage/confirmation/<c_id>' , methods=['GET', 'POST'])
def cartref_confirmation(c_id):
    if request.method=='POST':
        cart = Checkout.query.filter_by(reference = c_id).first()
        cart.payment = "C"
        d_time = datetime.now()
        ship_date = datetime.now() + timedelta(days=3)
        cart.payment_complete = d_time
        db.session.commit()
        # ส่ง sms หา seller ว่ามีคนสั่งสินค้า
        seller = []
        for item in cart.items:
            item.ship_date = ship_date
            product_owner = Products.query.get(item.product)
            item.status = "รอการจัดส่ง"
            if product_owner.owner_id not in seller:
                seller.append(product_owner.owner_id)
        db.session.commit()
        text = "Farmstory มีการสั่งซื้อสินค้าของคุณ กรุณาล็อกอินเข้าระบบเพื่อดูข้อมูล"
        for s in seller:
            user = User.query.get(s)
            n = Nex.query.first()
            phone_contact = '66'+ user.contact[1:]
            client = nexmo.Client(key= n.nex_ap + app.config['SM_KEY'], secret= n.nex_key+app.config['SM_SCR'])
            TO_NUMBER = phone_contact
            message = text
            client.send_message({'from': pagename,'to': TO_NUMBER,'text': message,'type': 'unicode'})
            time.sleep(3)
        return redirect(url_for('paymentcomplete'))
    elif current_user.is_authenticated and current_user.role == 'admin':
        cart = Checkout.query.filter_by(reference = c_id).first()
        return render_template("cartconfirmation.html", cart=cart, image_stored = app.config['IMAGE_STORED'])
    else:
        return render_template('404.html')

@app.route('/manage/paymentcomplete')
def paymentcomplete():
    if current_user.is_authenticated and current_user.role == 'admin':
        carts = Checkout.query.filter_by(payment = 'C').all()
        return render_template("paymentcomplete.html", carts = carts)
    else:
        return render_template('404.html')

@app.route('/manage/articles', methods=['GET', 'POST'])
def addarticles():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = Add_articles()
    time = datetime.now()
    if form.validate_on_submit() and current_user.is_authenticated and current_user.role == 'admin':
        db.session.add(Articles(title = form.title.data, sub_title= form.sub_title.data, content1 = form.content1.data, content2 = form.content2.data, content3 = form.content3.data, content4 = form.content4.data, content5 = form.content5.data, content6 = form.content6.data, date_publish = time, author = 'farmstory'))
        db.session.commit()
        return redirect(url_for('manage'))
    elif request.method == 'GET' and current_user.is_authenticated and current_user.role == 'admin':
        return render_template("addarticles.html", cook = cook, form=form)
    else:
        return render_template('404.html')


@app.route('/merchant/<name>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = ChangeProfile()
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
                return render_template("edit.html", form=form, cook =cook, category_list= category_list, m_name="robots", m_content="noindex")
        elif request.method == 'POST':
            flash("ข้อมูลไม่ถูกต้อง")
            return render_template("edit.html", form=form, cook =cook, category_list= category_list, m_name="robots", m_content="noindex")
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            return render_template("edit.html", form=form, cook =cook, category_list= category_list, m_name="robots", m_content="noindex")
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
            return render_template("addcontact.html", form=form, category_list= category_list, cook =cook, m_name="robots", m_content="noindex")
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
    bucket = storage_client.get_bucket(app.config['BUCKET_NAME'])
    blob = bucket.blob('products/'+filetype+'/'+picture_fn)
    blob.upload_from_filename(picture_path)

    return picture_path

def delete_blob(blob_name):
    bucket_name = app.config['BUCKET_NAME']
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
            return render_template("addproduct.html", form=form, margin=margin, category_list= category_list, cook =cook, m_name="robots", m_content="noindex")
    elif current_user.role == 'Seller' and current_user.verified == 'no':
        return render_template("addproduct.html", form=form, margin=margin, cook =cook, category_list= category_list, m_name="robots", m_content="noindex")
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
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if in_cart:
            message = "มีสินค้าอยู่ในตะกร้าสินค้าของผู้ซื้อ ไม่สามารถเปลี่ยนข้อมูลสินค้านี้ได้"
            return render_template("editproduct.html", time=time,  product=product, category_list= category_list, margin=margin, message=message, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
        else:
            return render_template("editproduct.html", time=time, product=product, category_list= category_list, margin=margin, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
    else:
        return redirect (url_for('dashboard', brand=current_user.username))

@app.route('/merchant/product/image/<name>')
@login_required
def update_image(name):
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    product=Products.query.get(name)
    if product.owner_id == current_user.id:
        return render_template("updateimage.html", product=product, category_list= category_list, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
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
                return redirect (url_for('update_image', name=product.id))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile1 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
        if file == '2':
            if product.imgfile2:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile2)
                product.imgfile2 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile2 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
        if file == '3':
            if product.imgfile3:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile3)
                product.imgfile3 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile3 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
        if file == '4':
            if product.imgfile4:
                save_picture(form.image.data, name, category)
                delete_blob(product.imgfile4)
                product.imgfile4 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
            else:
                save_picture(form.image.data, name, category)
                product.imgfile4 = filename
                db.session.commit()
                return redirect (url_for('update_image', name=product.id))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if in_cart:
            return redirect(url_for('edit_product', name=product.id))
        elif file in {'1','2','3','4'}:
            if file == '1':
                filename = product.imgfile1
            elif file == '2':
                filename = product.imgfile2
            elif file == '3':
                filename = product.imgfile3
            elif file == '4':
                filename = product.imgfile4
            return render_template("updateimagefile.html", form=form, product=product, category_list= category_list, filename=filename, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
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
        return redirect (url_for('edit_product', name = product.id))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.id))
        else:
            form.title.data = product.title
            form.tag.data = product.tag
            form.description.data = product.description
            return render_template("updatedetail.html", form=form, product=product, category_list= category_list, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
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
        return redirect (url_for('edit_product', name = product.id))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.productcode))
        else:
            form.price.data = product.price
            form.shipping_fee.data = product.shipping_fee
            form.promotion.data = product.promotion
            return render_template("updateprice.html", form=form, time=time, category_list= category_list, product=product, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
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
        return redirect (url_for('edit_product', name = product.id))
    elif request.method == 'GET' and product.owner_id == current_user.id:
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if in_cart:
            return redirect (url_for('edit_product', name = product.id))
        else:

            return render_template("updatestock.html", form=form, product=product, category_list= category_list, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
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
        in_cart = CheckoutItems.query.filter(CheckoutItems.product == str(product.id), CheckoutItems.status != 'จัดส่งแล้ว').first()
        if not in_cart:
            return render_template("deleteproduct.html", product=product, category_list= category_list, image_stored = app.config['IMAGE_STORED'], cook =cook, m_name="robots", m_content="noindex")
        else:
            return redirect(url_for("edit_product", name=product.id))
    else:
        return redirect(url_for("dashboard", brand = current_user.username))


@app.route('/aboutus')
def aboutus():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    return render_template("aboutus.html", category_list= category_list, cook = cook)


@app.route('/sellwithus')
def sellwithus():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    return render_template("sellwithus.html", category_list= category_list, cook = cook)

@app.route('/howtoaddproduct')
def howtoaddproduct():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    return render_template("howtoaddproduct.html", category_list= category_list, cook = cook)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title = '404'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('404.html', title = '500')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = Reset_Pass()
    if form.validate_on_submit():
        time = datetime.now()
        user = User.query.filter_by(contact = form.contact.data).first()
        if user and user.email == form.email.data:
            inP_change = PasswordChange.query.filter_by(contact = user.contact).first()
            if inP_change and inP_change.expire < time:
                db.session.delete(inP_change)
                db.sessin.commit()
                o_t_p = uuid.uuid4().hex[:4]
                text = "Farmstory รหัสยืนยันตัวตนของคุณคือ: "+ str(o_t_p)
                time_expire = datetime.now() + timedelta(days=1)
                try:
                    to = '66'+ user.contact[1:]
                    send_sms(to, text)
                    db.session.add(PasswordChange(contact = form.contact.data, otp = str(o_t_p), expire = time_expire))
                    db.session.commit()
                    return redirect(url_for("changepassword"))
                except:
                    flash('ไม่สามารถยืนยันตัวตนได้')
                    return redirect(url_for('resetpassword'))
            elif inP_change and inP_change.expire > time:
                flash('เราได้ส่งรหัสยืนยันตัวตนให้คุณแล้ว')
                return redirect(url_for("changepassword"))
            else:
                o_t_p = uuid.uuid4().hex[:4]
                text = "รหัสยืนยันตัวตนของคุณคือ: "+ str(o_t_p)
                time_expire = datetime.now() + timedelta(days=1)
                try:
                    to = '66'+ user.contact[1:]
                    send_sms(to, text)
                    db.session.add(PasswordChange(contact = form.contact.data, otp = str(o_t_p), expire = time_expire))
                    db.session.commit()
                    return redirect(url_for("changepassword"))
                except:
                    flash('ไม่สามารถยืนยันตัวตนได้')
                    return redirect(url_for('resetpassword'))
        else:
            flash('ไม่มีหมายเลขนี้ในระบบ')
            return redirect(url_for('resetpassword'))
    else:
        return render_template("resetpassword.html", category_list= category_list, cook = cook, form=form)


@app.route('/changepassword', methods=['GET', 'POST'])
def changepassword():
    user = request.cookies.get('cook_id')
    cook = Cookie.query.filter_by(cook_id = user).first()
    form = Password_change()
    time = datetime.now()
    if form.validate_on_submit():
        person = PasswordChange.query.filter_by(otp = form.otp.data).first()
        user = User.query.filter_by(contact = person.contact).first()
        if person and person.expire < time:
            db.session.delete(person)
            db.session.commit()
            flash('รหัสของคุณหมดอายุแล้วกรุณาขอรหัสใหม่')
            return redirect(url_for("resetpassword"))
        elif person and person.expire > time:
            hashed_pw = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            user.password = hashed_pw
            db.session.delete(person)
            db.session.commit()
            flash('เปลี่ยนรหัสเรียบร้อยแล้ว')
            return redirect(url_for("login"))
        else:
            flash('กรุณาขอรหัสก่อนเปลี่ยนพาสเวิร์ด')
            return redirect(url_for("resetpassword"))
    return render_template("changepassword.html", category_list= category_list, cook = cook, form=form)
