from django.conf import settings
def visualization_settings(request):
    return {'VISUALIZATION_CONFIG': settings.VISUALIZATION_CONFIG}