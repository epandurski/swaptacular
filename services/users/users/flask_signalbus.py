import time
import logging
import threading
from functools import wraps, partial
from sqlalchemy import event
from sqlalchemy.exc import DBAPIError


logger = logging.getLogger(__name__)


ERROR_CODE_ATTRS = ['pgcode', 'sqlstate']  # psycopg2/psycopg2cffi, MySQL Connector
DEADLOCK_ERROR_CODES = ['40001', '40P01']


def get_db_error_code(exception):
    for attr in ERROR_CODE_ATTRS:
        error_code = getattr(exception, attr, '')
        if error_code:
            break
    return error_code


def retry_on_deadlock(session, retries=6, min_wait=0.1, max_wait=10.0, rollback=False):
    """Return a function decorator."""

    def decorator(action):
        """Function decorator that retries 'action' in case of a deadlock."""

        @wraps(action)
        def f(*args, **kwargs):
            num_failures = 0
            while True:
                try:
                    return action(*args, **kwargs)
                except DBAPIError as e:
                    num_failures += 1
                    if num_failures > retries or get_db_error_code(e.orig) not in DEADLOCK_ERROR_CODES:
                        if rollback:
                            session.rollback()
                        raise
                session.rollback()
                wait_seconds = min(max_wait, min_wait * 2 ** (num_failures - 1))
                time.sleep(wait_seconds)

        return f

    return decorator


class SignalBus:
    def __init__(self, app, db):
        self.app = app
        self.db = db
        self.signal_session = db.create_scoped_session({'expire_on_commit': False})
        self.event_handlers = {}
        self.event_handlers_lock = threading.Lock()
        self.retry_on_deadlock = retry_on_deadlock(self.signal_session, rollback=True)

    def send(self, instance, session=None):
        model = type(instance)
        assert hasattr(model, 'send_message'), '{} does not have method "send_message". '.format(model.__name__)
        if session is None:
            session = self.db.session
        if event.contains(session, 'transient_to_pending', self.transient_to_pending_handler):
            logger.warning('Use of SignalBus.send while "transient_to_pending" handler is configured.')
        session.add(instance)
        self._attach_commit_handler(model, session)

    def process_signals(self, model, session=None):
        return self.retry_on_deadlock(self._process_signals)(model)

    def transient_to_pending_handler(self, session, instance):
        model = type(instance)
        if hasattr(model, 'send_message'):
            self._attach_commit_handler(model, session)
            logger.debug('A commit handler for %s has been added to session.', model.__name__)

    def _attach_commit_handler(self, model, session):
        with self.event_handlers_lock:
            if model not in self.event_handlers:
                self.event_handlers[model] = partial(self.process_signals, model)
            event_handler = self.event_handlers[model]
            if event.contains(session, 'after_commit', event_handler):
                event.remove(session, 'after_commit', event_handler)
            event.listen(session, 'after_commit', event_handler, once=True)

    def _process_signals(self, model):
        for record in self.signal_session.query(model).all():
            self.signal_session.delete(record)
            self.signal_session.flush()
            record.send_message()
            self.signal_session.commit()
        self.signal_session.expire_all()
        self.signal_session.commit()
