from datetime import datetime

from flask_restful import reqparse

post_parser = reqparse.RequestParser()
post_parser.add_argument('body', type=str)
post_parser.add_argument('published_date', type=datetime)
post_parser.add_argument('userID', type=int)
post_parser.add_argument('token', type=str, required=True, help='Auth token is required to create a post')

user_parser = reqparse.RequestParser()
user_parser.add_argument('username', type=str, required=True)
user_parser.add_argument('password', type=str, required=True)