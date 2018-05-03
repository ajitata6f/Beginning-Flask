from application import app, db, api
from flask import render_template, url_for, flash, request, redirect, abort,current_app

from application.product.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, CommentForm
from application.product.models import User, UserRole, Post, Comment
from application.product.rest.api import PostApi, AuthApi
from application.product.utils import send_email
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime

@app.before_request
def before_request():
    authorized_endpoints = ('index', 'confirm', 'signup', 'logout', 'unconfirmed')
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint not in authorized_endpoints:
            return redirect(url_for('unconfirmed'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = User.query.filter_by(username=loginForm.username.data).first()
        if user is not None and user.verify_password(loginForm.password.data):
            login_user(user, loginForm.remember_me.data)
            return redirect(url_for('dashboard')), 302
        flash('user does not exist', 'danger')
    return render_template("index.html", form=loginForm)

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    registrationForm = RegistrationForm()
    if registrationForm.validate_on_submit():
        username = registrationForm.username.data
        password = registrationForm.password.data
        email = registrationForm.email.data

        user = User.query.filter_by(username=registrationForm.username.data).first()
        if user is not None:
            registrationForm.username.errors.append('Username already taken')
        else:
            user_role = UserRole.query.get(2)
            new_user = User(username=username, email=email, role=user_role)
            new_user.password = password
            new_user.role = UserRole.query.filter_by(role_name="user").first()
            db.session.add(new_user)
            db.session.commit()
            token = new_user.generate_confirmation_token()
            send_email('Account Creation', new_user.email,'mail/confirm', user=new_user, token=token)
            flash('account created successfully', 'success')
            return redirect(url_for('index'))
    return render_template('signup.html', form=registrationForm)

@app.route('/dashboard', methods=['POST', 'GET'])
@login_required
def dashboard():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, published_date=datetime.utcnow(), author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('dashboard'))

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.published_date.desc()).paginate(page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items

    return render_template('dashboard.html', form=form, posts=posts, pagination=pagination)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index')), 302

@app.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. thanks!', 'success')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('index'))

@app.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous() or current_user.confirmed:
        return redirect('index')
    return render_template('unconfirmed.html')

@app.route('/resend_confirmation')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email('Account Confirmation', current_user.email, 'mail/confirm', user=current_user, token=token)
    flash('A new confirmation mail has been sent to you by email', 'success')
    return redirect(url_for('index'))

@app.route('/user/<string:username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.published_date.desc()).all()
    return render_template("user.html", user=user, posts=posts)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your profile have been updated', 'success')
        posts = current_user.posts.order_by(Post.time_posted.desc()).all()
        return redirect(url_for('user', username=current_user.username), posts=posts)

    form.firstname.data = current_user.firstname
    form.lastname.data = current_user.lastname
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", form=form)

@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, user=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment have been published', 'success')
        return redirect(url_for('post', id=post.postID))
    return render_template('post.html', posts=[post], form=form, comments=post.comments)

@app.route('/post/edit_post/<int:id>', methods=['GET','POST'])
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('Post successfully updated', 'success')
        return redirect(url_for('dashboard'))
    form.body.data = post.body
    return render_template('edit_post.html', post=post, form=form)

@app.route('/follow/<string:username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User', 'error')
        return redirect(url_for('dashboard'))
    if current_user.is_following(user):
        flash('You are already following this user.', 'warning')
        return redirect(url_for('user', username=user.username))
    current_user.follow(user)
    flash('You are now following {username}'.format(username=user.username), 'success')
    return redirect(url_for('user', username=user.username))

@app.route('/unfollow/<string:username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid User', 'error')
        return redirect(url_for('dashboard'))
    current_user.unfollow(user)
    flash('You have successfully unfollwed {username}'.format(username=user.username), 'success')
    return redirect(url_for('user', username=user.username))

@app.route('/followers/<username>')
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'error')
        redirect(url_for('dashboard'))
    page = request.args.get('page', default=1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FOLLOWERS_PER_PAGE'], error_out=False)
    follows = [{'user':item.follower, 'follow_date':item.follow_date} for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of', endpoint='followers', pagination=pagination, follows=follows)


api.add_resource(PostApi, '/api/post','/api/post/<int:id>' )
api.add_resource(AuthApi, '/api/auth')


