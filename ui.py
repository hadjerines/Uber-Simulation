import tkinter as tk
from tkinter import ttk
from tkintermapview import TkinterMapView
import threading
import time
import math

# Sample data
PASSENGERS = [
    {"name": "Alice", "lat": 40.730610, "lon": -73.935242, "ride_status": "Not Booked"},
    {"name": "Bob", "lat": 40.712776, "lon": -74.005974, "ride_status": "Not Booked"},
    {"name": "Charlie", "lat": 40.758896, "lon": -73.985130, "ride_status": "Not Booked"}
]

DRIVERS = [
    {"name": "Driver1", "lat": 40.740610, "lon": -73.935242, "status": "Available"},
    {"name": "Driver2", "lat": 40.722776, "lon": -74.005974, "status": "Available"}
]

RIDE_STATS = {
    "total_rides": 0,
    "completed_rides": 0,
    "total_wait_time": 0
}

# Utility function to calculate distance
def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

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

def add_markers(map_widget):
    for passenger in PASSENGERS:
        map_widget.set_marker(passenger["lat"], passenger["lon"], text=passenger["name"] + " 🪽")
    for driver in DRIVERS:
        map_widget.set_marker(driver["lat"], driver["lon"], text=driver["name"] + " 🚗")

class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Welcome to Uber Simulation", font=("Arial", 24)).pack(pady=20)
        tk.Button(self, text="View Map", command=lambda: controller.show_page("MainPage")).pack(pady=10)
        tk.Button(self, text="Book a Ride", command=lambda: controller.show_page("BookingPage")).pack(pady=10)
        tk.Button(self, text="Exit", command=controller.quit).pack(pady=10)

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Uber Simulation Map", font=("Arial", 24)).pack(pady=10)
        self.map_widget = TkinterMapView(self, width=800, height=500, corner_radius=0)
        self.map_widget.set_position(40.730610, -73.935242)
        self.map_widget.set_zoom(12)
        self.map_widget.pack()
        add_markers(self.map_widget)

        self.info_label = tk.Label(self, text="Ride Info:", font=("Arial", 14))
        self.info_label.pack(pady=5)

        self.stats_label = tk.Label(self, text="", font=("Arial", 12))
        self.stats_label.pack()

        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=5)
        tk.Button(self, text="Back to Booking", command=lambda: controller.show_page("BookingPage")).pack(pady=5)

        self.update_stats()

    def update_stats(self):
        if RIDE_STATS["completed_rides"] > 0:
            avg_wait = RIDE_STATS["total_wait_time"] / RIDE_STATS["completed_rides"]
        else:
            avg_wait = 0
        self.stats_label.config(text=f"Total Rides: {RIDE_STATS['total_rides']}, Completed: {RIDE_STATS['completed_rides']}, Avg Wait Time: {avg_wait:.1f}s")
        self.after(3000, self.update_stats)

    def simulate_ride(self, passenger_name, destination_coords):
        passenger = next((p for p in PASSENGERS if p["name"] == passenger_name), None)
        driver = find_closest_driver(passenger["lat"], passenger["lon"])

        if not driver:
            self.info_label.config(text="No driver available!")
            return

        RIDE_STATS["total_rides"] += 1
        wait_start = time.time()

        passenger["ride_status"] = "In Progress"
        driver["status"] = "Busy"
        self.map_widget.delete_all_marker()
        self.map_widget.set_marker(driver["lat"], driver["lon"], text=driver["name"] + " 🚗")
        self.map_widget.set_marker(passenger["lat"], passenger["lon"], text=passenger["name"] + " 🪽")
        self.map_widget.set_marker(destination_coords[0], destination_coords[1], text="Destination 🎯")
        self.info_label.config(text=f"{driver['name']} is picking up {passenger_name}...")

        def animate_ride():
            self.animate_move(driver, (driver["lat"], driver["lon"]), (passenger["lat"], passenger["lon"]))
            RIDE_STATS["total_wait_time"] += time.time() - wait_start
            time.sleep(1)
            self.animate_move(driver, (passenger["lat"], passenger["lon"]), destination_coords)
            time.sleep(1)
            passenger["ride_status"] = "Completed"
            driver["status"] = "Available"
            RIDE_STATS["completed_rides"] += 1
            self.info_label.config(text=f"{driver['name']} completed the ride for {passenger_name}.")
            add_markers(self.map_widget)

        threading.Thread(target=animate_ride, daemon=True).start()

    def animate_move(self, driver, start, end, steps=20, delay=0.2):
        lat_diff = (end[0] - start[0]) / steps
        lon_diff = (end[1] - start[1]) / steps
        lat, lon = start
        for _ in range(steps):
            lat += lat_diff
            lon += lon_diff
            self.map_widget.delete_all_marker()
            self.map_widget.set_marker(lat, lon, text=driver["name"] + " 🚗")
            self.map_widget.set_marker(end[0], end[1], text="Destination 🎯")
            time.sleep(delay)

class BookingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Book a Ride", font=("Arial", 24)).pack(pady=10)
        tk.Label(self, text="Select Passenger:").pack(pady=5)
        self.passenger_var = tk.StringVar()
        self.passenger_dropdown = ttk.Combobox(self, textvariable=self.passenger_var)
        self.passenger_dropdown['values'] = [p["name"] for p in PASSENGERS]
        self.passenger_dropdown.current(0)
        self.passenger_dropdown.pack(pady=5)

        tk.Label(self, text="Enter Destination Coordinates (lat, lon):").pack(pady=5)
        self.destination_entry = tk.Entry(self)
        self.destination_entry.insert(0, "40.735, -74.002")
        self.destination_entry.pack(pady=5)

        tk.Button(self, text="Confirm Booking", command=self.book_ride).pack(pady=10)
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=5)

    def book_ride(self):
        passenger_name = self.passenger_var.get()
        destination = self.destination_entry.get()
        try:
            lat, lon = map(float, destination.split(","))
        except ValueError:
            print("Invalid destination coordinates.")
            return

        main_page = self.controller.frames["MainPage"]
        main_page.simulate_ride(passenger_name, (lat, lon))
        self.controller.show_page("MainPage")

class UberSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Uber Simulation")
        self.geometry("900x700")
        self.frames = {}

        for F in (MenuPage, MainPage, BookingPage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("MenuPage")

    def show_page(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

if __name__ == "__main__":
    app = UberSimulationApp()
    app.mainloop()
