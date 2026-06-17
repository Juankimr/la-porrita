from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pool.urls")),
]

if settings.DEBUG:
    from django.contrib.staticfiles import views
    from django.urls import re_path
    import os

    def serve_static(request, path):
        return views.serve(request, path)

    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve_static),
    ]
