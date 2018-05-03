import hashlib

from application import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import AnonymousUserMixin
from application import login_manager
from itsdangerous import URLSafeTimedSerializer as Serializer, SignatureExpired, BadSignature
from flask import current_app, request, flash
from datetime import datetime

class Follow(db.Model):
    __tablename__ = 'follows'
    followerID = db.Column(db.Integer(), db.ForeignKey('users.userID'), primary_key=True)
    followedID = db.Column(db.Integer(), db.ForeignKey('users.userID'),  primary_key=True)
    follow_date = db.Column(db.DateTime, default=datetime.utcnow())

class User(db.Model):
    __tablename__ = 'users'
    userID = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    username = db.Column(db.String(45), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    confirmed = db.Column(db.Boolean(), default=False, nullable=False)
    firstname = db.Column(db.String(45))
    lastname = db.Column(db.String(45))
    email = db.Column(db.String(45), nullable=False)
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.followerID], backref=db.backref('follower', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    followers = db.relationship('Follow', foreign_keys=[Follow.followedID], backref=db.backref('followed', lazy='joined'), lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    roleID = db.Column(db.Integer(), db.ForeignKey('user_role.roleID'))

    @property
    def password(self):
        raise AttributeError('Password is not readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        if isinstance(self, AnonymousUserMixin):
            return False
        else:
            return True

    def is_active(self):
        return True

    def is_anonymous(self):
        if isinstance(self, AnonymousUserMixin):
            return True
        else:
            return False

    def get_id(self):
        return self.userID

    @login_manager.user_loader
    def load_user(userID):
        return User.query.get(int(userID))

    def generate_confirmation_token(self):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.userID)

    def confirm(self, token, expiration=3600):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, max_age=expiration)
        except:
            return False

        if data != self.userID:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'

        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url=url, hash=hash,size=size, default=default, rating=rating )

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followedID=user.userID).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def is_following(self, user):
        return self.followed.filter_by(followedID=user.userID).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(followerID=user.userID).first() is not None

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import  IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            role = UserRole.query.get(2)
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     firstname=forgery_py.name.first_name(),
                     lastname=forgery_py.name.last_name(),
                     location=forgery_py.name.location(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True),
                     role=role)
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError as err:
                print(err)
                db.session.rollback()

    @staticmethod
    def verify_auth_token(token):
        serializer = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token)
        except SignatureExpired as ex:
            flash('Token has expired', 'error')
        except BadSignature:
            flash('Signature doesn\'t match', 'error')

        user = User.query.get(data['id'])
        return user





    def __repr__(self):
        return "<User '{}'>".format(self.username)


class UserRole(db.Model):
    __tablename__ = 'user_role'
    roleID = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    role_name = db.Column(db.String(45), nullable=False)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return "<Role '{}'>".format(self.role_name)

class Post(db.Model):
    __tablename__ = 'posts'
    postID = db.Column(db.Integer(), primary_key=True, nullable=False)
    body = db.Column(db.Text())
    published_date = db.Column(db.DateTime(), index=True, default= datetime.utcnow())
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    userID = db.Column(db.Integer(), db.ForeignKey('users.userID'))

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(1,3),
                     published_date=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()

class Comment(db.Model):
    __tablename__='comments'
    commentID = db.Column(db.Integer(), primary_key=True)
    body = db.Column(db.Text())
    comment_date = db.Column(db.DateTime(), default=datetime.utcnow())
    disabled = db.Column(db.Boolean(), default=False)
    userID = db.Column(db.Integer(), db.ForeignKey('users.userID'))
    postID = db.Column(db.Integer(), db.ForeignKey('posts.postID'))




