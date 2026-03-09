from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Enrollment
from students.models import Student
from lectures.models import Course, Teacher

@csrf_exempt
def enrollment_list(request):
    if request.method == 'GET':
        enrollments = list(Enrollment.objects.values('id', 'student__registration_number', 'course__course_code', 'course__course_name'))
        return JsonResponse(enrollments, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            student = Student.objects.get(registration_number=data['registration_number'])
            course = Course.objects.get(course_code=data['course_code'])
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=404)
        enrollment, created = Enrollment.objects.get_or_create(student=student, course=course)
        return JsonResponse({'id': enrollment.id, 'created': created}, status=201)

@csrf_exempt
def enrollment_detail(request, pk):
    try:
        e = Enrollment.objects.get(pk=pk)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    if request.method == 'DELETE':
        e.delete()
        return JsonResponse({'message': 'Deleted'})
    return JsonResponse({'id': e.id})