"""Geofence utility functions for attendance tracking."""
from math import radians, cos, sin, asin, sqrt


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    Returns distance in meters.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r


def is_within_geofence(student_lat, student_lon, teacher_lat, teacher_lon, radius_meters):
    """
    Check if student is within the geofence radius around the teacher's location.
    Returns True if student is within radius, False otherwise.
    """
    distance = haversine_distance(
        float(student_lat), float(student_lon),
        float(teacher_lat), float(teacher_lon)
    )
    return distance <= radius_meters
