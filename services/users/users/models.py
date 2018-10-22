from users import db, logger


class User(db.Model):
    user_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    salt = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    recovery_code_hash = db.Column(db.Text, nullable=True)
    two_factor_login = db.Column(db.Boolean, nullable=False)


class UserUpdateSignal(db.Model):
    user_update_signal_id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)
    old_email = db.Column(db.Text, nullable=True)
    new_email = db.Column(db.Text, nullable=True)

    def send_message(self):
        """Inform the other services that user's email has changed."""

        logger.debug('Sent user update signal: %i, %s, %s', self.user_id, self.old_email, self.new_email)
