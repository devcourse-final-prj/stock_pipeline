"""
URL configuration for stock_data_flow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from superset.views import ml_view, treemap_view
from viz.views import calc_view, graph_view

urlpatterns = [
    path('', include('homepage.urls')),
    path('ml/', ml_view, name='ml_page'),
    path('treemap/', treemap_view, name='treemap_page'),
    path('calc/', calc_view, name='calc_page'),
    path('graph/', graph_view, name='graph_page'),
    path('admin/', admin.site.urls),
    path('viz/', include('viz.urls')),
]
