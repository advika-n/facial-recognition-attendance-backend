from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import base64
import numpy as np
from datetime import datetime, timedelta

from lectures.models import Lecture, Course
from students.models import Student
from enrollments.models import Enrollment
from attendance.models import Attendance
from faces.models import FaceEncoding


# ─── Current Lecture ──────────────────────────────────────────────────────────

def current_lecture(request):
    classroom = request.GET.get('classroom')
    if not classroom:
        return JsonResponse({"error": "classroom parameter is required"}, status=400)

    now = timezone.localtime()
    lecture = Lecture.objects.filter(
        classroom=classroom,
        date=now.date(),
        start_time__lte=now.time(),
        end_time__gte=now.time()
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


# ─── Start Lecture ────────────────────────────────────────────────────────────

@csrf_exempt
def start_lecture(request):
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

    try:
        course = Course.objects.get(class_id=class_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": f"Course with class_id '{class_id}' not found"}, status=404)

    now = timezone.localtime()
    today = now.date()
    start_time = now.time()
    end_dt = datetime.combine(today, start_time) + timedelta(minutes=duration_minutes)
    end_time = end_dt.time()

    lecture, created = Lecture.objects.get_or_create(
        course=course,
        classroom=classroom,
        date=today,
        defaults={"start_time": start_time, "end_time": end_time}
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


# ─── Mark Attendance ──────────────────────────────────────────────────────────

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

    now = timezone.localtime()
    lecture = Lecture.objects.filter(
        classroom=classroom,
        date=now.date(),
        start_time__lte=now.time(),
        end_time__gte=now.time()
    ).first()

    if not lecture:
        return JsonResponse({"error": "No lecture currently running in this classroom"}, status=404)

    try:
        student = Student.objects.get(registration_number=registration_number)
    except Student.DoesNotExist:
        return JsonResponse({"error": f"Student {registration_number} not found"}, status=404)

    if not Enrollment.objects.filter(student=student, course=lecture.course).exists():
        return JsonResponse({"error": "Student not enrolled in this course"}, status=403)

    attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)

    if not created:
        return JsonResponse({"message": "Attendance already marked"}, status=200)

    return JsonResponse({"message": "Attendance marked successfully"}, status=201)


# ─── Lecture Attendance (live view for professor) ─────────────────────────────

def lecture_attendance(request, lecture_id):
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
            "department": record.student.department,
            "time_marked": record.timestamp.isoformat() if record.timestamp else None
        })

    return JsonResponse({"lecture_id": lecture_id, "attendance": attendance})


# ─── Student Attendance Percentage ───────────────────────────────────────────

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
            student=student, lecture__course=course
        ).count()

        percentage = round((attended_lectures / total_lectures) * 100, 2) if total_lectures > 0 else 0.0

        result[course.course_code] = {
            "course_name": course.course_name,
            "attended": attended_lectures,
            "total": total_lectures,
            "percentage": percentage
        }

    return JsonResponse({"student": student.registration_number, "attendance": result})


# ─── Register Face ────────────────────────────────────────────────────────────

@csrf_exempt
def register_face(request):
    """
    Accepts a base64 JPEG image, extracts face encoding, stores in DB.
    Body: { "student_id": 1, "image": "<base64 jpeg>" }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        image_b64 = data.get("image")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not student_id or not image_b64:
        return JsonResponse({"error": "student_id and image are required"}, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    try:
        import face_recognition
        from PIL import Image
        import io

        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_np = np.array(image)

        encodings = face_recognition.face_encodings(image_np)

        if len(encodings) == 0:
            return JsonResponse({"error": "No face detected. Please try again."}, status=400)

        if len(encodings) > 1:
            return JsonResponse({"error": "Multiple faces detected. Ensure only one face is visible."}, status=400)

        encoding_bytes = encodings[0].tobytes()

        FaceEncoding.objects.update_or_create(
            student=student,
            defaults={"encoding": encoding_bytes}
        )

        return JsonResponse({
            "message": f"Face registered successfully for {student.name}",
            "student": student.registration_number
        })

    except ImportError as e:
        return JsonResponse({"error": f"Import failed: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Failed to process image: {str(e)}"}, status=500)


# ─── Get All Encodings ────────────────────────────────────────────────────────

def get_encodings(request):
    """
    Returns all stored face encodings as base64.
    Called by recognize.py at startup.
    GET /api/get-encodings/
    """
    stored = FaceEncoding.objects.select_related('student').all()

    result = []
    for enc in stored:
        result.append({
            "student_id": enc.student.id,
            "name": enc.student.name,
            "registration_number": enc.student.registration_number,
            "department": enc.student.department,
            "encoding": base64.b64encode(bytes(enc.encoding)).decode('utf-8')
        })

    return JsonResponse({"encodings": result, "count": len(result)})


# ─── Recognize and Mark (for ESP32-CAM) ──────────────────────────────────────

@csrf_exempt
def recognize_and_mark(request):
    """
    Called by ESP32-CAM with raw JPEG bytes.
    Runs face recognition, finds matching student, marks attendance.
    POST /api/recognize-and-mark/
    Headers: Content-Type: image/jpeg, X-Classroom: 301
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    classroom = request.headers.get('X-Classroom', '')
    if not classroom:
        return JsonResponse({"error": "X-Classroom header is required"}, status=400)

    try:
        import face_recognition
        import cv2

        jpg_bytes = request.body
        if not jpg_bytes:
            return JsonResponse({"error": "No image data received"}, status=400)

        nparr = np.frombuffer(jpg_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings_in_frame = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings_in_frame:
            return JsonResponse({"recognized": False, "reason": "No face detected"})

        stored = FaceEncoding.objects.select_related('student').all()
        if not stored.exists():
            return JsonResponse({"recognized": False, "reason": "No faces registered"})

        known_encodings = []
        known_students = []
        for enc in stored:
            arr = np.frombuffer(bytes(enc.encoding), dtype=np.float64)
            known_encodings.append(arr)
            known_students.append(enc.student)

        for face_enc in face_encodings_in_frame:
            distances = face_recognition.face_distance(known_encodings, face_enc)
            best_idx = int(np.argmin(distances))
            best_distance = distances[best_idx]

            if best_distance < 0.6:
                student = known_students[best_idx]

                now = timezone.localtime()
                lecture = Lecture.objects.filter(
                    classroom=classroom,
                    date=now.date(),
                    start_time__lte=now.time(),
                    end_time__gte=now.time()
                ).first()

                if not lecture:
                    return JsonResponse({
                        "recognized": True,
                        "name": student.name,
                        "registration_number": student.registration_number,
                        "marked": False,
                        "reason": "No active lecture in this classroom"
                    })

                if not Enrollment.objects.filter(student=student, course=lecture.course).exists():
                    return JsonResponse({
                        "recognized": True,
                        "name": student.name,
                        "registration_number": student.registration_number,
                        "marked": False,
                        "reason": "Student not enrolled in this course"
                    })

                _, created = Attendance.objects.get_or_create(student=student, lecture=lecture)

                return JsonResponse({
                    "recognized": True,
                    "name": student.name,
                    "registration_number": student.registration_number,
                    "department": student.department,
                    "marked": created,
                    "already_marked": not created,
                    "confidence": round((1 - best_distance) * 100, 1)
                })

        return JsonResponse({"recognized": False, "reason": "No match found"})

    except ImportError:
        return JsonResponse({"error": "face_recognition or cv2 not installed"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
