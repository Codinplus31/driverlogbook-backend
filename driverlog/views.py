from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import math

def calculate_route_and_distance(start, pickup, dropoff):
    geolocator = Nominatim(user_agent="driverlog-pro")
    
    def get_coords(location_name):
        try:
            loc = geolocator.geocode(location_name)
            if loc:
                return (loc.latitude, loc.longitude)
        except:
            pass
        fallbacks = {
            'chicago, il': (41.8781, -87.6298),
            'st. louis, mo': (38.6270, -90.1994),
            'atlanta, ga': (33.7490, -84.3880),
            'new york, ny': (40.7128, -74.0060),
            'los angeles, ca': (34.0522, -118.2437),
            'dallas, tx': (32.7767, -96.7970),
            'phoenix, az': (33.4484, -112.0740),
            'seattle, wa': (47.6062, -122.3321),
            'denver, co': (39.7392, -104.9903),
            'austin, tx': (30.2672, -97.7431),
        }
        location_lower = location_name.lower()
        for key, coords in fallbacks.items():
            if key in location_lower:
                return coords
        return (0, 0)  
    
    start_coords = get_coords(start)
    pickup_coords = get_coords(pickup)
    dropoff_coords = get_coords(dropoff)
    
    dist_start_pickup = geodesic(start_coords, pickup_coords).miles if start_coords != (0, 0) and pickup_coords != (0, 0) else 0
    dist_pickup_dropoff = geodesic(pickup_coords, dropoff_coords).miles if pickup_coords != (0, 0) and dropoff_coords != (0, 0) else 0
    total_distance = dist_start_pickup + dist_pickup_dropoff
    
    route_points = [start_coords, pickup_coords, dropoff_coords]
    
    return {
        'route_points': route_points,
        'total_distance': round(total_distance, 1),
        'distances': {
            'start_to_pickup': round(dist_start_pickup, 1),
            'pickup_to_dropoff': round(dist_pickup_dropoff, 1)
        }
    }

def calculate_eld_logs(current_cycle_used, distance_miles):
    logs = []
    remaining_cycle = current_cycle_used
    current_day = 1
    total_driving = distance_miles / 55  
    total_on_duty = 2  
    total_fuel_stops = math.floor(distance_miles / 1000)
    total_fuel_time = total_fuel_stops * 1  
    
    total_trip_hours = total_driving + total_on_duty + total_fuel_time
    remaining_driving = total_driving
    remaining_on_duty = total_on_duty + total_fuel_time
    
    while remaining_driving > 0 or remaining_on_duty > 0:
        day_log = {
            'day': current_day,
            'entries': [],
            'total_driving': 0,
            'total_on_duty': 0,
            'total_sleeper': 0,
            'total_off_duty': 0
        }
        
        available_driving = 11
        available_on_duty = 14
        day_used = 0
        
        if remaining_on_duty > 0 and available_on_duty > 0:
            use = min(remaining_on_duty, available_on_duty)
            day_log['entries'].append({
                'time': '06:00',
                'activity': 'On-Duty',
                'duration': round(use, 1),
                'color': 'bg-blue-400'
            })
            day_used += use
            available_on_duty -= use
            remaining_on_duty -= use
            day_log['total_on_duty'] += use
        
        while available_driving > 0 and remaining_driving > 0:
            drive = min(available_driving, remaining_driving)
            if drive <= 0:
                break
                
            day_log['entries'].append({
                'time': '07:00' if len(day_log['entries']) == 0 else '10:00',
                'activity': 'Driving',
                'duration': round(drive, 1),
                'color': 'bg-green-500'
            })
            
            day_used += drive
            available_driving -= drive
            remaining_driving -= drive
            day_log['total_driving'] += drive
        
        if total_fuel_time > 0 and day_log['total_driving'] > 0:
            fuel_to_use = min(total_fuel_time, 2)  
            if fuel_to_use > 0 and available_on_duty >= fuel_to_use:
                day_log['entries'].append({
                    'time': '14:00',
                    'activity': 'Fuel Stop',
                    'duration': fuel_to_use,
                    'color': 'bg-yellow-400'
                })
                day_used += fuel_to_use
                available_on_duty -= fuel_to_use
                total_fuel_time -= fuel_to_use
                day_log['total_on_duty'] += fuel_to_use
        
        if remaining_on_duty > 0 and available_on_duty > 0:
            use = min(remaining_on_duty, available_on_duty)
            day_log['entries'].append({
                'time': '16:00',
                'activity': 'On-Duty',
                'duration': round(use, 1),
                'color': 'bg-blue-400'
            })
            day_used += use
            available_on_duty -= use
            remaining_on_duty -= use
            day_log['total_on_duty'] += use
        
        if day_log['total_driving'] >= 11 or (day_used >= 14 and (remaining_driving > 0 or remaining_on_duty > 0)):
            sleep = 10
            day_log['entries'].append({
                'time': '20:00',
                'activity': 'Sleeper Berth',
                'duration': sleep,
                'color': 'bg-purple-500'
            })
            day_log['total_sleeper'] = sleep
        elif remaining_driving == 0 and remaining_on_duty == 0:
            off = 14 - day_used
            if off > 0:
                day_log['entries'].append({
                    'time': '20:00',
                    'activity': 'Off-Duty',
                    'duration': round(off, 1),
                    'color': 'bg-gray-400'
                })
                day_log['total_off_duty'] = off
        
        logs.append(day_log)
        current_day += 1
        
        if remaining_driving <= 0 and remaining_on_duty <= 0:
            break
            
    return logs

@csrf_exempt
@require_http_methods(["POST"])
def generate_trip(request):
    try:
        data = json.loads(request.body)
        
        current_location = data.get('currentLocation', '').strip()
        pickup_location = data.get('pickupLocation', '').strip()
        dropoff_location = data.get('dropoffLocation', '').strip()
        current_cycle_used = float(data.get('currentCycleUsed', 0))
        
        if not all([current_location, pickup_location, dropoff_location]):
            return JsonResponse({'error': 'All locations are required'}, status=400)
        
        if current_cycle_used < 0 or current_cycle_used > 70:
            return JsonResponse({'error': 'Current cycle used must be between 0 and 70 hours'}, status=400)
        
        route_data = calculate_route_and_distance(current_location, pickup_location, dropoff_location)
        
        eld_logs = calculate_eld_logs(current_cycle_used, route_data['total_distance'])
        
        trip_hours_used = sum(log['total_driving'] + log['total_on_duty'] for log in eld_logs)
        remaining_cycle = max(0, 70 - (current_cycle_used + trip_hours_used))
        
        response_data = {
            'success': True,
            'route': route_data,
            'logs': eld_logs,
            'trip_hours_used': round(trip_hours_used, 1),
            'remaining_cycle': round(remaining_cycle, 1),
            'message': 'ELD logs generated successfully'
        }
        
        return JsonResponse(response_data, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

def health_check(request):
    return JsonResponse({
        'status': 'ok',
        'service': 'Driverlog Django Backend',
        'version': '1.0'
    })
