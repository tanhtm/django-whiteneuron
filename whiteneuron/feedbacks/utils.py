from apps.base.utils import base_badge_callback
from .models import FeedbackData

def feedback_data_badge_callback(request):
    return base_badge_callback(request, FeedbackData)