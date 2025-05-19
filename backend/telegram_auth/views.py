from django.http import JsonResponse

def auth_view(request):
    print("Auth endpoint hit!")  # This will show up in your Docker logs
    return JsonResponse({
        "id": 42,
        "username": "chill_user",
        "status": "stoned and authorized"
    })
