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

# ─── InsightFace singleton — loaded ONCE at startup, not per request ──────────
import insightface as _insightface_module
import cv2  # needed in register_face and recognize_and_mark

_face_app = _insightface_module.app.FaceAnalysis(
    name='buffalo_sc',
    providers=['CPUExecutionProvider']
)
_face_app.prepare(ctx_id=0, det_size=(320, 320))
# ─────────────────────────────────────────────────────────────────────────────


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

    total_enrolled = Enrollment.objects.filter(course=lecture.course).count()

    return JsonResponse({
        "lecture_id": lecture_id,
        "course_name": lecture.course.course_name,
        "course_code": lecture.course.course_code,
        "classroom": lecture.classroom,
        "date": str(lecture.date),
        "start_time": str(lecture.start_time),
        "end_time": str(lecture.end_time),
        "total_enrolled": total_enrolled,
        "attendance": attendance
    })


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
    Body: { "student_id": 1, "image": "<base64 jpeg>", "label": "straight" }
    Multiple calls with different labels build up a richer encoding set.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        student_id = data.get("student_id")
        image_b64 = data.get("image")
        label = data.get("label", "")
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not student_id or not image_b64:
        return JsonResponse({"error": "student_id and image are required"}, status=400)

    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    try:
        import io
        from PIL import Image

        app = _face_app  # module-level singleton — no reload cost

        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image_np = np.array(image)
        # InsightFace expects BGR
        bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        faces = app.get(bgr)

        if len(faces) == 0:
            return JsonResponse({"error": "No face detected. Please try again."}, status=400)

        if len(faces) > 1:
            return JsonResponse({"error": "Multiple faces detected. Ensure only one face is visible."}, status=400)

        # 512-d float32 embedding
        embedding = faces[0].normed_embedding.astype(np.float32)
        encoding_bytes = embedding.tobytes()

        FaceEncoding.objects.create(
            student=student,
            encoding=encoding_bytes,
            label=label
        )

        total = FaceEncoding.objects.filter(student=student).count()

        return JsonResponse({
            "message": f"Photo {total} registered for {student.name} ({label})",
            "student": student.registration_number,
            "total_encodings": total
        })

    except ImportError as e:
        return JsonResponse({"error": f"ImportError: {str(e)}"}, status=500)
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
            "label": enc.label,
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
        jpg_bytes = request.body
        if not jpg_bytes:
            return JsonResponse({"error": "No image data received"}, status=400)

        nparr = np.frombuffer(jpg_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return JsonResponse({"recognized": False, "reason": "Failed to decode image — may be corrupted"})

        h, w = frame.shape[:2]
        print(f"[DEBUG] Image received: {len(jpg_bytes)} bytes, decoded size: {w}x{h}")

        app = _face_app  # module-level singleton — no reload cost

        faces = app.get(frame)
        print(f"[DEBUG] Faces found: {len(faces)}")

        if not faces:
            return JsonResponse({"recognized": False, "reason": "No face detected"})

        stored = FaceEncoding.objects.select_related('student').all()
        if not stored.exists():
            return JsonResponse({"recognized": False, "reason": "No faces registered"})

        # Load known encodings — InsightFace uses 512-d float32, cosine similarity
        known_encodings = []
        known_students = []
        for enc in stored:
            arr = np.frombuffer(bytes(enc.encoding), dtype=np.float32)
            known_encodings.append(arr)
            known_students.append(enc.student)

        for face in faces:
            query_enc = face.normed_embedding.astype(np.float32)

            # Cosine similarity: higher = more similar (opposite of dlib distance)
            similarities = [float(np.dot(query_enc, k)) for k in known_encodings]
            best_idx = int(np.argmax(similarities))
            best_sim = similarities[best_idx]

            # Log all similarities per unique student (best score per student)
            seen = {}
            for s, sim in zip(known_students, similarities):
                if s.registration_number not in seen or sim > seen[s.registration_number][1]:
                    seen[s.registration_number] = (s.name, sim)
            for reg, (name, sim) in sorted(seen.items(), key=lambda x: -x[1][1]):
                print(f"[DEBUG] {name} ({reg}): {sim:.4f}")

            # ArcFace threshold: >0.35 is a strong match, <0.20 is clearly unknown
            THRESHOLD = 0.35
            if best_sim > THRESHOLD:
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
                    "confidence": round(best_sim * 100, 1)
                })

        return JsonResponse({"recognized": False, "reason": "No match found"})

    except ImportError as e:
        return JsonResponse({"error": f"Missing dependency: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
