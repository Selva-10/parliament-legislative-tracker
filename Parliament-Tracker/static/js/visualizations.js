class ParliamentVisualizer {
    constructor() {
        this.colors = { parties: { BJP:'#FF9933', Congress:'#138808' }, status: { introduced:'#4285F4', passed_both:'#0F9D58' } };
    }
    createBarChart(containerId, labels, data, label='Count') {
        const ctx = document.getElementById(containerId).getContext('2d');
        return new Chart(ctx, { type:'bar', data:{ labels:labels, datasets:[{ label:label, data:data, backgroundColor:'#1a237e' }] } });
    }
    createPieChart(containerId, labels, data) {
        const ctx = document.getElementById(containerId).getContext('2d');
        return new Chart(ctx, { type:'pie', data:{ labels:labels, datasets:[{ data:data, backgroundColor:['#4285F4','#EA4335','#FBBC05','#34A853'] }] } });
    }
    initMap(containerId, center=[20.5937,78.9629], zoom=5) {
        const map = L.map(containerId).setView(center, zoom);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution:'© OpenStreetMap' }).addTo(map);
        return map;
    }
    addMarkers(map, states) {
        states.forEach(s => {
            L.marker([s.coordinates.lat, s.coordinates.lng]).bindPopup(`<b>${s.state}</b><br>Bills: ${s.metrics.bills_introduced}`).addTo(map);
        });
    }
    initCalendar(containerId, events) {
        const calendarEl = document.getElementById(containerId);
        return new FullCalendar.Calendar(calendarEl, { initialView:'dayGridMonth', events:events });
    }
}
const parliamentViz = new ParliamentVisualizer();