import os
from foodapp import app
from flask import render_template

@app.route('/')
def home():
  return render_template("home.html")

@app.route('/<brand>')
def view(brand):
    # if brand in db:
    #return Brand
    #else
  return render_template("brand.html",brand=brand)
