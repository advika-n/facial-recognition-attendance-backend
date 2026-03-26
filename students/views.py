from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Student


@csrf_exempt
def student_list(request):
    if request.method == 'GET':
        students = list(Student.objects.values(
            'id', 'name', 'registration_number', 'department', 'is_active'
        ))
        return JsonResponse(students, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        student = Student.objects.create(
            name=data['name'],
            registration_number=data['registration_number'],
            department=data.get('department', '')
        )
        return JsonResponse({
            'id': student.id,
            'name': student.name,
            'registration_number': student.registration_number,
            'department': student.department
        }, status=201)


@csrf_exempt
def student_detail(request, pk):
    try:
        student = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        student.delete()
        return JsonResponse({'message': 'Deleted'})

    return JsonResponse({
        'id': student.id,
        'name': student.name,
        'registration_number': student.registration_number,
        'department': student.department
    })
