from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Bill
from datetime import datetime


def scraper_dashboard(request):
    """Admin dashboard for scraper monitoring"""
    from .auto_scraper import auto_scraper
    
    context = {
        'status': auto_scraper.get_status(),
        'total_bills': Bill.objects.count(),
        'today_bills': Bill.objects.filter(last_updated__date=datetime.now().date()).count(),
    }
    return render(request, 'tracker/admin/scraper_dashboard.html', context)


@csrf_exempt
def trigger_scrape_api(request):
    """API endpoint to manually trigger scraping"""
    from .auto_scraper import manual_scrape_all
    
    if request.method == 'POST':
        results = manual_scrape_all()
        return JsonResponse({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def scraper_status_api(request):
    """API endpoint to get scraper status"""
    from .auto_scraper import get_scraper_status
    
    status = get_scraper_status()
    status['total_bills'] = Bill.objects.count()
    status['bills_by_source'] = {
        'MPA': Bill.objects.filter(source='MPA').count(),
        'PRS': Bill.objects.filter(source__icontains='PRS').count(),
    }
    return JsonResponse(status)


def scraping_logs(request):
    """View scraping logs"""
    return render(request, 'tracker/admin/scraping_logs.html', {'logs': []})