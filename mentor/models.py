"""
Models for MentoraX AI.
We store each student analysis record in the database.
This way we can look back at past analyses too.
"""

from django.db import models


class StudentRecord(models.Model):
    """
    Stores all the academic data that was entered for a student.
    One record = one analysis session.
    """

    # Basic student info
    student_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20)

    # Academic data
    subject_name = models.CharField(max_length=100, default="General")
    marks_obtained = models.FloatField()
    total_marks = models.FloatField()
    attendance_percent = models.FloatField()  # e.g. 75.5 means 75.5%
    study_hours_per_week = models.FloatField()

    # Calculated fields (we fill these in the view before saving)
    performance_percent = models.FloatField(default=0)
    tier = models.CharField(max_length=20, default="")  # Excellent / Average / Alert

    # When was this record created
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} ({self.student_id}) - {self.tier}"

    class Meta:
        # Show latest records first in admin
        ordering = ["-created_at"]
