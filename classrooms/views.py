from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Classroom

@csrf_exempt
def classroom_list(request):
    if request.method == 'GET':
        rooms = list(Classroom.objects.values('id', 'room_name', 'room_type', 'camera_id'))
        return JsonResponse(rooms, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        room = Classroom.objects.create(
            room_name=data['room_name'],
            room_type=data['room_type'],
            camera_id=data.get('camera_id', '')
        )
        return JsonResponse({'id': room.id, 'room_name': room.room_name, 'room_type': room.room_type}, status=201)

@csrf_exempt
def classroom_detail(request, pk):
    try:
        room = Classroom.objects.get(pk=pk)
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        room.delete()
        return JsonResponse({'message': 'Deleted'})

    return JsonResponse({'id': room.id, 'room_name': room.room_name, 'room_type': room.room_type, 'camera_id': room.camera_id})