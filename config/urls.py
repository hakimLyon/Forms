from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve as media_serve
from defense import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing, name='landing'),
    path('login/', views.password_gate, name='password_gate'),
    path('sessions/', views.sessions_list, name='sessions_list'),
    path('template/download/', views.download_template, name='download_template'),
    path('template/sample/', views.download_sample, name='download_sample'),
    path('sessions/<int:session_id>/', views.session_rooms, name='session_rooms'),
    path('sessions/<int:session_id>/import/', views.import_excel, name='import_excel'),
    path('sessions/<int:session_id>/room/<int:room_number>/', views.room_students, name='room_students'),
    path('sessions/<int:session_id>/room/<int:room_number>/public/', views.room_public, name='room_public'),
    path('sessions/<int:session_id>/room/<int:room_number>/public/<str:room_token>/', views.room_public_legacy, name='room_public_legacy'),
    path('sessions/<int:session_id>/download-all/<str:fmt>/', views.download_all_pv, name='download_all_pv'),
    path('student/<int:student_id>/start/', views.start_defense, name='start_defense'),
    path('student/<int:student_id>/end/', views.end_defense, name='end_defense'),
    path('student/<int:student_id>/pv/', views.pv_overview, name='pv_overview'),
    path('student/<int:student_id>/pv/<str:fmt>/', views.download_pv, name='download_pv'),
    path('student/<int:student_id>/detail/', views.student_detail, name='student_detail'),
    path('student/<int:student_id>/detail/pdf/', views.download_detail_pdf, name='download_detail_pdf'),
    path('defense/<str:token>/', views.defense_entry, name='defense_entry'),
    path('defense/<str:token>/panel/', views.panel_members, name='panel_members'),
    path('defense/<str:token>/end/', views.end_defense_from_panel, name='end_defense_from_panel'),
    path('defense/<str:token>/eval/<int:member_index>/', views.evaluation_form, name='evaluation_form'),
    path('defense/<str:token>/result/<int:eval_id>/', views.evaluation_result, name='evaluation_result'),
    path('defense/<str:token>/continue/<str:edit_token>/', views.evaluation_edit_link, name='evaluation_edit_link'),
    # Serve uploaded media in production (static is handled by WhiteNoise).
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]
