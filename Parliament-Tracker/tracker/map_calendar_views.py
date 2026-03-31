from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
from .models import State, CalendarEvent


class GeographicMapView(TemplateView):
    template_name = "tracker/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        states = State.objects.all()

        context["states"] = [
            {
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "bills_introduced": s.bills_introduced,
                "bills_passed": s.bills_passed,
                "total_mps": s.total_mps,
            }
            for s in states
        ]
        return context


class LegislativeCalendarView(TemplateView):
    template_name = "tracker/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now()
        upcoming = CalendarEvent.objects.filter(
            start_datetime__gte=today,
            start_datetime__lte=today + timedelta(days=30)
        ).order_by("start_datetime")

        context["events"] = upcoming
        return context

