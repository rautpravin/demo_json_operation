from django.urls import path
from app_demo.views import UpdateJSON, download

urlpatterns = [
    path('download/<str:path>', download, name='download'),
    path('', UpdateJSON.as_view(), name='index'),
]
