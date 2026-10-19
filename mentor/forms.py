"""
Forms for MentoraX AI.
- BiometricForm: for the fake biometric login (just collects name)
- StudentDataForm: the main data entry form
"""

from django import forms


class BiometricForm(forms.Form):
    """
    Simple form for the biometric login page.
    In a real system this would verify fingerprint/face data.
    For our project, we just ask for student name to set the session.
    """
    student_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your name to authorize...",
            "class": "bio-input",
            "autocomplete": "off",
        }),
        label="Student Name"
    )


class StudentDataForm(forms.Form):
    """
    Main data entry form.
    Collects all the academic variables we need for analysis.
    The OCR part is a placeholder - just a disabled file input for now.
    """

    student_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. STU2024001",
            "class": "form-control",
        }),
        label="Student ID"
    )

    subject_name = forms.CharField(
        max_length=100,
        initial="Mathematics",
        widget=forms.TextInput(attrs={
            "placeholder": "e.g. Mathematics",
            "class": "form-control",
        }),
        label="Subject"
    )

    marks_obtained = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            "placeholder": "e.g. 72",
            "class": "form-control",
            "step": "0.5",
        }),
        label="Marks Obtained"
    )

    total_marks = forms.FloatField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            "placeholder": "e.g. 100",
            "class": "form-control",
            "step": "0.5",
        }),
        label="Total Marks"
    )

    attendance_percent = forms.FloatField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "placeholder": "e.g. 78.5",
            "class": "form-control",
            "step": "0.5",
        }),
        label="Attendance %"
    )

    study_hours_per_week = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            "placeholder": "e.g. 14",
            "class": "form-control",
            "step": "0.5",
        }),
        label="Study Hours / Week"
    )

    # OCR — live via AJAX scan button
    marksheet_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
            "id": "marksheetInput",
        }),
        label="Upload Marksheet Image"
    )

    def clean(self):
        """
        Custom validation:
        marks_obtained cannot be more than total_marks.
        This prevents garbage data from entering the diagnostic engine.
        """
        cleaned_data = super().clean()
        marks = cleaned_data.get("marks_obtained")
        total = cleaned_data.get("total_marks")

        if marks is not None and total is not None:
            if marks > total:
                raise forms.ValidationError(
                    f"Marks obtained ({marks}) cannot be greater than total marks ({total})!"
                )

        return cleaned_data
