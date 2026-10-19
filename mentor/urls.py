"""
URL patterns for the mentor app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("",            views.home_page,      name="home_page"),
    path("scan/",       views.biometric_scan, name="biometric_scan"),
    path("authorize/",  views.authorize,      name="authorize"),
    path("input/",      views.data_input,     name="data_input"),
    path("dashboard/",  views.dashboard,      name="dashboard"),
    path("logout/",     views.logout_user,    name="logout_user"),
    path("about/",      views.about_page,     name="about_page"),
    path("ocr/",        views.ocr_scan,       name="ocr_scan"),
]
