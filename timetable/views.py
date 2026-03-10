from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import TimetableEntry


@csrf_exempt
def timetable_list(request):
    if request.method == 'GET':
        entries = list(TimetableEntry.objects.values())
        return JsonResponse(entries, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        entry = TimetableEntry.objects.create(
            class_id=data['class_id'],
            course_name=data['course_name'],
            slot_type=data['slot_type'],
            day=data['day'],
            slot=data['slot'],
            classroom=data['classroom'],
            professor_id=data.get('professor_id', '')
        )
        return JsonResponse({'id': entry.id, 'class_id': entry.class_id}, status=201)


@csrf_exempt
def timetable_detail(request, pk):
    try:
        entry = TimetableEntry.objects.get(pk=pk)
    except TimetableEntry.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        entry.delete()
        return JsonResponse({'message': 'Deleted'})

    return JsonResponse({
        'id': entry.id,
        'class_id': entry.class_id,
        'day': entry.day,
        'slot': entry.slot,
        'professor_id': entry.professor_id
    })
