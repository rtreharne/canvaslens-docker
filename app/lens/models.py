from django.db import models
import datetime
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

class Institute(models.Model):
    name = models.CharField(max_length=128)
    url = models.URLField()

    def __str__(self):
        return self.name

class Term(models.Model):
    code = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.code

class TaskDetail(models.Model):

    REPEAT_CHOICES = (
        ("one-off task", "One-off Task"),
        ("every day", "Every Day"),
        ("every 7 days", "Every Week")
    )

    email = models.EmailField()
    institution = models.ForeignKey(Institute, on_delete=models.CASCADE)
    api_token = models.CharField(max_length=128, help_text="For help on how to generate your API TOKEN click <a href='https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-manage-API-access-tokens-as-an-instructor/ta-p/1177' target='_blank'>here</a>.")
    subject = models.CharField(blank=True, max_length=4, default="", null=True, help_text="For example: LIFE, MATH, ARCH, etc ...")
    course_codes = models.TextField(blank=True, default=None, verbose_name="Additional Courses")
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    start = models.DateTimeField(default=timezone.now)
    repeat = models.CharField(max_length=20, choices=REPEAT_CHOICES, default="one-off task")
    additional_recipients = models.TextField(blank=True, default="", null=True)
    periodic_task = models.ForeignKey(PeriodicTask, on_delete=models.CASCADE, default=None, blank=True, null=True)

    def __str__(self):
        return self.email

