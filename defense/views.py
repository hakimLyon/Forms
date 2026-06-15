from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
import secrets, io, json

from .models import SitePassword, Session, Student, Evaluation
from .utils import (
    import_excel_students, generate_pv_docx, generate_pv_pdf, calc_scores,
    SUPERVISOR_QUESTIONS, EXAMINER_QUESTIONS, PRESENTATION_BLOCK,
    OVERALL_QUESTION, EVALUATION_ROLES, generate_detail_pdf,
    get_evaluation_detail_rows,
)


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def get_site_password():
    obj, _ = SitePassword.objects.get_or_create(id=1, defaults={'password': 'aimssn'})
    return obj.password


def require_auth(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('authenticated'):
            return redirect('password_gate')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ─── Public pages ─────────────────────────────────────────────────────────────

def landing(request):
    """First page: animated logo page with Enter Platform button."""
    return render(request, 'defense/landing.html')


def password_gate(request):
    """Password entry page (separate from the logo landing page)."""
    if request.method == 'POST':
        entered = request.POST.get('password', '')
        if entered == get_site_password():
            request.session['authenticated'] = True
            return redirect('sessions_list')
        return render(request, 'defense/password.html',
                      {'error': 'Incorrect password. Please try again.'})
    return render(request, 'defense/password.html')


# ─── Authenticated: session/room management ───────────────────────────────────

@require_auth
def sessions_list(request):
    sessions = Session.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'defense/sessions_list.html', {'sessions': sessions})


@require_auth
def session_rooms(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    r1 = session.students.filter(room=1)
    r2 = session.students.filter(room=2)
    return render(request, 'defense/session_rooms.html', {
        'session': session,
        'room1_count':   r1.count(),
        'room1_pending': r1.filter(defense_status='pending').count(),
        'room1_ongoing': r1.filter(defense_status='ongoing').count(),
        'room1_done':    r1.filter(defense_status='done').count(),
        'room2_count':   r2.count(),
        'room2_pending': r2.filter(defense_status='pending').count(),
        'room2_ongoing': r2.filter(defense_status='ongoing').count(),
        'room2_done':    r2.filter(defense_status='done').count(),
    })


@require_auth
def room_students(request, session_id, room_number):
    session = get_object_or_404(Session, pk=session_id)
    students = Student.objects.filter(session=session, room=room_number).order_by('time')

    return render(request, 'defense/room_students.html', {
        'session': session,
        'room_number': room_number,
        'students': students,
    })


@require_auth
def start_defense(request, student_id):
    """Start a defense: generate per-student token, record who started it."""
    student = get_object_or_404(Student, pk=student_id)
    if student.defense_status == 'pending':
        student.defense_status = 'ongoing'
        student.started_at = timezone.now()
        student.start_link_token = secrets.token_urlsafe(32)
        # Record the session user key so only they can end it
        student.started_by_session = request.session.session_key
        student.save()
    return redirect('room_students',
                    session_id=student.session_id,
                    room_number=student.room)


@require_auth
def end_defense(request, student_id):
    """End a defense - only the person who started it (or admin) can do this."""
    student = get_object_or_404(Student, pk=student_id)
    # Allow if: same session started it, OR Django admin (staff)
    can_end = (
        request.session.session_key == student.started_by_session
        or request.user.is_staff
    )
    if not can_end:
        messages.error(request, "Only the person who started this defense can end it.")
        return redirect('room_students',
                        session_id=student.session_id,
                        room_number=student.room)
    if student.defense_status == 'ongoing':
        student.defense_status = 'done'
        student.ended_at = timezone.now()
        student.save()
    return redirect('room_students',
                    session_id=student.session_id,
                    room_number=student.room)


@require_auth
def import_excel(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    if request.method == 'POST' and request.FILES.get('excel_file'):
        f = request.FILES['excel_file']
        session.excel_file = f
        session.save()
        count = import_excel_students(session, f)
        messages.success(request, f"Imported {count} students successfully.")
    return redirect('session_rooms', session_id=session_id)


# ─── Room public link ─────────────────────────────────────────────────────────

# ─── Room public link (fixed URL, no token) ──────────────────────────────────

def room_public(request, session_id, room_number):
    """
    Public room page, fixed predictable URL e.g. /sessions/1/room/1/public/
    Accessible to anyone with the link - no token required.
    Shows all ONGOING defenses in this room as clickable cards
    (thesis title + Enter button leading to the panel/evaluation forms).
    """
    session = get_object_or_404(Session, pk=session_id)
    students = Student.objects.filter(
        session=session, room=room_number,
        defense_status='ongoing'
    ).order_by('time')

    return render(request, 'defense/room_public.html', {
        'session': session,
        'room_number': room_number,
        'students': students,
    })


def room_public_legacy(request, session_id, room_number, room_token):
    """Old token-based room link - redirect to the new fixed URL."""
    return redirect('room_public', session_id=session_id, room_number=room_number)


# ─── Per-student defense flow (public, token-gated) ──────────────────────────

def defense_entry(request, token):
    """Entry page for a single student defense - shown to evaluators."""
    student = get_object_or_404(Student, start_link_token=token)
    if student.defense_status != 'ongoing':
        return render(request, 'defense/defense_closed.html', {'student': student})
    return render(request, 'defense/defense_entry.html',
                  {'student': student, 'token': token})


def panel_members(request, token):
    """Grid of panel members. The starter also sees 'End Defense' here."""
    student = get_object_or_404(Student, start_link_token=token)
    if student.defense_status != 'ongoing':
        return render(request, 'defense/defense_closed.html', {'student': student})
    members = student.get_panel_members()
    submitted_names = list(
        Evaluation.objects.filter(student=student)
                          .values_list('evaluator_name', flat=True)
    )
    # Is this the person who started? They can end it.
    can_end = (
        request.session.session_key == student.started_by_session
        or request.user.is_staff
    )
    return render(request, 'defense/panel_members.html', {
        'student': student,
        'members': members,
        'token': token,
        'submitted_names': submitted_names,
        'can_end': can_end,
    })


def end_defense_from_panel(request, token):
    """End a defense from the panel page (starter's button)."""
    student = get_object_or_404(Student, start_link_token=token)
    can_end = (
        request.session.session_key == student.started_by_session
        or request.user.is_staff
    )
    if not can_end:
        return render(request, 'defense/defense_closed.html', {'student': student})
    if student.defense_status == 'ongoing':
        student.defense_status = 'done'
        student.ended_at = timezone.now()
        student.save()
    # Redirect to room student table (authenticated area)
    return redirect('room_students',
                    session_id=student.session_id,
                    room_number=student.room)


def evaluation_form(request, token, member_index):
    student = get_object_or_404(Student, start_link_token=token)
    if student.defense_status != 'ongoing':
        return render(request, 'defense/defense_closed.html', {'student': student})

    members = student.get_panel_members()
    if member_index >= len(members):
        return redirect('panel_members', token=token)
    member = members[member_index]

    existing = Evaluation.objects.filter(
        student=student, evaluator_name=member['name']
    ).first()

    # Lock editing to the original submitter's browser session (admin/staff bypass)
    if existing and existing.submitted_by_session:
        is_owner = request.session.session_key == existing.submitted_by_session
        is_admin = request.user.is_staff
        if not is_owner and not is_admin:
            return render(request, 'defense/evaluation_locked.html', {
                'student': student,
                'member': member,
                'token': token,
                'existing': existing,
            })

    # Rubric definitions are imported from utils (shared with detail/PDF views)

    if request.method == 'POST':
        if not request.session.session_key:
            request.session.save()
        eval_obj = existing or Evaluation(student=student)
        eval_obj.evaluator_email = request.POST.get('email', '')
        eval_obj.evaluator_name  = request.POST.get('evaluator_name', member['name'])
        eval_obj.student_full_name = request.POST.get('student_full_name', student.full_name())
        eval_obj.thesis_title_confirmed = request.POST.get('thesis_title', student.thesis_title)
        eval_obj.role = member['role']
        eval_obj.research_paper = request.POST.get('research_paper') == 'yes'

        if member['role'] == 'supervisor':
            eval_obj.score_clarity      = int(request.POST.get('score_clarity', 0))
            eval_obj.score_literature   = int(request.POST.get('score_literature', 0))
            eval_obj.score_knowledge    = int(request.POST.get('score_knowledge', 0))
            eval_obj.score_critical     = int(request.POST.get('score_critical', 0))
            eval_obj.score_presentation = int(request.POST.get('score_presentation', 0))
        else:
            eval_obj.score_intro       = int(request.POST.get('score_intro', 0))
            eval_obj.score_transition  = int(request.POST.get('score_transition', 0))
            eval_obj.score_quality     = int(request.POST.get('score_quality', 0))
            eval_obj.score_analysis    = int(request.POST.get('score_analysis', 0))
            eval_obj.score_correctness = int(request.POST.get('score_correctness', 0))
            eval_obj.score_summary     = int(request.POST.get('score_summary', 0))
            eval_obj.score_delivery    = int(request.POST.get('score_delivery', 0))
            eval_obj.score_engagement  = int(request.POST.get('score_engagement', 0))
            eval_obj.score_structure   = int(request.POST.get('score_structure', 0))
            eval_obj.score_timing      = int(request.POST.get('score_timing', 0))
            eval_obj.score_qa          = int(request.POST.get('score_qa', 0))
            eval_obj.score_overall     = int(request.POST.get('score_overall', 0))

        eval_obj.additional_info = request.POST.get('additional_info', '')
        eval_obj.submitted_by_session = request.session.session_key
        if 'annotated_document' in request.FILES:
            eval_obj.annotated_document = request.FILES['annotated_document']
        eval_obj.save()
        return redirect('evaluation_result', token=token, eval_id=eval_obj.id)

    context = {
        'student': student,
        'member': member,
        'member_index': member_index,
        'token': token,
        'existing': existing,
        'scores': range(1, 11),
        'evaluation_roles': EVALUATION_ROLES,
    }

    if member['role'] == 'supervisor':
        context['score_questions'] = SUPERVISOR_QUESTIONS
        context['form_max'] = 50
    else:
        context['examiner_questions'] = EXAMINER_QUESTIONS
        context['presentation_block'] = PRESENTATION_BLOCK
        context['presentation_scores'] = [2, 4, 6, 8, 10]
        context['overall_question'] = OVERALL_QUESTION
        context['form_max'] = 100

    return render(request, 'defense/evaluation_form.html', context)


def evaluation_result(request, token, eval_id):
    evaluation = get_object_or_404(Evaluation, pk=eval_id)
    student = get_object_or_404(Student, start_link_token=token)
    members = student.get_panel_members()
    member_index = 0
    for i, m in enumerate(members):
        if m['name'] == evaluation.evaluator_name:
            member_index = i
            break

    all_evaluations = Evaluation.objects.filter(student=student).order_by('role', 'evaluator_name')

    # Build a lookup so the template can show an "Edit" link for any row,
    # mapping each evaluation back to its panel member index.
    name_to_index = {m['name']: i for i, m in enumerate(members)}
    eval_rows = []
    for ev in all_evaluations:
        eval_rows.append({
            'evaluation': ev,
            'member_index': name_to_index.get(ev.evaluator_name),
            'is_current': ev.id == evaluation.id,
        })

    final_grade_info = None
    if all_evaluations.exists():
        scores = calc_scores(student, list(all_evaluations))
        final_grade_info = {
            'final_score': scores['final_score'],
            'final_label': scores['final_grade'],
        }

    return render(request, 'defense/evaluation_result.html', {
        'evaluation': evaluation,
        'student': student,
        'token': token,
        'member_index': member_index,
        'eval_rows': eval_rows,
        'final_grade_info': final_grade_info,
    })


# ─── PV / Download ────────────────────────────────────────────────────────────

@require_auth
def pv_overview(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    evaluations = Evaluation.objects.filter(student=student)
    supervisor_evals = evaluations.filter(role='supervisor')
    examiner_evals   = evaluations.filter(role__in=['examiner', 'president'])
    sup_scores  = [e.total_score_percent() for e in supervisor_evals]
    exam_scores = [e.total_score_percent() for e in examiner_evals]
    sup_avg  = sum(sup_scores)  / len(sup_scores)  if sup_scores  else 0
    exam_avg = sum(exam_scores) / len(exam_scores) if exam_scores else 0
    final    = 0.4 * sup_avg + 0.6 * exam_avg if (sup_scores or exam_scores) else 0

    def grade_label(pct):
        if pct >= 85: return "Distinction"
        elif pct >= 80: return "Very Good Pass"
        elif pct >= 70: return "Good Pass"
        elif pct >= 60: return "Pass"
        else: return "Fail"

    return render(request, 'defense/pv_overview.html', {
        'student': student,
        'evaluations': evaluations,
        'supervisor_evals': supervisor_evals,
        'examiner_evals': examiner_evals,
        'sup_avg': round(sup_avg, 1),
        'exam_avg': round(exam_avg, 1),
        'final_score': round(final, 1),
        'final_grade': grade_label(final),
    })


@require_auth
def download_pv(request, student_id, fmt):
    student = get_object_or_404(Student, pk=student_id)
    evaluations = list(Evaluation.objects.filter(student=student))
    if fmt == 'docx':
        buf = generate_pv_docx(student, evaluations)
        response = HttpResponse(
            buf,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = \
            f'attachment; filename="PV_{student.surname}_{student.given_names}.docx"'
        return response
    elif fmt == 'pdf':
        buf = generate_pv_pdf(student, evaluations)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = \
            f'attachment; filename="PV_{student.surname}_{student.given_names}.pdf"'
        return response
    return HttpResponse("Invalid format", status=400)


@require_auth
def download_all_pv(request, session_id, fmt):
    import zipfile
    session = get_object_or_404(Session, pk=session_id)
    students = Student.objects.filter(session=session)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        used_names = set()
        for student in students:
            evals = list(Evaluation.objects.filter(student=student))
            base = f"PV_{student.surname}_{student.given_names}".replace(' ', '_')
            ext = 'docx' if fmt == 'docx' else 'pdf'
            fname = f"{base}.{ext}"
            # Avoid duplicate filenames (e.g. two students with same name)
            counter = 2
            while fname in used_names:
                fname = f"{base}_{student.id}.{ext}"
                if fname in used_names:
                    fname = f"{base}_{counter}.{ext}"
                    counter += 1
            used_names.add(fname)

            if fmt == 'docx':
                file_content = generate_pv_docx(student, evals)
            else:
                file_content = generate_pv_pdf(student, evals)
            zf.writestr(fname, file_content.read())
    buf.seek(0)
    response = HttpResponse(buf, content_type='application/zip')
    response['Content-Disposition'] = \
        f'attachment; filename="PV_All_{session.name}.zip"'
    return response


# ─── Student detail (all responses, post-defense) ─────────────────────────────

@require_auth
def student_detail(request, student_id):
    """
    Shows every question and answer submitted by each evaluator
    (Supervisor(s), Examiner(s), Jury President) for this student.
    Accessible once the defense session has been marked done (or any time
    by admin), via a "Detail" button on the room table.
    """
    student = get_object_or_404(Student, pk=student_id)
    evaluations = Evaluation.objects.filter(student=student).order_by('role', 'evaluator_name')

    eval_blocks = []
    for ev in evaluations:
        eval_blocks.append({
            'evaluation': ev,
            'rows': get_evaluation_detail_rows(ev),
        })

    final_grade_info = None
    if evaluations.exists():
        scores = calc_scores(student, list(evaluations))
        final_grade_info = {
            'final_score': scores['final_score'],
            'final_label': scores['final_grade'],
        }

    return render(request, 'defense/student_detail.html', {
        'student': student,
        'eval_blocks': eval_blocks,
        'final_grade_info': final_grade_info,
    })


@require_auth
def download_detail_pdf(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    evaluations = list(Evaluation.objects.filter(student=student).order_by('role', 'evaluator_name'))
    buf = generate_detail_pdf(student, evaluations)
    response = HttpResponse(buf, content_type='application/pdf')
    response['Content-Disposition'] = \
        f'attachment; filename="Detail_{student.surname}_{student.given_names}.pdf"'
    return response
