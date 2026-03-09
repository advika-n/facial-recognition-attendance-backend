from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Attendance
from students.models import Student
from lectures.models import Lecture


@csrf_exempt
def attendance_list(request):
    if request.method == 'GET':
        records = list(Attendance.objects.values(
            'id',
            'student__registration_number',
            'student__name',
            'lecture__course__course_name',
            'lecture__course__course_code',
            'lecture__date',
            'timestamp',
        ))
        return JsonResponse(records, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            student = Student.objects.get(registration_number=data['registration_number'])
            lecture = Lecture.objects.get(pk=data['lecture_id'])
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        except Lecture.DoesNotExist:
            return JsonResponse({'error': 'Lecture not found'}, status=404)

        record, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
        return JsonResponse({
            'id': record.id,
            'created': created,
            'student': student.registration_number,
            'lecture': lecture.id,
        }, status=201)
