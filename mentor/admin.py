from django.contrib import admin
from .models import StudentRecord


@admin.register(StudentRecord)
class StudentRecordAdmin(admin.ModelAdmin):
    list_display = ["student_name", "student_id", "subject_name", "performance_percent", "tier", "created_at"]
    list_filter = ["tier"]
    search_fields = ["student_name", "student_id"]
