from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def auth_view(request):
    return JsonResponse({'message': 'Auth endpoint hit'})
