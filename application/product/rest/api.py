import json

from flask_restful import Resource, reqparse
from flask import jsonify, abort

from application import db, app
from application.product.models import Post, UserRole, User
from application.product.rest.parser import post_parser, user_parser
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class PostApi(Resource):

    def get(self, id=None, page=1):
        if not id:
            posts = Post.query.paginate(page, 10).items
        else:
            posts = [Post.query.get(id)]

        if not posts:
            abort(404)

        resource = {}
        for post in posts:
            resource[post.postID] = {
                'authorID': post.author.userID,
                'body': post.body,
                'comment_count': post.comments.count(),
                'comments': [comment.body for comment in post.comments],
                'published_date': post.published_date
            }

        return jsonify(resource)

    def post(self):
        args = post_parser.parse_args()
        body = args['body']
        published_date = args['published_date']
        token = args['token']

        user = User.verify_auth_token(token)
        if not user:
            abort(401)

        post = Post(body=body, published_date=published_date, author=user)
        db.session.add(post)
        db.session.commit()

        return jsonify({'status':'post created successfully'})


    def put(self, id=None):
        if id is None:
            abort(400)

        post = Post.query.get(id)

        if post is None:
            abort(404)

        args = post_parser.parse_args()
        post.body = args['body']
        db.session.add(post)
        db.session.commit()

        return jsonify({'status':'post successfully updated'})

    def delete(self, id=None):
        if id is None:
            abort(400)

        post = Post.query.get(id)

        if post is None:
            abort(404)

        db.session.delete(post)
        db.session.commit()

        return jsonify({'status':'post successfully deleted'})


class AuthApi(Resource):
    def post(self):
        args = user_parser.parse_args()
        user = User.query.filter_by(username=args['username']).first()

        if user.verify_password(args['password']):
            serializer = Serializer(secret_key=app.config['SECRET_KEY'], expires_in=600)
            return serializer.dumps({'id',user.userID})
        else:
            abort(401)



