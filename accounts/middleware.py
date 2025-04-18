# your_app/middleware.py

from datetime import datetime
from django.utils.timezone import make_aware

class TrackLastLoginMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            # Update the last login timestamp to current time
            request.user.last_login = make_aware(datetime.now())  # Ensure it's timezone-aware
            request.user.save()

        # Continue processing the request
        response = self.get_response(request)
        return response