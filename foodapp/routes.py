import os
import uuid
from PIL import Image
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from foodapp import app, bcrypt, margin
from flask import render_template, request, url_for, redirect, flash, jsonify, json
from foodapp.forms import RegistrationForm, LoginForm, MerchantRegistrationForm, ChangeStatusForm, MerchantLoginForm, ProductForm, EditImageForm, EditDetailForm, EditPriceForm, EditStockForm, Profile, Ship_Address
from foodapp.models import User
from flask_login import login_user, current_user, logout_user, login_required

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
def view(brand):
    # if brand in db:
    #return Brand
    #else
  return render_template("brand.html",brand=brand)

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
