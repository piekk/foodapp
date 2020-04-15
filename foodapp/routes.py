import os
from foodapp import app
from flask import render_template, request

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

@app.route('/product')
def product():
    return render_template("product.html")
