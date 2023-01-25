from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import TaskForm
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from datetime import datetime, timedelta
import json
           
def index(request):
    return render (request, "lens/index.html")
def new_report_form(request):
    form = TaskForm()
 
    if request.method == "POST":
        form = TaskForm(request.POST)
     
        # check if form data is valid
        if form.is_valid():

            
            # Create a new periodic_task object, but don't save yet
            new_object = form.save(False)

            # Create default flag for "one off" periodic flag
            one_off = False
            
            # Logic for repeat
            if new_object.repeat == "every day":
                delta = 1
            elif new_object.repeat == "every 7 days":
                delta = 7
            else:
                delta = 1
                one_off = True
            
            # Create/Get schedule

            if one_off:
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=5,
                    period=IntervalSchedule.SECONDS
                )
            else:
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=delta,
                    period=IntervalSchedule.DAYS,
                )
            
            # Create scheduled task (for beat)
            periodic_task = PeriodicTask.objects.create(
                interval=schedule,                 
                name='Lens {} {}'.format(new_object.email, str(new_object.start)),          
                task='lens.tasks.report', 
                start_time=new_object.start,
                args = json.dumps([
                    new_object.institution.url, 
                    new_object.api_token,
                    new_object.subject,
                    new_object.term.code,
                    new_object.course_codes,
                    new_object.additional_recipients,
                ]),
                one_off = one_off
            )

            # Update periodic task with scheduled task and save
            new_object.periodic_task = periodic_task
            new_object.save()     

            return HttpResponseRedirect(reverse('lens:thanks'))
        else:
            print("Form is not valid")
 

    return render(request, "lens/new_report_form.html", {"form": form})

def thanks(request):
    return render(request, "lens/thanks.html")
