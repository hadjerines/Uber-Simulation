import tkinter as tk
from tkinter import ttk
from tkintermapview import TkinterMapView
import threading
import time
import math
import random

PASSENGERS = [
    {"name": "Alice", "lat": 40.730610, "lon": -73.935242, "ride_status": "Not Booked"},
    {"name": "Bob", "lat": 40.712776, "lon": -74.005974, "ride_status": "Not Booked"},
    {"name": "Charlie", "lat": 40.758896, "lon": -73.985130, "ride_status": "Not Booked"}
]

DRIVERS = [
    {"name": "Driver1", "lat": 40.740610, "lon": -73.935242, "status": "Available"},
    {"name": "Driver2", "lat": 40.722776, "lon": -74.005974, "status": "Available"}
]

RIDE_STATS = {"total_rides": 0, "completed_rides": 0, "total_wait_time": 0}
RIDE_QUEUE = []


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
    for p in PASSENGERS:
        map_widget.set_marker(p["lat"], p["lon"], text=p["name"] + " 🪴")
    for d in DRIVERS:
        map_widget.set_marker(d["lat"], d["lon"], text=d["name"] + " 🚗")

class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Welcome to Uber Simulation", font=("Arial", 24)).pack(pady=20)
        tk.Button(self, text="View Map", command=lambda: controller.show_page("MainPage")).pack(pady=10)
        tk.Button(self, text="Book a Ride", command=lambda: controller.show_page("BookingPage")).pack(pady=10)
        # In MenuPage class
        tk.Button(self, text="Ride History", command=lambda: controller.show_page("RideHistoryPage")).pack(pady=10)
        tk.Button(self, text="Exit", command=controller.quit).pack(pady=10)

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Uber Simulation Map", font=("Arial", 24)).pack(pady=10)

        self.map_widget = TkinterMapView(self, width=800, height=500, corner_radius=0)
        self.map_widget.set_position(40.730610, -73.935242)
        self.map_widget.set_zoom(12)
        self.map_widget.pack(side="left")

        self.side_panel = tk.Frame(self)
        self.side_panel.pack(side="right", fill="y", padx=10)

        self.info_label = tk.Label(self.side_panel, text="Ride Info:", font=("Arial", 14))
        self.info_label.pack(pady=5)

        self.stats_label = tk.Label(self.side_panel, text="", font=("Arial", 12))
        self.stats_label.pack(pady=5)

        tk.Label(self.side_panel, text="Passenger Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.passenger_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.passenger_status_text.pack(pady=5)

        tk.Label(self.side_panel, text="Driver Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.driver_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.driver_status_text.pack(pady=5)

        tk.Label(self.side_panel, text="Ride Log", font=("Arial", 14, "bold")).pack(pady=5)
        self.ride_log_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.ride_log_text.pack(pady=5)

        self.heatmap_label = tk.Label(self.side_panel, text="", font=("Arial", 12), fg="red")
        self.heatmap_label.pack(pady=5)

        tk.Button(self.side_panel, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=5)
        tk.Button(self.side_panel, text="Back to Booking", command=lambda: controller.show_page("BookingPage")).pack(pady=5)

        add_markers(self.map_widget)
        self.update_stats()
        self.update_passenger_status()
        self.update_driver_status()
        self.update_heatmap()
        self.start_idle_driver_movement()
        self.process_ride_queue()

    def update_stats(self):
        avg_wait = RIDE_STATS["total_wait_time"] / RIDE_STATS["completed_rides"] if RIDE_STATS["completed_rides"] > 0 else 0
        self.stats_label.config(text=f"Total Rides: {RIDE_STATS['total_rides']}, Completed: {RIDE_STATS['completed_rides']}, Avg Wait Time: {avg_wait:.1f}s")
        self.after(3000, self.update_stats)

    def update_passenger_status(self):
        self.passenger_status_text.config(state="normal")
        self.passenger_status_text.delete("1.0", tk.END)
        for p in PASSENGERS:
            self.passenger_status_text.insert(tk.END, f"{p['name']}: {p['ride_status']}\n")
        self.passenger_status_text.config(state="disabled")
        self.after(2000, self.update_passenger_status)

    def update_driver_status(self):
        self.driver_status_text.config(state="normal")
        self.driver_status_text.delete("1.0", tk.END)
        for d in DRIVERS:
            self.driver_status_text.insert(tk.END, f"{d['name']}: {d['status']} ({d['lat']:.5f}, {d['lon']:.5f})\n")
        self.driver_status_text.config(state="disabled")
        self.after(2000, self.update_driver_status)

    def update_heatmap(self):
        hot_spots = [p for p in PASSENGERS if p["ride_status"] == "Not Booked"]
        self.heatmap_label.config(text=f"\u26a0\ufe0f High demand at {len(hot_spots)} location(s)" if hot_spots else "No high-demand zones.")
        self.after(3000, self.update_heatmap)

    def log_ride_event(self, message):
        if not hasattr(self, 'ride_logs'):
            self.ride_logs = []
        self.ride_logs.append(message)
        self.ride_log_text.config(state="normal")
        self.ride_log_text.insert(tk.END, message + "\n")
        self.ride_log_text.see(tk.END)
        self.ride_log_text.config(state="disabled")

    def simulate_ride(self, passenger_name, destination_coords):
        passenger = next((p for p in PASSENGERS if p["name"] == passenger_name), None)
        driver = find_closest_driver(passenger["lat"], passenger["lon"])

        if not driver:
            self.info_label.config(text="No driver available!")
            self.log_ride_event(f"No driver available for {passenger_name}, added to queue")
            RIDE_QUEUE.append((passenger_name, destination_coords))
            return

        RIDE_STATS["total_rides"] += 1
        wait_start = time.time()
        passenger["ride_status"] = "In Progress"
        driver["status"] = "Busy"
        self.map_widget.delete_all_marker()
        self.map_widget.set_marker(driver["lat"], driver["lon"], text=driver["name"] + " 🚗")
        self.map_widget.set_marker(passenger["lat"], passenger["lon"], text=passenger["name"] + " 🪴")
        self.map_widget.set_marker(destination_coords[0], destination_coords[1], text="Destination 🎯")
        self.info_label.config(text=f"{driver['name']} is picking up {passenger_name}...")
        self.log_ride_event(f"{driver['name']} assigned to {passenger_name}")

        def animate_ride():
            self.animate_move(driver, (driver["lat"], driver["lon"]), (passenger["lat"], passenger["lon"]))
            RIDE_STATS["total_wait_time"] += time.time() - wait_start
            self.log_ride_event(f"{driver['name']} picked up {passenger_name}")
            time.sleep(1)
            self.animate_move(driver, (passenger["lat"], passenger["lon"]), destination_coords)
            time.sleep(1)
            passenger["ride_status"] = "Completed"
            driver["status"] = "Available"
            RIDE_STATS["completed_rides"] += 1
            self.info_label.config(text=f"{driver['name']} completed the ride for {passenger_name}.")
            self.log_ride_event(f"{driver['name']} completed ride for {passenger_name}")
            add_markers(self.map_widget)

        threading.Thread(target=animate_ride, daemon=True).start()

    def animate_move(self, driver, start, end, steps=20, delay=0.2):
        lat_diff = (end[0] - start[0]) / steps
        lon_diff = (end[1] - start[1]) / steps
        lat, lon = start
        for _ in range(steps):
            lat += lat_diff
            lon += lon_diff
            driver["lat"], driver["lon"] = lat, lon
            direction_emoji = "➡️"
            if abs(lat_diff) > abs(lon_diff):
                direction_emoji = "⬆️" if lat_diff > 0 else "⬇️"
            else:
                direction_emoji = "➡️" if lon_diff > 0 else "⬅️"
            self.map_widget.delete_all_marker()
            self.map_widget.set_marker(lat, lon, text=driver["name"] + " " + direction_emoji)
            self.map_widget.set_marker(end[0], end[1], text="Destination 🎯")
            self.update_passenger_status()
            time.sleep(delay + random.uniform(0, 0.2))

    def start_idle_driver_movement(self):
        def move_idle_drivers():
            while True:
                for driver in DRIVERS:
                    if driver["status"] == "Available":
                        driver["lat"] += random.uniform(-0.0003, 0.0003)
                        driver["lon"] += random.uniform(-0.0003, 0.0003)
                time.sleep(3)
        threading.Thread(target=move_idle_drivers, daemon=True).start()

    def process_ride_queue(self):
        def check_queue():
            while True:
                if RIDE_QUEUE:
                    passenger_name, destination = RIDE_QUEUE[0]
                    driver = find_closest_driver(*destination)
                    if driver:
                        RIDE_QUEUE.pop(0)
                        self.simulate_ride(passenger_name, destination)
                time.sleep(5)
        threading.Thread(target=check_queue, daemon=True).start()

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

# ... [keep your imports and global data as-is]

class RideHistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Ride History", font=("Arial", 24)).pack(pady=10)
        self.history_text = tk.Text(self, height=30, width=100, state="disabled")
        self.history_text.pack(pady=10)
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=5)

    def update_history(self, ride_logs):
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)
        for log in ride_logs:
            self.history_text.insert(tk.END, log + "\n")
        self.history_text.config(state="disabled")


class UberSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Uber Simulation")
        self.geometry("1200x700")
        
        # Create a container to hold all frames
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        # Initialize all pages
        for F in (MenuPage, MainPage, BookingPage, RideHistoryPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("MenuPage")

    def show_page(self, page_name):
        frame = self.frames.get(page_name)
        if frame is None:
            print(f"Error: Page {page_name} not found!")
            return
            
        # Special handling for RideHistoryPage
        if page_name == "RideHistoryPage":
            main_page = self.frames["MainPage"]
            ride_logs = getattr(main_page, 'ride_logs', [])
            frame.update_history(ride_logs)
            
        frame.tkraise()
        print(f"Successfully showed {page_name}")

# Keep the rest of your code (MainPage, BookingPage, etc.) exactly the same


if __name__ == "__main__":
    app = UberSimulationApp()
    app.mainloop()
