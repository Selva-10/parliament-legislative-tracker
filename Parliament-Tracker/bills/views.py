# bills/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Bill, ScrapeSource
from .scraper import scrape_prs, scrape_loksabha, scrape_rajyasabha
import json
import logging
from celery import shared_task

logger = logging.getLogger(__name__)

def dashboard(request):
    """Dashboard view with key metrics"""
    context = {
        'total_bills': Bill.objects.count(),
        'pending_bills': Bill.objects.filter(status='PENDING').count(),
        'passed_bills': Bill.objects.filter(status='PASSED').count(),
        'loksabha_bills': Bill.objects.filter(house='LOK_SABHA').count(),
        'rajyasabha_bills': Bill.objects.filter(house='RAJYA_SABHA').count(),
        'recent_bills': Bill.objects.order_by('-introduction_date')[:10],
    }
    return render(request, 'bills/dashboard.html', context)

def bill_list(request):
    """Show all bills with search and filter"""
    bills = Bill.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        bills = bills.filter(
            Q(title__icontains=search_query) |
            Q(bill_id__icontains=search_query) |
            Q(bill_number__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(introduced_by__icontains=search_query)
        )
    
    # Filter by house
    house = request.GET.get('house', '')
    if house:
        bills = bills.filter(house=house)
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        bills = bills.filter(status=status)
    
    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        bills = bills.filter(introduction_date__gte=date_from)
    if date_to:
        bills = bills.filter(introduction_date__lte=date_to)
    
    # Pagination - show all bills with pagination
    paginator = Paginator(bills, 20)  # Show 20 bills per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    houses = Bill.objects.values_list('house', flat=True).distinct()
    statuses = Bill.objects.values_list('status', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_house': house,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
        'houses': houses,
        'statuses': statuses,
        'total_count': bills.count(),
    }
    return render(request, 'bills/bill_list.html', context)

def bill_detail(request, pk):
    """Show detailed view of a single bill"""
    bill = get_object_or_404(Bill, pk=pk)
    return render(request, 'bills/bill_detail.html', {'bill': bill})

def analytics(request):
    """Analytics view with charts"""
    # Status distribution
    status_counts = Bill.objects.values('status').annotate(count=Count('status'))
    
    # House distribution
    house_counts = Bill.objects.values('house').annotate(count=Count('house'))
    
    # Monthly introduction trend
    last_year = timezone.now() - timedelta(days=365)
    monthly_bills = Bill.objects.filter(
        introduction_date__gte=last_year
    ).extra({
        'month': "strftime('%%Y-%%m', introduction_date)"
    }).values('month').annotate(count=Count('id')).order_by('month')
    
    context = {
        'status_counts': json.dumps(list(status_counts)),
        'house_counts': json.dumps(list(house_counts)),
        'monthly_bills': json.dumps(list(monthly_bills)),
        'total_bills': Bill.objects.count(),
    }
    return render(request, 'bills/analytics.html', context)

def map_view(request):
    """Map view for bills by region"""
    # Get bills by state/region (you'll need to add region field to model)
    bills_by_region = Bill.objects.values('introduced_by_party').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'bills_by_region': json.dumps(list(bills_by_region)),
    }
    return render(request, 'bills/map.html', context)

def calendar_view(request):
    """Calendar view for bill introduction dates"""
    from django.http import HttpResponse
    from icalendar import Calendar, Event
    import uuid
    
    # Get date from query params
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    bills = Bill.objects.exclude(introduction_date__isnull=True)
    
    if year and month:
        bills = bills.filter(
            introduction_date__year=year,
            introduction_date__month=month
        )
    
    # Check if iCal download requested
    if request.GET.get('format') == 'ical':
        cal = Calendar()
        cal.add('prodid', '-//Parliament Tracker//parliament.gov.in//')
        cal.add('version', '2.0')
        
        for bill in bills[:50]:
            event = Event()
            event.add('summary', f"{bill.bill_id}: {bill.title[:50]}")
            event.add('dtstart', bill.introduction_date)
            event.add('dtend', bill.introduction_date)
            event.add('dtstamp', timezone.now())
            event.add('uid', str(uuid.uuid4()))
            event.add('description', f"Bill introduced in {bill.get_house_display()}")
            cal.add_component(event)
        
        response = HttpResponse(cal.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename=bills.ics'
        return response
    
    context = {
        'bills': bills[:50],
        'year': year,
        'month': month,
    }
    return render(request, 'bills/calendar.html', context)

def api_bills(request):
    """API endpoint for bills"""
    bills = Bill.objects.all()
    
    # Apply filters
    house = request.GET.get('house')
    if house:
        bills = bills.filter(house=house)
    
    status = request.GET.get('status')
    if status:
        bills = bills.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        bills = bills.filter(
            Q(title__icontains=search) |
            Q(bill_id__icontains=search)
        )
    
    limit = int(request.GET.get('limit', 100))
    bills = bills[:limit]
    
    data = [{
        'id': str(bill.id),
        'bill_id': bill.bill_id,
        'title': bill.title,
        'house': bill.house,
        'status': bill.status,
        'introduction_date': bill.introduction_date.isoformat() if bill.introduction_date else None,
        'introduced_by': bill.introduced_by,
    } for bill in bills]
    
    return JsonResponse({'bills': data, 'count': len(data)})

@shared_task
def scrape_all_sources():
    """Celery task to scrape all sources"""
    results = {}
    
    # Scrape PRS
    try:
        prs_count = scrape_prs()
        results['PRS'] = prs_count
    except Exception as e:
        logger.error(f"PRS scrape failed: {e}")
        results['PRS'] = f"Error: {e}"
    
    # Scrape Lok Sabha
    try:
        ls_count = scrape_loksabha()
        results['LOK_SABHA'] = ls_count
    except Exception as e:
        logger.error(f"Lok Sabha scrape failed: {e}")
        results['LOK_SABHA'] = f"Error: {e}"
    
    # Scrape Rajya Sabha
    try:
        rs_count = scrape_rajyasabha()
        results['RAJYA_SABHA'] = rs_count
    except Exception as e:
        logger.error(f"Rajya Sabha scrape failed: {e}")
        results['RAJYA_SABHA'] = f"Error: {e}"
    
    return results

def trigger_scrape(request):
    """Manual trigger for scraping"""
    if request.method == 'POST':
        source = request.POST.get('source', 'all')
        
        if source == 'all' or source == 'PRS':
            scrape_all_sources.delay()
        elif source == 'LOK_SABHA':
            scrape_loksabha.delay()
        elif source == 'RAJYA_SABHA':
            scrape_rajyasabha.delay()
        
        return JsonResponse({'status': 'scraping_started'})
    
    sources = ScrapeSource.objects.filter(is_active=True)
    return render(request, 'bills/scrape.html', {'sources': sources})