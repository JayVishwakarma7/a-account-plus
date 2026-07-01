import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render

from .forms import ContactForm
from .models import ContactSubmission

logger = logging.getLogger(__name__)


def index(request):
    if request.method == 'POST':
        return handle_contact_submission(request)

    # GET request - just show the page
    return render(request, 'landing/index.html')


def handle_contact_submission(request):
    """Contact form ka JSON submission handle karta hai (validation ke saath)."""
    if request.content_type != 'application/json':
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid request format.'},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON payload.'},
            status=400,
        )

    # BUG FIX: pehle raw dict data.get(...) se seedha DB me save ho raha tha,
    # bina kisi validation ke (khaali/galat email bhi save ho jata).
    # Ab ContactForm (jo forms.py me pehle se defined tha par kabhi use hi
    # nahi ho raha tha) se validate karte hain.
    form = ContactForm(data)
    if not form.is_valid():
        return JsonResponse(
            {'status': 'error', 'message': 'Please check the form details.', 'errors': form.errors},
            status=400,
        )

    submission = form.save()

    subject = f"New Contact Form from {submission.name}"
    body = (
        f"Name: {submission.name}\n"
        f"Email: {submission.email}\n"
        f"Phone: {submission.phone}\n\n"
        f"Message:\n{submission.message}"
    )

    # BUG FIX: pehle send_mail fail hone par (e.g. galat SMTP credentials)
    # poori request 500 error de deti thi, jabki form data DB me save ho
    # chuka hota tha. Ab email fail hone par bhi user ko success hi dikhta
    # hai (data safe hai), sirf error log ho jaata hai.
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.CONTACT_RECEIVER_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception('Contact form email bhejne me error aaya (submission id=%s)', submission.id)

    return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})


@login_required
def clientmail(request):
    # BUG FIX: pehle yahan 'landing/403.html' render hota tha jo file exist
    # hi nahi karti thi -> TemplateDoesNotExist error aata tha.
    # PermissionDenied raise karne se Django ka standard 403 handling milta hai.
    if not request.user.is_staff:
        raise PermissionDenied

    submissions = ContactSubmission.objects.all()
    return render(request, 'landing/clientmail.html', {'submissions': submissions})
