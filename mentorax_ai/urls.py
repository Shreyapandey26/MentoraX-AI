"""
Main URL config for MentoraX AI.
We just include all URLs from the 'mentor' app here.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # All our mentor app URLs start from root "/"
    path("", include("mentor.urls")),
]
