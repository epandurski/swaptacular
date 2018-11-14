import logging
from flask_sqlalchemy import SQLAlchemy
from flask_signalbus import SignalBusMixin

logger = logging.getLogger(__name__)


class CustomAlchemy(SignalBusMixin, SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if "isolation_level" not in options:
            options["isolation_level"] = "REPEATABLE_READ"
        return super().apply_driver_hacks(app, info, options)


db = CustomAlchemy()


class User(db.Model):
    user_id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.Text, unique=True, nullable=False)
    salt = db.Column(db.Text, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    recovery_code_hash = db.Column(db.Text, nullable=True)
    two_factor_login = db.Column(db.Boolean, nullable=False)


class UserUpdateSignal(db.Model):
    user_update_signal_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('user.user_id'), nullable=False)
    email = db.Column(db.Text, nullable=True)

    def send_signalbus_message(self):
        """Inform the other services that user's email has changed."""

        logger.debug(
            'Triggered sending of user update signal: %i, %i, %s',
            self.user_update_signal_id,
            self.user_id,
            self.email
        )