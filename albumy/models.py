import os
from datetime import datetime

from flask import current_app
from flask_avatars import Identicon
from flask_login import UserMixin
from sqlalchemy.util import symbol
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, whooshee


@whooshee.register_model('name', 'username')
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(254), unique=True, index=True)
    username = db.Column(db.String(20), unique=True, index=True)
    _password_hash = db.Column(db.String(128))
    website = db.Column(db.String(255))
    bio = db.Column(db.String(120))
    location = db.Column(db.String(50))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed = db.Column(db.Boolean, default=False)
    avatar_raw = db.Column(db.String(64))
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    receive_comment_notification = db.Column(db.Boolean, default=True)
    receive_follow_notification = db.Column(db.Boolean, default=True)
    receive_collect_notification = db.Column(db.Boolean, default=True)
    public_collections = db.Column(db.Boolean, default=True)
    locked = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')
    photos = db.relationship('Photo', back_populates='author', cascade='all')
    comments = db.relationship('Comment', back_populates='author')
    collections = db.relationship('Collect', back_populates='collector', cascade='all')
    following = db.relationship('Follow', back_populates='follower', foreign_keys='[Follow.follower_id]',
                                cascade='all', lazy='dynamic')
    followers = db.relationship('Follow', back_populates='followed', foreign_keys='[Follow.followed_id]',
                                cascade='all', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='receiver', cascade='all')

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.set_role()
        self.generate_avatar()
        self.follow(self)

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(self.name)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]

    def set_role(self):
        if self.role is None:
            if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='Normal').first()

    def collect(self, photo):
        if not self.is_collecting(photo):
            collect = Collect(collector=self, collected=photo)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_collecting(self, photo):
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def is_following(self, user):
        if user.id is None:
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = Follow.query.filter(Follow.follower == self, Follow.followed == user).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def lock(self):
        if not self.is_admin:
            self.locked = True
            self.role = Role.query.filter_by(name='Locked').first()
            db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='Normal').first()
        db.session.commit()

    @property
    def is_active(self):
        return self.active

    def block(self):
        if not self.is_admin:
            self.active = False
            db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

    @property
    def password(self):
        raise AttributeError('password can not readable')

    @password.setter
    def password(self, value):
        self._password_hash = generate_password_hash(value)

    def validate_password(self, password):
        return check_password_hash(self._password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    level = db.Column(db.Integer)
    permissions = db.relationship('Permission', back_populates='roles', secondary='roles_permissions')
    users = db.relationship('User', back_populates='role')

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked': {'permissions': ['FOLLOW', 'COLLECT'], 'level': 100},
            'Normal': {'permissions': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'], 'level': 50},
            'Moderator': {'permissions': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'], 'level': 1},
            'Administrator': {'permissions': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER'],
                              'level': 0}
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name, level=roles_permissions_map[role_name]['level'])
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]['permissions']:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)
    roles = db.relationship('Role', back_populates='permissions', secondary='roles_permissions')

    def __repr__(self):
        return '<Permission %r>' % self.name


roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')))


@whooshee.register_model('description')
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64))
    filename_m = db.Column(db.String(64))
    filename_s = db.Column(db.String(64))
    flag = db.Column(db.Integer, default=0)
    description = db.Column(db.String(500))
    can_comment = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='photos')
    tags = db.relationship('Tag', back_populates='photos', secondary='tagging')
    comments = db.relationship('Comment', back_populates='photo', cascade='all')
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')


@whooshee.register_model('name')
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True)
    photos = db.relationship('Photo', back_populates='tags', secondary='tagging')

    def __repr__(self):
        return '<Tag %r>' % self.name


tagging = db.Table('tagging',
                   db.Column('photo_id', db.ForeignKey('photo.id')),
                   db.Column('tag_id', db.ForeignKey('tag.id')))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    flag = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    photo = db.relationship('Photo', back_populates='comments')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='comments')
    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])
    replies = db.relationship('Comment', back_populates='replied', cascade='all')


class Collect(db.Model):
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    collector = db.relationship('User', back_populates='collections', lazy='joined')
    collected_id = db.Column(db.Integer, db.ForeignKey('photo.id'), primary_key=True)
    collected = db.relationship('Photo', back_populates='collectors', lazy='joined')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver = db.relationship('User', back_populates='notifications')


@db.event.listens_for(Photo, 'after_delete')
def delete_photos(mapper, connection, target):
    for filename in [target.filename, target.filename_s, target.filename_m]:
        if filename is not None:
            path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
            if os.path.exists(path):
                os.remove(path)


@db.event.listens_for(User.avatar_raw, 'set')
def change_avatar(target, value, oldvalue, initiator):
    if oldvalue and symbol('NO_VALUE') != oldvalue:
        path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], oldvalue)
        if os.path.exists(path):
            os.remove(path)


@db.event.listens_for(User.avatar_s, 'set')
def change_avatar(target, value, oldvalue, initiator):
    if symbol('NO_VALUE') != oldvalue:
        path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], oldvalue)
        if os.path.exists(path):
            os.remove(path)


@db.event.listens_for(User.avatar_m, 'set')
def change_avatar(target, value, oldvalue, initiator):
    if symbol('NO_VALUE') != oldvalue:
        path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], oldvalue)
        if os.path.exists(path):
            os.remove(path)


@db.event.listens_for(User.avatar_l, 'set')
def change_avatar(target, value, oldvalue, initiator):
    if symbol('NO_VALUE') != oldvalue:
        path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], oldvalue)
        if os.path.exists(path):
            os.remove(path)


@db.event.listens_for(User, 'after_delete')
def delete_user(mapper, connection, target):
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):
                os.remove(path)
