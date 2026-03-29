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
        try:
            data = json.loads(request.body)
            name = data.get('name')
            registration_number = data.get('registration_number')
            if not name or not registration_number:
                return JsonResponse({'error': 'name and registration_number are required'}, status=400)
            student = Student.objects.create(
                name=name,
                registration_number=registration_number,
                department=data.get('department', '')
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
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
