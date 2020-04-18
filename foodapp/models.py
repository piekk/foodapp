from foodapp import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(22), unique=True,  nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)


    def __repr__(self):
        return "(username: %s)" % (self.username)
