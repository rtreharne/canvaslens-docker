from django.urls import path

from . import views

app_name = 'lens'
urlpatterns = [
    path('', views.index, name='index'),
    path('new-report/', views.new_report_form, name='new-report'),
    path('thanks/', views.thanks, name='thanks'),
    path('quickstart/', views.quickstart, name='quickstart')
]