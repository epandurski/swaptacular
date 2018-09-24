from users import db


class User(db.Model):
    user_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    salt = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    recovery_code_hash = db.Column(db.Text, nullable=False)
