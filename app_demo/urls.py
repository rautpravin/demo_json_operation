from django.urls import path
from app_demo.views import UpdateJSON, download, UpdateMergeSection

urlpatterns = [
    path('download/<str:path>', download, name='download'),
    path('', UpdateJSON.as_view(), name='index'),
    path('merge-sec', UpdateMergeSection.as_view(), name='merge-sec'),
]
