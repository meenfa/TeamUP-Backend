from urllib.parse import urlencode

from django.conf import settings
from django.core import signing


TOKEN_SALT = 'accounts.email_verification'


def build_email_verification_token(user):
    return signing.dumps({'user_id': user.id, 'email': user.email}, salt=TOKEN_SALT)


def load_email_verification_token(token):
    return signing.loads(
        token,
        salt=TOKEN_SALT,
        max_age=settings.EMAIL_VERIFICATION_TOKEN_MAX_AGE_SECONDS,
    )


def build_email_verification_url(token):
    query_string = urlencode({'token': token})
    separator = '&' if '?' in settings.EMAIL_VERIFICATION_URL else '?'
    return f'{settings.EMAIL_VERIFICATION_URL}{separator}{query_string}'
