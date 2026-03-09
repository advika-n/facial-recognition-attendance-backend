from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Professor

@csrf_exempt
def professor_list(request):
    if request.method == 'GET':
        profs = list(Professor.objects.values('id', 'professor_id', 'name', 'department'))
        return JsonResponse(profs, safe=False)

    if request.method == 'POST':
        data = json.loads(request.body)
        prof = Professor.objects.create(
            professor_id=data['professor_id'],
            name=data['name'],
            department=data['department']
        )
        return JsonResponse({'id': prof.id, 'professor_id': prof.professor_id, 'name': prof.name}, status=201)

@csrf_exempt
def professor_detail(request, pk):
    try:
        prof = Professor.objects.get(pk=pk)
    except Professor.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'DELETE':
        prof.delete()
        return JsonResponse({'message': 'Deleted'})

    return JsonResponse({'id': prof.id, 'professor_id': prof.professor_id, 'name': prof.name, 'department': prof.department})