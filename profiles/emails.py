from django.core.mail import EmailMultiAlternatives
from django.template import loader

import winrepo.settings as settings


def build_email(subject_template_name, email_template_name, html_email_template_name, context=None, reply=False):

    subject = loader.render_to_string(subject_template_name, context)
    subject = settings.EMAIL_SUBJECT_PREFIX + ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    headers = {}
    if reply:
        headers['Reply-To'] = settings.EMAIL_REPLY_TO
    
    email_message = EmailMultiAlternatives(subject, body, settings.EMAIL_FROM, None, headers=headers)
    html_email = loader.render_to_string(html_email_template_name, context)
    email_message.attach_alternative(html_email, 'text/html')

    email_message.context = context

    return email_message


def user_update_email(
    request, user,
    subject_template_name='account/user_update_email_subject.txt',
    email_template_name='account/user_update_email_body.txt',
    html_email_template_name='account/user_update_email_body.html'
):
    context = {
        "request": request,
        "user": user,
    }

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context,
        True,
    )
    message.to = [user.email]
    return message


def user_update_email_email(
    request, user, token,
    subject_template_name='account/user_update_email_email_subject.txt',
    email_template_name='account/user_update_email_email_body.txt',
    html_email_template_name='account/user_update_email_email_body.html'
):
    context = {
        "request": request,
        "user": user,
        "token": token,
    }

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context,
        True,
    )
    message.to = [user.email]
    return message


def profile_update_email(
    request, user, profile,
    subject_template_name='profiles/profile_update_email_subject.txt',
    email_template_name='profiles/profile_update_email_body.txt',
    html_email_template_name='profiles/profile_update_email_body.html'
):
    context = {
        "request": request,
        "user": user,
        "profile": profile,
    }

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context,
        True,
    )
    message.to = [user.email]
    return message


def user_create_confirm_email(
    request, user, token,
    subject_template_name='registration/signup_confirm_email_subject.txt',
    email_template_name='registration/signup_confirm_email_body.txt',
    html_email_template_name='registration/signup_confirm_email_body.html'
):
    context = {
        "request": request,
        "user": user,
        "token": token,
    }

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context
    )
    message.to = [user.email]
    return message


def user_reset_password_email(
    request, user, token,
    subject_template_name='registration/reset_password_email_subject.txt',
    email_template_name='registration/reset_password_email_body.txt',
    html_email_template_name='registration/reset_password_email_body.html'
):
    context = {
        "request": request,
        "user": user,
        "token": token,
    }

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context
    )
    message.to = [user.email]
    return message


def test_email(
    to,
    subject_template_name='test_email_subject.txt',
    email_template_name='test_email_body.txt',
    html_email_template_name='test_email_body.html'
):
    context = {}

    message = build_email(
        subject_template_name,
        email_template_name,
        html_email_template_name,
        context
    )
    message.to = [to]
    return message
