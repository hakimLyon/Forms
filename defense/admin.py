from django.contrib import admin
from django.utils.html import format_html
from .models import SitePassword, PVSettings, Session, Student, Evaluation


@admin.register(PVSettings)
class PVSettingsAdmin(admin.ModelAdmin):
    list_display = ['director_name', 'director_title', 'institution_name']

    def has_add_permission(self, request):
        # Only allow one PVSettings record (singleton)
        return not PVSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SitePassword)
class SitePasswordAdmin(admin.ModelAdmin):
    list_display = ['password']


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ['time', 'surname', 'given_names', 'room', 'defense_date', 'defense_status']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'program', 'is_active', 'created_at']
    inlines = [StudentInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'session', 'room', 'time', 'defense_date', 'defense_status']
    list_filter = ['session', 'room', 'defense_status', 'defense_date']
    search_fields = ['surname', 'given_names', 'thesis_title']
    list_editable = ['defense_status']
    actions = ['reset_start']

    def reset_start(self, request, queryset):
        queryset.update(defense_status='pending', started_at=None, start_link_token=None)
        self.message_user(request, "Selected students reset to pending.")
    reset_start.short_description = "Reset defense start (admin)"

    fieldsets = (
        ('Student Info', {'fields': ('session', 'time', 'surname', 'given_names', 'thesis_title', 'room', 'defense_date')}),
        ('Supervisor(s)', {'fields': ('supervisor_1_name', 'supervisor_1_email', 'supervisor_1_institution', 'supervisor_2_name', 'supervisor_2_email')}),
        ('Jury President', {'fields': ('jury_president_name', 'jury_president_email', 'jury_president_affiliation')}),
        ('Examiners', {'fields': ('examiner_1_name', 'examiner_1_email', 'examiner_1_affiliation', 'examiner_2_name', 'examiner_2_email', 'examiner_2_affiliation', 'examiner_3_name', 'examiner_3_email', 'examiner_3_affiliation')}),
        ('Status', {'fields': ('defense_status', 'started_at', 'ended_at', 'start_link_token')}),
    )


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['evaluator_name', 'student', 'role', 'total_score_raw', 'grade_label', 'submitted_at']
    list_filter = ['role', 'student__session']
    readonly_fields = ['submitted_at']
