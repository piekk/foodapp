from foodapp import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(22), unique=True,  nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    firstname = db.Column(db.String(30), nullable=True)
    lastname = db.Column(db.String(40), nullable=True)
    contact = db.Column(db.String(12), unique=True, nullable=True)
    alter_contact = db.Column(db.String(10), unique=True, nullable=True)
    role = db.Column(db.String(6), unique=False, nullable=False)
    verified = db.Column(db.String(3), unique=False, default='no', nullable=False)
    date_register = db.Column(db.DateTime, unique=False, nullable=False)
    product = db.relationship("Products", backref="owner_product")


    def __repr__(self):
        return "(username: %s)" % (self.username)

class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_add = db.Column(db.DateTime, unique=False, nullable=False)
    productcode = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(35), unique=False, nullable=False)
    price = db.Column(db.String(7), unique=False, nullable=False)
    shipping_fee= db.Column(db.String(5), unique=False, nullable=False)
    promotion = db.Column(db.String(6), unique=False, nullable=True, default=0)
    promotion_expire = db.Column(db.DateTime, unique=False, nullable=True)
    imgfile1 = db.Column(db.String(50), unique=True, nullable=False)
    imgfile2 = db.Column(db.String(50), unique=True, nullable=True)
    imgfile3 = db.Column(db.String(50), unique=True, nullable=True)
    imgfile4 = db.Column(db.String(50), unique=True, nullable=True)
    quantity = db.Column(db.Integer, unique=False, nullable=False, default=0)
    category = db.Column(db.String(20), unique=False, nullable=False, default='Category')
    tag = db.Column(db.String(50), unique=False, nullable=True, default='tag')
    description = db.Column(db.Text, nullable=True)
    view = db.Column(db.Integer, unique=False, nullable=False, default=0)
    number_bought = db.Column(db.Integer, unique=False, nullable=False, default=0)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    review = db.relationship("Reviews", backref='product_review')

    def __repr__(self):
        return "(title: %s)" % (self.title)

class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    star_rating = db.Column(db.Integer, unique=False, nullable=False)
    messages = db.Column(db.String(100), nullable=True)
    review_by = db.Column(db.String(12), nullable=False)
    review_date = db.Column(db.DateTime, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))

    def __repr__(self):
        return "(star_rating: {}, by: {})" .format(self.star_rating, self.review_by)
