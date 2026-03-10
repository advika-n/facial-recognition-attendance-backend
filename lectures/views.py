from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Course


@csrf_exempt
def course_list(request):
    if request.method == 'GET':
        courses = list(Course.objects.values('id', 'class_id', 'course_code', 'course_name', 'professor_id'))
        return JsonResponse(courses, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        course = Course.objects.create(
            class_id=data.get('class_id', ''),
            course_code=data['course_code'],
            course_name=data['course_name'],
            professor_id=data.get('professor_id', '')
        )
        return JsonResponse({
            'id': course.id,
            'class_id': course.class_id,
            'course_code': course.course_code,
            'course_name': course.course_name,
            'professor_id': course.professor_id
        }, status=201)


@csrf_exempt
def course_detail(request, pk):
    try:
        course = Course.objects.get(pk=pk)
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        course.delete()
        return JsonResponse({'message': 'Deleted'})

    return JsonResponse({
        'id': course.id,
        'class_id': course.class_id,
        'course_code': course.course_code,
        'course_name': course.course_name,
        'professor_id': course.professor_id
    })
