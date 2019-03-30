from urllib.parse import urlparse, urljoin

from flask import request, redirect, url_for, flash, current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature

from .extensions import db
from .settings import Operations


def is_safe_url(target):
    ref_url = urlparse(request.full_path)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and test_url.netloc == ref_url.netloc


def redirect_back(default='main.index', **kwargs):
    for target in (request.args.get('next'), request.referrer):
        if not target:
            continue
        if is_safe_url(target):
            return redirect(target)
    return redirect(url_for(default, **kwargs))


def generate_token(user, operation, expires_in=None, **kwargs):
    s = Serializer(current_app.config['SECRET_KEY'], expires_in)
    data = dict(id=user.id, operation=operation)
    data.update(**kwargs)
    return s.dumps(data).decode()


def validate_token(token, user, operation, password=None):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (SignatureExpired, BadSignature):
        return False
    if data.get('id') != user.id or data.get('operation') != operation:
        return False

    if operation == Operations.CONFIRM:
        user.confirmed = True
    if operation == Operations.RESET_PASSWORD:
        user.password = password
    else:
        return False

    db.session.commit()
    return True


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('%s字段中有错误:%s' % (getattr(form, field).label.text, error), 'dangers')