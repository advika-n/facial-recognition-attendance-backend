from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import json
import base64

from lectures.models import Lecture, Course
from students.models import Student
from enrollments.models import Enrollment
from attendance.models import Attendance
from faces.models import FaceEncoding
from lecture_attendance_view import lecture_attendance



def current_lecture(request):
    classroom = request.GET.get('classroom')

    if not classroom:
        return JsonResponse({"error": "classroom parameter is required"}, status=400)

    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    lecture = Lecture.objects.filter(
        classroom=classroom,
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).first()

    if not lecture:
        return JsonResponse({"message": "No lecture currently running"}, status=404)

    return JsonResponse({
        "lecture_id": lecture.id,
        "course_code": lecture.course.course_code,
        "course_name": lecture.course.course_name,
        "classroom": lecture.classroom,
        "start_time": str(lecture.start_time),
        "end_time": str(lecture.end_time)
    })


@csrf_exempt
def start_lecture(request):
    """
    Called by the professor dashboard when they click Start Attendance.
    Creates a Lecture record for today so mark_attendance can find it.
    Body: { "class_id": "CH202526010001", "classroom": "301", "duration_minutes": 60 }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        class_id = data.get("class_id")
        classroom = data.get("classroom")
        duration_minutes = int(data.get("duration_minutes", 60))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not class_id or not classroom:
        return JsonResponse({"error": "class_id and classroom are required"}, status=400)

    # Find the course by class_id
    try:
        course = Course.objects.get(class_id=class_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": f"Course with class_id '{class_id}' not found"}, status=404)

    now = timezone.localtime()
    today = now.date()
    start_time = now.time()

    # Calculate end time
    from datetime import datetime, timedelta
    start_dt = datetime.combine(today, start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    end_time = end_dt.time()

    # Check if a lecture already exists for this course + classroom + today
    lecture, created = Lecture.objects.get_or_create(
        course=course,
        classroom=classroom,
        date=today,
        defaults={
            "start_time": start_time,
            "end_time": end_time
        }
    )

    return JsonResponse({
        "lecture_id": lecture.id,
        "course_code": course.course_code,
        "course_name": course.course_name,
        "classroom": classroom,
        "date": str(today),
        "start_time": str(lecture.start_time),
        "end_time": str(lecture.end_time),
        "created": created
    }, status=201 if created else 200)


@csrf_exempt
def mark_attendance(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        data = json.loads(request.body)
        classroom = data.get("classroom")
        registration_number = data.get("registration_number")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not classroom or not registration_number:
        return JsonResponse({"error": "classroom and registration_number are required"}, status=400)

    # Find current lecture for this classroom
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    lecture = Lecture.objects.filter(
        classroom=classroom,
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).first()

    if not lecture:
        return JsonResponse({"error": "No lecture currently running in this classroom"}, status=404)

    # Find student by registration number
    try:
        student = Student.objects.get(registration_number=registration_number)
    except Student.DoesNotExist:
        return JsonResponse({"error": f"Student {registration_number} not found"}, status=404)

    # Check enrollment
    if not Enrollment.objects.filter(student=student, course=lecture.course).exists():
        return JsonResponse({"error": "Student not enrolled in this course"}, status=403)

    # Prevent duplicate attendance
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        lecture=lecture
    )

    if not created:
        return JsonResponse({"message": "Attendance already marked"}, status=200)

    return JsonResponse({"message": "Attendance marked successfully"}, status=201)


def student_attendance_percentage(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    result = {}
    enrollments = Enrollment.objects.filter(student=student)

    for enrollment in enrollments:
        course = enrollment.course
        total_lectures = Lecture.objects.filter(course=course).count()
        attended_lectures = Attendance.objects.filter(
            student=student,
            lecture__course=course
        ).count()

        percentage = round((attended_lectures / total_lectures) * 100, 2) if total_lectures > 0 else 0.0

        result[course.course_code] = {
            "course_name": course.course_name,
            "attended": attended_lectures,
            "total": total_lectures,
            "percentage": percentage
        }

    return JsonResponse({
        "student": student.registration_number,
        "attendance": result
    })


@csrf_exempt
def register_face(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        encoding_b64 = data.get("encoding")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not student_id or not encoding_b64:
        return JsonResponse({"error": "Missing fields"}, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    encoding_bytes = base64.b64decode(encoding_b64)
    FaceEncoding.objects.update_or_create(
        student=student,
        defaults={"encoding": encoding_bytes}
    )

    return JsonResponse({"message": "Face encoding stored successfully"})

def lecture_attendance(request, lecture_id):
    """
    Returns list of students marked present for a specific lecture.
    Called by the professor dashboard every 5 seconds during an active session.
    GET /api/lecture/<lecture_id>/attendance/
    """
    try:
        lecture = Lecture.objects.get(pk=lecture_id)
    except Lecture.DoesNotExist:
        return JsonResponse({"error": "Lecture not found"}, status=404)

    records = Attendance.objects.filter(lecture=lecture).select_related('student')

    attendance = []
    for record in records:
        attendance.append({
            "name": record.student.name,
            "registration_number": record.student.registration_number,
            "department": record.student.department if hasattr(record.student, 'department') else "",
            "time_marked": record.created_at.isoformat() if hasattr(record, 'created_at') else None
        })

    return JsonResponse({"lecture_id": lecture_id, "attendance": attendance})
