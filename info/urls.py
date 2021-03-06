"""
Url design for the info app.
"""
from django.conf.urls import include, url
from . import views

app_name = 'info'

urlpatterns = [
    url(r'^about$', views.about, name='about'),
    url(r'^help$', views.help, name='help'),
    url(r'^imprint$', views.imprint, name='imprint'),
    url(r'^terms$', views.terms, name='terms'),
    url(r'^privacy$', views.privacy, name='privacy'),
]
