from custom_user.models import System

def system_settings(request):
    system = System.objects.first()  # Get the first system object (assuming there's only one)
    return {
        'system': system,
        
    }