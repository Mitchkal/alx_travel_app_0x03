from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_booking_confirmation_email(booking, from_email=None):
    """
    Celery task tosend booking confirmation email asynchronously
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    subject = f"Booking Confirmation: {booking.id}"
    message = f"Dear {booking.user.username},\n'nYour booking for {booking.listing.title} has been confirmed.\n\nThank you for choosing us!"
    recipient_list = [booking.user.email]
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        html_message=message.replace("\n", "<br>"),
        fail_silently=False,
    )
    return f"Email sent to {booking.user.email} for booking {booking.id}"
