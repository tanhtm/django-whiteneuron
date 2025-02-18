from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.base.models import BaseModel 

# Feedback
# Đề xuất thay đổi dữ liệu
class FeedbackData(BaseModel):
    user = models.ForeignKey(
        "base.User",
        on_delete=models.CASCADE,
        related_name="feedbacks",
        verbose_name=_("User")
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("Content Type")
    )

    object_id = models.PositiveIntegerField(
        verbose_name=_("Object ID")
    )

    content_object = GenericForeignKey('content_type', 'object_id')

    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("The message of the feedback")
    )

    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_("Is Resolved"),
        help_text=_("Whether the feedback is resolved")
    )

    note= models.TextField(
        verbose_name=_("Note"),
        help_text=_("Admin note for the feedback"),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedbacks")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.user} - {self.content_type}({self.object_id})'
    


    


