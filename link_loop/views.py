from django.shortcuts import redirect

def api_route_view(requset):
    return redirect('api-root')