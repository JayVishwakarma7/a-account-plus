import json
import logging
import resend
from .models import Review

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
    
    reviews = Review.objects.all()[:6]

    # GET request - just show the page
    return render(request, 'landing/index.html')

def submit_review(request):
    if request.method == 'POST':
        from .forms import ReviewForm
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Review submitted!'})
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

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

    # Direct Resend API use karo (bina SMTP ke)
    try:
        resend.api_key = settings.RESEND_API_KEY
        
        params = {
            "from": "Contact Form <onboarding@resend.dev>",
            "to": [settings.CONTACT_RECEIVER_EMAIL],
            "subject": subject,
            "html": f"""
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {submission.name}</p>
            <p><strong>Email:</strong> {submission.email}</p>
            <p><strong>Phone:</strong> {submission.phone}</p>
            <p><strong>Message:</strong></p>
            <p>{submission.message}</p>
            """,
        }
        
        email = resend.Emails.send(params)
        logger.info(f'Email sent successfully via Resend: {email}')
        
    except Exception as e:
        logger.exception(f'Contact form email bhejne me error aaya (submission id={submission.id}): {str(e)}')

    return JsonResponse({'status': 'success', 'message': 'Message sent successfully!'})


@login_required
def clientmail(request):
    if not request.user.is_staff:
        raise PermissionDenied

    submissions = ContactSubmission.objects.all()
    return render(request, 'landing/clientmail.html', {'submissions': submissions})