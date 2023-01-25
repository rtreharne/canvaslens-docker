from django.forms import ModelForm, DateTimeField, DateTimeInput
from .models import TaskDetail

class TaskForm(ModelForm):

    class Meta:
        model = TaskDetail
        exclude = ('periodic_task', 'start', 'additional_recipients')