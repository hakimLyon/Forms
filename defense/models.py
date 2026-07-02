from django.db import models


class SitePassword(models.Model):
    password = models.CharField(max_length=100, default='aimssn')
    class Meta:
        verbose_name = "Site Password"
    def __str__(self):
        return f"Site Password: {self.password}"


class PVSettings(models.Model):
    """
    Global PV (Proces-Verbal / Defense Report) settings.
    Centralizes the signature block and logo used in every generated PV
    (Word and PDF, single download or ZIP export).
    """
    director_name = models.CharField(
        max_length=200, default="Dr. Coura Balde",
        help_text="Full name shown in the signature block, e.g. 'Dr. Coura Balde'"
    )
    director_title = models.CharField(
        max_length=200, default="Academic Manager, AIMS Senegal",
        help_text="Title/role shown under the name, e.g. 'Academic Manager, AIMS Senegal'"
    )
    institution_name = models.CharField(
        max_length=200, default="AIMS Senegal",
        help_text="Institution name (used for reference, not always printed)"
    )
    logo = models.ImageField(
        upload_to='pv_settings/', blank=True, null=True,
        help_text="Logo shown in the PV header. If empty, the default AIMS logo is used."
    )

    class Meta:
        verbose_name = "PV Settings"
        verbose_name_plural = "PV Settings"

    def __str__(self):
        return f"PV Settings ({self.director_name})"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class Session(models.Model):
    name = models.CharField(max_length=200)
    number_of_years = models.IntegerField(default=1)
    program = models.CharField(max_length=200, default="Cooperative Masters")
    academic_year = models.CharField(max_length=20, default="2024-2026")
    excel_file = models.FileField(upload_to='excel/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class Student(models.Model):
    ROOM_CHOICES = [(1, 'AIMS Room 1'), (2, 'AIMS Room 2')]
    DEFENSE_STATUS = [
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='students')
    id_student = models.CharField(max_length=50, blank=True, default='')
    time = models.CharField(max_length=20, blank=True)
    surname = models.CharField(max_length=100)
    given_names = models.CharField(max_length=200)
    thesis_title = models.TextField()
    room = models.IntegerField(choices=ROOM_CHOICES, default=1)
    defense_date = models.DateField(null=True, blank=True)

    supervisor_1_name        = models.CharField(max_length=200, blank=True)
    supervisor_1_email       = models.CharField(max_length=200, blank=True)
    supervisor_1_institution = models.CharField(max_length=200, blank=True)
    supervisor_2_name        = models.CharField(max_length=200, blank=True)
    supervisor_2_email       = models.CharField(max_length=200, blank=True)

    jury_president_name        = models.CharField(max_length=200, blank=True)
    jury_president_email       = models.CharField(max_length=200, blank=True)
    jury_president_affiliation = models.CharField(max_length=200, blank=True)

    examiner_1_name        = models.CharField(max_length=200, blank=True)
    examiner_1_email       = models.CharField(max_length=200, blank=True)
    examiner_1_affiliation = models.CharField(max_length=200, blank=True)
    examiner_2_name        = models.CharField(max_length=200, blank=True)
    examiner_2_email       = models.CharField(max_length=200, blank=True)
    examiner_2_affiliation = models.CharField(max_length=200, blank=True)
    examiner_3_name        = models.CharField(max_length=200, blank=True)
    examiner_3_email       = models.CharField(max_length=200, blank=True)
    examiner_3_affiliation = models.CharField(max_length=200, blank=True)

    defense_status    = models.CharField(max_length=20, choices=DEFENSE_STATUS, default='pending')
    started_at        = models.DateTimeField(null=True, blank=True)
    ended_at          = models.DateTimeField(null=True, blank=True)
    start_link_token  = models.CharField(max_length=64, blank=True, unique=True, null=True)
    # tracks which Django session started this defense (for end-defense auth)
    started_by_session = models.CharField(max_length=64, blank=True)

    def full_name(self):
        return f"{self.given_names} {self.surname}"

    def get_panel_members(self):
        members = []
        multi_sup = bool(self.supervisor_2_name)
        if self.supervisor_1_name:
            members.append({
                'role': 'supervisor',
                'label': 'Supervisor 1' if multi_sup else 'Supervisor',
                'name': self.supervisor_1_name,
                'email': self.supervisor_1_email,
            })
        if self.supervisor_2_name:
            members.append({
                'role': 'supervisor',
                'label': 'Supervisor 2',
                'name': self.supervisor_2_name,
                'email': self.supervisor_2_email,
            })
        if self.jury_president_name:
            members.append({
                'role': 'president',
                'label': 'President Jury',
                'name': self.jury_president_name,
                'email': self.jury_president_email,
            })
        multi_ex = bool(self.examiner_2_name)
        if self.examiner_1_name:
            members.append({
                'role': 'examiner',
                'label': 'Examiner 1' if multi_ex else 'Examiner',
                'name': self.examiner_1_name,
                'email': self.examiner_1_email,
            })
        if self.examiner_2_name:
            members.append({
                'role': 'examiner',
                'label': 'Examiner 2',
                'name': self.examiner_2_name,
                'email': self.examiner_2_email,
            })
        if self.examiner_3_name:
            members.append({
                'role': 'examiner',
                'label': 'Examiner 3',
                'name': self.examiner_3_name,
                'email': self.examiner_3_email,
            })
        return members

    def __str__(self):
        return f"{self.full_name()} - {self.thesis_title[:50]}"

    class Meta:
        ordering = ['time']


class Evaluation(models.Model):
    ROLE_CHOICES = [
        ('supervisor', 'Supervisor'),
        ('examiner', 'Examiner'),
        ('president', 'Jury President'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='evaluations')
    evaluator_email       = models.EmailField()
    evaluator_name        = models.CharField(max_length=200)
    student_full_name     = models.CharField(max_length=200)
    thesis_title_confirmed = models.TextField()
    role                  = models.CharField(max_length=20, choices=ROLE_CHOICES)
    research_paper        = models.BooleanField(default=False)

    # ── Supervisor rubric (/50): 5 questions x /10 ──────────────────────────
    score_clarity      = models.IntegerField(default=0)  # Clarity of problem & significance
    score_literature   = models.IntegerField(default=0)  # Literature knowledge
    score_knowledge    = models.IntegerField(default=0)  # Subject knowledge & methodology
    score_critical     = models.IntegerField(default=0)  # Critical analysis & contribution
    score_presentation = models.IntegerField(default=0)  # Presentation quality

    # ── Examiner / Jury President rubric (/100) ─────────────────────────────
    score_intro        = models.IntegerField(default=0)  # 1-5  Introduction of topic
    score_transition   = models.IntegerField(default=0)  # 1-10 Smooth transition between sections
    score_quality      = models.IntegerField(default=0)  # 1-10 Quality of content
    score_analysis     = models.IntegerField(default=0)  # 1-5  Student analysis
    score_correctness  = models.IntegerField(default=0)  # 1-5  Clarity and correctness of content
    score_summary      = models.IntegerField(default=0)  # 1-5  Summary and conclusions
    # Presentation block a-e, each scored 2/4/6/8/10 (=/10), total /50
    score_delivery     = models.IntegerField(default=0)  # a. Professional and confident delivery
    score_engagement   = models.IntegerField(default=0)  # b. Engaged with audience
    score_structure    = models.IntegerField(default=0)  # c. Overall structure and organization
    score_timing       = models.IntegerField(default=0)  # d. Length of talk
    score_qa           = models.IntegerField(default=0)  # e. Response to questions from audience
    score_overall      = models.IntegerField(default=0)  # 1-10 Overall Impression/Quality

    additional_info     = models.TextField(blank=True)
    annotated_document  = models.FileField(upload_to='pv_uploads/', blank=True, null=True)
    submitted_at        = models.DateTimeField(auto_now_add=True)
    # Browser session that submitted this evaluation - used to restrict edits
    submitted_by_session = models.CharField(max_length=64, blank=True)
    # Secret per-response edit link token (Google Forms "Edit response" model):
    # lets the evaluator resume/edit their own response from any device.
    edit_token = models.CharField(max_length=64, blank=True, default='')

    def total_score_raw(self):
        """Total score - meaning depends on role: /50 for supervisor, /100 for examiner/president."""
        if self.role == 'supervisor':
            return (self.score_clarity + self.score_literature + self.score_knowledge
                    + self.score_critical + self.score_presentation)
        else:
            return (self.score_intro + self.score_transition + self.score_quality
                    + self.score_analysis + self.score_correctness + self.score_summary
                    + self.presentation_block_raw() + self.score_overall)

    def total_score_max(self):
        return 50 if self.role == 'supervisor' else 100

    def presentation_block_raw(self):
        """Sum of the a-e presentation criteria (each 2,4,6,8,10) -> max 50."""
        return (self.score_delivery + self.score_engagement + self.score_structure
                + self.score_timing + self.score_qa)

    def total_score_percent(self):
        return (self.total_score_raw() / self.total_score_max()) * 100

    def grade_label(self):
        p = self.total_score_percent()
        if p >= 85:  return "Distinction"
        elif p >= 80: return "Very Good Pass"
        elif p >= 70: return "Good Pass"
        elif p >= 60: return "Pass"
        else:         return "Fail"

    def __str__(self):
        return f"{self.evaluator_name} → {self.student.full_name()}"
