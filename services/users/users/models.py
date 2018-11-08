import logging
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_signalbus import SignalBus

logger = logging.getLogger(__name__)


class CustomAlchemy(SQLAlchemy):
    def apply_driver_hacks(self, app, info, options):
        if "isolation_level" not in options:
            options["isolation_level"] = "REPEATABLE_READ"
        return super().apply_driver_hacks(app, info, options)


db = CustomAlchemy()
migrate = Migrate(None, db)
signalbus = SignalBus(None, db)


def init_app(app):
    db.init_app(app)
    migrate.init_app(app)
    signalbus.init_app(app)


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
    old_email = db.Column(db.Text, nullable=True)
    new_email = db.Column(db.Text, nullable=True)

    def send_signalbus_message(self):
        """Inform the other services that user's email has changed."""

        logger.debug('Sent user update signal: %i, %s, %s', self.user_id, self.old_email, self.new_email)
