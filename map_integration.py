from math import sqrt
# Add sample markers for drivers and passengers
DRIVERS = [
    {"name": "Driver A", "lat": 40.715, "lon": -74.002},
    {"name": "Driver B", "lat": 40.722, "lon": -74.010},
]

PASSENGERS = [
    {"name": "Passenger X", "lat": 40.708, "lon": -74.015},
    {"name": "Passenger Y", "lat": 40.730, "lon": -74.000},
]

def add_markers(map_widget):
    for driver in DRIVERS:
        map_widget.set_marker(driver["lat"], driver["lon"], text=driver["name"] + " 🚗")

    for passenger in PASSENGERS:
        map_widget.set_marker(passenger["lat"], passenger["lon"], text=passenger["name"] + " 🧍")



def find_closest_driver(passenger_lat, passenger_lon):
    min_dist = float('inf')
    closest = None
    for driver in DRIVERS:
        dist = sqrt((passenger_lat - driver["lat"]) ** 2 + (passenger_lon - driver["lon"]) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest = driver
    return closest
