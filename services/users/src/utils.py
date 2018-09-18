import re
import random
import string
from crypt import crypt


EMAIL_REGEX = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
PASSWORD_SALT_CHARS = string.digits + string.ascii_letters + './'


def generate_password_salt(method):
    salt = '$%s$' % method if method else ''
    salt += ''.join(random.choice(PASSWORD_SALT_CHARS) for _ in range(16))
    return salt


def calc_crypt_hash(salt, message):
    return crypt(message, salt)


def is_invalid_email(email):
    return not EMAIL_REGEX.match(email)
