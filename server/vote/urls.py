from django.urls import path
from . import views

app_name = "vote"

urlpatterns = [
    #공통
    path("", views.main, name="main"),
    path('<int:poll_id>/', views.poll_detail, name='detail'),
    path("<int:poll_id>/classifyuser", views.classifyuser, name="classifyuser"),
    path("<int:poll_id>/calcstat", views.calcstat, name="calcstat"),

    #유저
    path('like/', views.poll_like, name='like'),
    path('mypage/', views.mypage, name='mypage'),
    path('mypage/update/', views.mypage_update, name='update'),
    path('<int:poll_id>/comment/write/', views.comment_write_view, name='comment_write'),
    path('<int:pk>/comment/delete/', views.comment_delete_view, name='comment_delete'),

    #논유저
    path('<int:poll_id>/<int:nonuservote_id>', views.poll_nonusergender, name='nonusergender'),
    path('<int:poll_id>/<int:nonuservote_id>/1', views.poll_nonusermbti, name='nonusermbti'),
    path('<int:poll_id>/<int:nonuservote_id>/1/1', views.poll_nonuserfinal, name='nonuserfinal'),
    
    ]
