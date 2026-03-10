from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from students.models import Student
from professors.models import Professor


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = data.get("user_id", "").strip()
        password = data.get("password", "").strip()
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not user_id or not password:
        return JsonResponse({"error": "user_id and password are required"}, status=400)

    # Check if student (password = registration number)
    try:
        student = Student.objects.get(registration_number=user_id)
        if password == user_id:
            return JsonResponse({
                "role": "student",
                "id": student.id,
                "name": student.name,
                "registration_number": student.registration_number,
            })
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
    except Student.DoesNotExist:
        pass

    # Check if professor (password = professor_id)
    try:
        professor = Professor.objects.get(professor_id=user_id)
        if password == user_id:
            return JsonResponse({
                "role": "professor",
                "id": professor.id,
                "name": professor.name,
                "professor_id": professor.professor_id,
                "department": professor.department,
            })
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
    except Professor.DoesNotExist:
        pass

    return JsonResponse({"error": "Invalid credentials"}, status=401)
