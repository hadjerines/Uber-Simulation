import math

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def calculate_surge(driver_count, request_count):
    ratio = request_count / max(1, driver_count)
    return min(3.0, max(1.0, 1.0 + (ratio - 1) * 0.5))

def calculate_fare(distance_km, duration_min, ride_type="UberX"):
    base_fares = {"UberX": 2.50, "UberBlack": 5.00, "UberXL": 3.50}
    per_km = {"UberX": 1.50, "UberBlack": 3.00, "UberXL": 2.00}
    per_min = {"UberX": 0.30, "UberBlack": 0.50, "UberXL": 0.40}
    
    base = base_fares.get(ride_type, 2.50)
    distance_cost = distance_km * per_km.get(ride_type, 1.50)
    time_cost = duration_min * per_min.get(ride_type, 0.30)
    
    surge = calculate_surge(
        len([d for d in DRIVERS if d["status"] == "Available"]),
        len([p for p in PASSENGERS if p["ride_status"] == "Not Booked"])
    )
    return round((base + distance_cost + time_cost) * surge, 2)

def find_closest_driver(lat, lon):
    closest = None
    min_distance = float('inf')
    for driver in DRIVERS:
        if driver["status"] == "Available":
            dist = calculate_distance(lat, lon, driver["lat"], driver["lon"])
            if dist < min_distance:
                min_distance = dist
                closest = driver
    return closest

def find_pool_match(passenger):
    return [p for p in PASSENGERS 
            if p["name"] != passenger["name"]
            and calculate_distance(p["lat"], p["lon"], 
                                 passenger["lat"], passenger["lon"]) <= POOL_RADIUS]

def add_markers(map_widget):
    for p in PASSENGERS:
        color = "green" if p["ride_status"] == "Not Booked" else "red"
        map_widget.set_marker(p["lat"], p["lon"], text=p["name"] + " 🪴", marker_color_outside=color)
    for d in DRIVERS:
        color = "blue" if d["status"] == "Available" else "orange"
        map_widget.set_marker(d["lat"], d["lon"], text=d["name"] + " 🚗", marker_color_outside=color)