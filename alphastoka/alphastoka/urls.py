"""alphastoka URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from mgmt import views
from datetime import datetime
from django.template.defaulttags import register

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^mgmt/create', views.mgmt_create),
    url(r'^mgmt/murder/([^\s]+)', views.mgmt_murder),
    url(r'^results', views.results),
    # default first view
    url(r'^$', views.index)
]

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def unixtime(intTime):
    that = datetime.fromtimestamp(int(intTime))
    total_time=(datetime.now() - that)

    return str(total_time).split(".")[0]
