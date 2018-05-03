from flask_mail import Message
from flask import render_template
from application import mail

def send_email(subject, to, template, **kwargs):
    message = Message(subject, sender='ajitata6f@gmail.com', recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    mail.send(message)