from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views
from myapp.notif_scheduler import NotificationsScheduler

urlpatterns = [
    path('<str:page>/', views.index, name='index'),
    path('', views.index, name='index'),
    path('stock/<str:symbol>/', views.single_stock, name='single_stock'),
    # path('historic/<str:symbol>/', views.single_stock_historic, name='single_stock_historic'),
    # path('api/wikiInfo/<str:company_name>', views.get_wiki_info, name="get_wiki_info"),
    path('api/historic/<str:symbol>/<str:time_range>/', views.single_stock_historic, name='single_stock_historic'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.user_profile, name='profile'),
    path('accounts/edit_profile/', views.edit_profile, name='edit_profile'),
    path('notification/add/', views.add_notification, name='notification'),  # add notification to db
    path('accounts/my_notifications/', views.my_notifications, name='my_notifications'),
    path('notification/delete_active/<str:pk>', views.delete_active_notification, name='delete_active_notification'),
    path('notification/delete_waiting/<str:pk>', views.delete_waiting_notification, name='delete_waiting_notification'),
    path('notification/delete_tracking/<str:pk>', views.delete_tracking_notification,
         name='delete_tracking_notification'),
    path('notification/delete_analyst_rec/<str:pk>', views.delete_analyst_notification,
         name='delete_analyst_notification'),
    path('company/get_description/<str:company_symbol>', views.get_company_desc, name="get_company_description"),
    path('tracking/add/', views.add_tracking, name='add_tracking'),
    path('notification_analyst/add/', views.add_notification_analyst, name='notification-analyst'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += staticfiles_urlpatterns()

scheduler = NotificationsScheduler()
scheduler.start()  # this will start the notifications scheduler
