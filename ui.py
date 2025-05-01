import tkinter as tk
from tkinter import ttk, messagebox
from tkintermapview import TkinterMapView
import threading
import time
import math
import random
import json
import os
from datetime import datetime

# Data storage files
USERS_FILE = "users.json"
RIDES_FILE = "rides.json"

# Initialize data files if they don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({"passengers": {}, "drivers": {}}, f)

if not os.path.exists(RIDES_FILE):
    with open(RIDES_FILE, 'w') as f:
        json.dump([], f)

class UserManager:
    @staticmethod
    def load_users():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_users(data):
        with open(USERS_FILE, 'w') as f:
            json.dump(data, f)
    
    @staticmethod
    def load_rides():
        with open(RIDES_FILE, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_rides(data):
        with open(RIDES_FILE, 'w') as f:
            json.dump(data, f)

# Sample data with persistence
PASSENGERS = [
    {"name": "Alice", "lat": 40.730610, "lon": -73.935242, "ride_status": "Not Booked", "rating": 4.5},
    {"name": "Bob", "lat": 40.712776, "lon": -74.005974, "ride_status": "Not Booked", "rating": 4.2},
    {"name": "Charlie", "lat": 40.758896, "lon": -73.985130, "ride_status": "Not Booked", "rating": 4.8}
]

DRIVERS = [
    {"name": "Driver1", "lat": 40.740610, "lon": -73.935242, "status": "Available", "rating": 4.7, "earnings": 0},
    {"name": "Driver2", "lat": 40.722776, "lon": -74.005974, "status": "Available", "rating": 4.9, "earnings": 0}
]

RIDE_STATS = {"total_rides": 0, "completed_rides": 0, "total_wait_time": 0, "total_earnings": 0}
RIDE_QUEUE = []
# Add after RIDE_QUEUE
TRAFFIC_ZONES = [
    {"lat": 40.730, "lon": -73.935, "radius": 0.01, "delay_factor": 1.5},
    {"lat": 40.712, "lon": -74.005, "radius": 0.008, "delay_factor": 2.0}
]

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)

def calculate_fare(distance_km, duration_min, ride_type="UberX"):
    base_fares = {"UberX": 2.50, "UberBlack": 5.00, "UberXL": 3.50}
    per_km = {"UberX": 1.50, "UberBlack": 3.00, "UberXL": 2.00}
    per_min = {"UberX": 0.30, "UberBlack": 0.50, "UberXL": 0.40}
    
    base = base_fares.get(ride_type, 2.50)
    distance_cost = distance_km * per_km.get(ride_type, 1.50)
    time_cost = duration_min * per_min.get(ride_type, 0.30)
    
    # Apply surge pricing (1.0x to 3.0x randomly)
    surge = 1.0 + random.random() * 2
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

def add_markers(map_widget):
    for p in PASSENGERS:
        color = "green" if p["ride_status"] == "Not Booked" else "red"
        map_widget.set_marker(p["lat"], p["lon"], text=p["name"] + " 🪴", marker_color_outside=color)
    for d in DRIVERS:
        color = "blue" if d["status"] == "Available" else "orange"
        map_widget.set_marker(d["lat"], d["lon"], text=d["name"] + " 🚗", marker_color_outside=color)

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Uber Simulation", font=("Arial", 24)).pack(pady=20)
        
        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        
        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        
        tk.Button(self, text="Login", command=self.login).pack(pady=10)
        tk.Button(self, text="Register", command=lambda: controller.show_page("RegisterPage")).pack()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        users = UserManager.load_users()
        
        if username in users["passengers"]:
            if users["passengers"][username]["password"] == password:
                self.controller.current_user = username
                self.controller.show_page("MenuPage")
                return
        
        if username in users["drivers"]:
            if users["drivers"][username]["password"] == password:
                self.controller.current_user = username
                self.controller.show_page("DriverDashboard")
                return
        
        messagebox.showerror("Error", "Invalid username or password")

class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Register", font=("Arial", 24)).pack(pady=20)
        
        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()
        
        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()
        
        tk.Label(self, text="User Type:").pack()
        self.user_type = tk.StringVar(value="passenger")
        tk.Radiobutton(self, text="Passenger", variable=self.user_type, value="passenger").pack()
        tk.Radiobutton(self, text="Driver", variable=self.user_type, value="driver").pack()
        
        tk.Button(self, text="Register", command=self.register).pack(pady=10)
        tk.Button(self, text="Back to Login", command=lambda: controller.show_page("LoginPage")).pack()
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user_type = self.user_type.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        users = UserManager.load_users()
        
        if username in users["passengers"] or username in users["drivers"]:
            messagebox.showerror("Error", "Username already exists")
            return
        
        if user_type == "passenger":
            users["passengers"][username] = {"password": password, "rating": 5.0}
            PASSENGERS.append({
                "name": username,
                "lat": 40.730610 + random.uniform(-0.05, 0.05),
                "lon": -73.935242 + random.uniform(-0.05, 0.05),
                "ride_status": "Not Booked",
                "rating": 5.0
            })
        else:
            users["drivers"][username] = {"password": password, "rating": 5.0, "earnings": 0}
            DRIVERS.append({
                "name": username,
                "lat": 40.730610 + random.uniform(-0.05, 0.05),
                "lon": -73.935242 + random.uniform(-0.05, 0.05),
                "status": "Available",
                "rating": 5.0,
                "earnings": 0
            })
        
        UserManager.save_users(users)
        messagebox.showinfo("Success", "Registration successful!")
        self.controller.show_page("LoginPage")

class MenuPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Safely handle current_user display
        user_display = controller.current_user if hasattr(controller, 'current_user') else "Guest"
        tk.Label(self, text=f"Welcome {user_display}", font=("Arial", 24)).pack(pady=20)
        
        tk.Button(self, text="View Map", command=lambda: controller.show_page("MainPage")).pack(pady=10)
        tk.Button(self, text="Book a Ride", command=lambda: controller.show_page("BookingPage")).pack(pady=10)
        tk.Button(self, text="Ride History", command=lambda: controller.show_page("RideHistoryPage")).pack(pady=10)
        tk.Button(self, text="Account Settings", command=lambda: controller.show_page("AccountPage")).pack(pady=10)
        tk.Button(self, text="Logout", command=self.logout).pack(pady=10)
    
    def logout(self):
        if hasattr(self.controller, 'current_user'):
            self.controller.current_user = None
        self.controller.show_page("LoginPage")
    
class DriverDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Safely handle current_user
        user_display = controller.current_user if hasattr(controller, 'current_user') else "Unknown Driver"
        tk.Label(self, text=f"Driver Dashboard: {user_display}", font=("Arial", 24)).pack(pady=20)

        self.status_var = tk.StringVar(value="Available" if self.driver["status"] == "Available" else "Busy")
        tk.Label(self, text="Status:").pack()
        tk.Radiobutton(self, text="Available", variable=self.status_var, value="Available", command=self.update_status).pack()
        tk.Radiobutton(self, text="Busy", variable=self.status_var, value="Busy", command=self.update_status).pack()
        
        tk.Label(self, text=f"Rating: {self.driver['rating']}").pack()
        tk.Label(self, text=f"Total Earnings: ${self.driver['earnings']:.2f}").pack()
        
        self.current_ride_label = tk.Label(self, text="Current Ride: None")
        self.current_ride_label.pack()
        
        tk.Button(self, text="View Map", command=lambda: controller.show_page("MainPage")).pack(pady=10)
        tk.Button(self, text="Ride History", command=lambda: controller.show_page("RideHistoryPage")).pack(pady=10)
        tk.Button(self, text="Logout", command=self.logout).pack(pady=10)
    
    def update_status(self):
        self.driver["status"] = self.status_var.get()
    
    def logout(self):
        self.controller.current_user = None
        self.controller.show_page("LoginPage")

class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ride_logs = []  # Initialize ride logs list
        
        # Map setup
        self.map_widget = TkinterMapView(self, width=800, height=600, corner_radius=0)
        self.map_widget.set_position(40.730610, -73.935242)
        self.map_widget.set_zoom(12)
        self.map_widget.pack(side="left", fill="both", expand=True)
        
        # Side panel setup
        self.side_panel = tk.Frame(self)
        self.side_panel.pack(side="right", fill="y", padx=10)
        
        # Info labels
        tk.Label(self.side_panel, text="Uber Simulation", font=("Arial", 16)).pack(pady=10)
        self.info_label = tk.Label(self.side_panel, text="", font=("Arial", 12))
        self.info_label.pack(pady=5)
        
        # Stats display
        self.stats_label = tk.Label(self.side_panel, text="", font=("Arial", 12))
        self.stats_label.pack(pady=5)
        
        # Passenger status
        tk.Label(self.side_panel, text="Passenger Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.passenger_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.passenger_status_text.pack(pady=5)
        
        # Driver status
        tk.Label(self.side_panel, text="Driver Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.driver_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.driver_status_text.pack(pady=5)
        
        # Ride log
        tk.Label(self.side_panel, text="Ride Log", font=("Arial", 14, "bold")).pack(pady=5)
        self.ride_log_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.ride_log_text.pack(pady=5)
        
        # Navigation buttons
        tk.Button(self.side_panel, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=10)
        
        # Initial setup
        add_markers(self.map_widget)
        self.update_stats()
        self.update_status()

    def simulate_ride(self, passenger_name, destination_coords, ride_type, fare):
        passenger = next((p for p in PASSENGERS if p["name"] == passenger_name), None)
        if not passenger:
            self.log_ride_event(f"Passenger {passenger_name} not found!")
            return
            
        driver = find_closest_driver(passenger["lat"], passenger["lon"])
        if not driver:
            self.info_label.config(text="No driver available!")
            self.log_ride_event(f"No driver available for {passenger_name}, added to queue")
            RIDE_QUEUE.append((passenger_name, destination_coords, ride_type, fare))
            return

        # Update statuses
        driver["status"] = "Busy"
        passenger["ride_status"] = "In Progress"
        RIDE_STATS["total_rides"] += 1
        
        # Start animation
        threading.Thread(
            target=self.animate_ride,
            args=(driver, passenger, destination_coords, fare),
            daemon=True
        ).start()

    def animate_ride(self, driver, passenger, destination_coords, fare):
        # Phase 1: Driver to pickup
        self.log_ride_event(f"{driver['name']} is picking up {passenger['name']}...")
        self.animate_move(driver, (driver["lat"], driver["lon"]), 
                         (passenger["lat"], passenger["lon"]))
        
        # Phase 2: Pickup to destination
        self.log_ride_event(f"Taking {passenger['name']} to destination...")
        self.animate_move(driver, (passenger["lat"], passenger["lon"]), destination_coords)
        
        # Completion
        driver["status"] = "Available"
        passenger["ride_status"] = "Completed"
        driver["earnings"] += fare
        RIDE_STATS["completed_rides"] += 1
        RIDE_STATS["total_earnings"] += fare
        
        # Save ride to history
        ride_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "passenger": passenger["name"],
            "driver": driver["name"],
            "fare": fare,
            "status": "Completed"
        }
        rides = UserManager.load_rides()
        rides.append(ride_data)
        UserManager.save_rides(rides)
        
        self.log_ride_event(f"Ride completed! Fare: ${fare:.2f}")
        add_markers(self.map_widget)  # Refresh markers

    def animate_move(self, driver, start, end, steps=20, delay=0.1):
        lat1, lon1 = start
        lat2, lon2 = end
        
        for i in range(steps):
            # Calculate intermediate position
            progress = i / steps
            lat = lat1 + (lat2 - lat1) * progress
            lon = lon1 + (lon2 - lon1) * progress
            driver["lat"], driver["lon"] = lat, lon
            
            # Clear and redraw markers
            self.map_widget.delete_all_marker()
            self.map_widget.set_marker(lat, lon, text=f"{driver['name']} 🚗")
            self.map_widget.set_marker(lat2, lon2, text="Destination 🎯")
            
            # Update passenger being picked up
            passenger_marker = next((p for p in PASSENGERS if p["ride_status"] == "In Progress"), None)
            if passenger_marker:
                self.map_widget.set_marker(
                    passenger_marker["lat"], 
                    passenger_marker["lon"], 
                    text=f"{passenger_marker['name']} 🪴"
                )
            
            # Force UI update
            self.update()
            time.sleep(delay)

    def log_ride_event(self, message):
        self.ride_logs.append(message)
        self.ride_log_text.config(state="normal")
        self.ride_log_text.insert(tk.END, message + "\n")
        self.ride_log_text.see(tk.END)
        self.ride_log_text.config(state="disabled")
        print("Ride Event:", message)  # Debug output

    def update_stats(self):
        avg_wait = RIDE_STATS["total_wait_time"] / RIDE_STATS["completed_rides"] if RIDE_STATS["completed_rides"] > 0 else 0
        self.stats_label.config(
            text=f"Total Rides: {RIDE_STATS['total_rides']}\n"
                 f"Completed: {RIDE_STATS['completed_rides']}\n"
                 f"Avg Wait: {avg_wait:.1f}s\n"
                 f"Total Earnings: ${RIDE_STATS['total_earnings']:.2f}"
        )
        self.after(3000, self.update_stats)

    def update_status(self):
        # Update passenger status
        self.passenger_status_text.config(state="normal")
        self.passenger_status_text.delete("1.0", tk.END)
        for p in PASSENGERS:
            self.passenger_status_text.insert(tk.END, f"{p['name']} ({p['rating']}★): {p['ride_status']}\n")
        self.passenger_status_text.config(state="disabled")
        
        # Update driver status
        self.driver_status_text.config(state="normal")
        self.driver_status_text.delete("1.0", tk.END)
        for d in DRIVERS:
            self.driver_status_text.insert(tk.END, f"{d['name']} ({d['rating']}★): {d['status']}\nEarnings: ${d['earnings']:.2f}\n")
        self.driver_status_text.config(state="disabled")
        
        self.after(2000, self.update_status)
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.map_widget = TkinterMapView(self, width=800, height=600, corner_radius=0)
        self.map_widget.set_position(40.730610, -73.935242)
        self.map_widget.set_zoom(12)
        self.map_widget.pack(side="left", fill="both", expand=True)
        
        self.side_panel = tk.Frame(self)
        self.side_panel.pack(side="right", fill="y", padx=10)
        
        tk.Label(self.side_panel, text="Uber Simulation", font=("Arial", 16)).pack(pady=10)
        
        self.info_label = tk.Label(self.side_panel, text="", font=("Arial", 12))
        self.info_label.pack(pady=5)
        
        self.stats_label = tk.Label(self.side_panel, text="", font=("Arial", 12))
        self.stats_label.pack(pady=5)
        
        tk.Label(self.side_panel, text="Passenger Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.passenger_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.passenger_status_text.pack(pady=5)
        
        tk.Label(self.side_panel, text="Driver Status", font=("Arial", 14, "bold")).pack(pady=5)
        self.driver_status_text = tk.Text(self.side_panel, height=10, width=30, state="disabled")
        self.driver_status_text.pack(pady=5)
        
        tk.Button(self.side_panel, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=10)
        
        add_markers(self.map_widget)
        self.update_stats()
        self.update_status()
    
    def update_stats(self):
        avg_wait = RIDE_STATS["total_wait_time"] / RIDE_STATS["completed_rides"] if RIDE_STATS["completed_rides"] > 0 else 0
        self.stats_label.config(
            text=f"Total Rides: {RIDE_STATS['total_rides']}\n"
                 f"Completed: {RIDE_STATS['completed_rides']}\n"
                 f"Avg Wait: {avg_wait:.1f}s\n"
                 f"Total Earnings: ${RIDE_STATS['total_earnings']:.2f}"
        )
        self.after(3000, self.update_stats)
    
    def update_status(self):
        self.passenger_status_text.config(state="normal")
        self.passenger_status_text.delete("1.0", tk.END)
        for p in PASSENGERS:
            self.passenger_status_text.insert(tk.END, f"{p['name']} ({p['rating']}★): {p['ride_status']}\n")
        self.passenger_status_text.config(state="disabled")
        
        self.driver_status_text.config(state="normal")
        self.driver_status_text.delete("1.0", tk.END)
        for d in DRIVERS:
            self.driver_status_text.insert(tk.END, f"{d['name']} ({d['rating']}★): {d['status']}\nEarnings: ${d['earnings']:.2f}\n")
        self.driver_status_text.config(state="disabled")
        
        self.after(2000, self.update_status)
    
class BookingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Book a Ride", font=("Arial", 24)).pack(pady=10)
        
        tk.Label(self, text="Ride Type:").pack()
        self.ride_type = tk.StringVar(value="UberX")
        tk.Radiobutton(self, text="UberX", variable=self.ride_type, value="UberX").pack()
        tk.Radiobutton(self, text="UberBlack", variable=self.ride_type, value="UberBlack").pack()
        tk.Radiobutton(self, text="UberXL", variable=self.ride_type, value="UberXL").pack()
        
        tk.Label(self, text="Pickup Location:").pack()
        self.pickup_var = tk.StringVar()
        self.pickup_dropdown = ttk.Combobox(self, textvariable=self.pickup_var)
        self.pickup_dropdown['values'] = [p["name"] for p in PASSENGERS]
        self.pickup_dropdown.current(0)
        self.pickup_dropdown.pack()
        
        tk.Label(self, text="Destination (lat, lon):").pack()
        self.dest_entry = tk.Entry(self)
        self.dest_entry.insert(0, "40.735, -74.002")
        self.dest_entry.pack()
        
        self.estimate_btn = tk.Button(self, text="Get Estimate", command=self.get_estimate)
        self.estimate_btn.pack(pady=5)
        
        self.estimate_label = tk.Label(self, text="", font=("Arial", 12))
        self.estimate_label.pack()
        
        self.book_btn = tk.Button(self, text="Confirm Booking", command=self.book_ride, state="disabled")
        self.book_btn.pack(pady=10)
        
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack()
    
    def get_estimate(self):
        passenger_name = self.pickup_var.get()
        passenger = next((p for p in PASSENGERS if p["name"] == passenger_name), None)
        
        try:
            dest_lat, dest_lon = map(float, self.dest_entry.get().split(","))
        except ValueError:
            messagebox.showerror("Error", "Invalid destination coordinates")
            return
        
        distance = calculate_distance(passenger["lat"], passenger["lon"], dest_lat, dest_lon)
        distance_km = distance * 111  # approx km per degree
        est_time = distance_km * 2  # approx minutes (2 min per km)
        fare = calculate_fare(distance_km, est_time, self.ride_type.get())
        
        self.estimate_label.config(
            text=f"Distance: {distance_km:.1f} km\n"
                 f"Est. Time: {est_time:.0f} min\n"
                 f"Est. Fare: ${fare:.2f}"
        )
        self.book_btn.config(state="normal")
        self.current_fare = fare
    
    def book_ride(self):
        passenger_name = self.pickup_var.get()
        passenger = next((p for p in PASSENGERS if p["name"] == passenger_name), None)
        
        try:
            dest_lat, dest_lon = map(float, self.dest_entry.get().split(","))
        except ValueError:
            messagebox.showerror("Error", "Invalid destination coordinates")
            return
        
        main_page = self.controller.frames["MainPage"]
        main_page.simulate_ride(passenger_name, (dest_lat, dest_lon), self.ride_type.get(), self.current_fare)
        self.controller.show_page("MainPage")

class RideHistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Ride History", font=("Arial", 24)).pack(pady=10)
        
        self.history_text = tk.Text(self, height=20, width=80, state="disabled")
        self.history_text.pack(pady=10, padx=10)
        
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack()
        
        self.update_history()
    
    def update_history(self):
        rides = UserManager.load_rides()
        user_rides = [r for r in rides if r["passenger"] == self.controller.current_user or r["driver"] == self.controller.current_user]
        
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)
        
        if not user_rides:
            self.history_text.insert(tk.END, "No ride history found")
        else:
            for ride in user_rides:
                self.history_text.insert(tk.END, 
                    f"Date: {ride['date']}\n"
                    f"Passenger: {ride['passenger']}\n"
                    f"Driver: {ride['driver']}\n"
                    f"Fare: ${ride['fare']:.2f}\n"
                    f"Rating: {ride.get('rating', 'Not rated')}\n"
                    f"Status: {ride['status']}\n"
                    "------------------------\n"
                )
        
        self.history_text.config(state="disabled")

class AccountPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        if not hasattr(controller, 'current_user') or not controller.current_user:
            tk.Label(self, text="Please login first", font=("Arial", 24)).pack(pady=20)
            tk.Button(self, text="Go to Login", command=lambda: controller.show_page("LoginPage")).pack(pady=10)
            return
        
        self.user_type = "passenger" if controller.current_user in [p["name"] for p in PASSENGERS] else "driver"
        
        tk.Label(self, text=f"Username: {controller.current_user}").pack()
        tk.Label(self, text=f"User Type: {self.user_type.capitalize()}").pack()
        
        if self.user_type == "passenger":
            passenger = next((p for p in PASSENGERS if p["name"] == controller.current_user), None)
            tk.Label(self, text=f"Rating: {passenger['rating']}").pack()
        else:
            driver = next((d for d in DRIVERS if d["name"] == controller.current_user), None)
            tk.Label(self, text=f"Rating: {driver['rating']}").pack()
            tk.Label(self, text=f"Total Earnings: ${driver['earnings']:.2f}").pack()
        
        tk.Button(self, text="Change Password", command=self.change_password).pack(pady=10)
        tk.Button(self, text="Delete Account", command=self.delete_account).pack(pady=10)
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack()
    
    def change_password(self):
        new_password = tk.simpledialog.askstring("Change Password", "Enter new password:", show="*")
        if new_password:
            users = UserManager.load_users()
            if self.user_type == "passenger":
                users["passengers"][self.controller.current_user]["password"] = new_password
            else:
                users["drivers"][self.controller.current_user]["password"] = new_password
            UserManager.save_users(users)
            messagebox.showinfo("Success", "Password changed successfully")
    
    def delete_account(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete your account?"):
            users = UserManager.load_users()
            if self.user_type == "passenger":
                del users["passengers"][self.controller.current_user]
                PASSENGERS[:] = [p for p in PASSENGERS if p["name"] != self.controller.current_user]
            else:
                del users["drivers"][self.controller.current_user]
                DRIVERS[:] = [d for d in DRIVERS if d["name"] != self.controller.current_user]
            
            UserManager.save_users(users)
            messagebox.showinfo("Success", "Account deleted successfully")
            self.controller.current_user = None
            self.controller.show_page("LoginPage")

class AdminDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="Admin Dashboard", font=("Arial", 24)).pack(pady=20)
        
        # Stats frame
        stats_frame = tk.Frame(self)
        stats_frame.pack(pady=10)
        
        self.total_rides_label = tk.Label(stats_frame, text="Total Rides: 0", font=("Arial", 12))
        self.total_rides_label.grid(row=0, column=0, padx=10)
        
        self.completed_rides_label = tk.Label(stats_frame, text="Completed Rides: 0", font=("Arial", 12))
        self.completed_rides_label.grid(row=0, column=1, padx=10)
        
        self.total_earnings_label = tk.Label(stats_frame, text="Total Earnings: $0.00", font=("Arial", 12))
        self.total_earnings_label.grid(row=0, column=2, padx=10)
        
        # User management
        user_frame = tk.LabelFrame(self, text="User Management", padx=10, pady=10)
        user_frame.pack(pady=10, fill="x")
        
        tk.Label(user_frame, text="Passengers:").grid(row=0, column=0)
        self.passenger_list = tk.Listbox(user_frame, height=5)
        self.passenger_list.grid(row=1, column=0, padx=5)
        
        tk.Label(user_frame, text="Drivers:").grid(row=0, column=1)
        self.driver_list = tk.Listbox(user_frame, height=5)
        self.driver_list.grid(row=1, column=1, padx=5)
        
        self.update_lists()
        
        tk.Button(self, text="Refresh", command=self.update_stats).pack(pady=5)
        tk.Button(self, text="Back to Menu", command=lambda: controller.show_page("MenuPage")).pack(pady=10)
        
        self.update_stats()
    
    def update_lists(self):
        self.passenger_list.delete(0, tk.END)
        for p in PASSENGERS:
            self.passenger_list.insert(tk.END, f"{p['name']} ({p['rating']}★)")
        
        self.driver_list.delete(0, tk.END)
        for d in DRIVERS:
            self.driver_list.insert(tk.END, f"{d['name']} ({d['rating']}★) - ${d['earnings']:.2f}")
    
    def update_stats(self):
        rides = UserManager.load_rides()
        completed = len([r for r in rides if r["status"] == "Completed"])
        earnings = sum(float(r["fare"]) for r in rides if r["status"] == "Completed")
        
        self.total_rides_label.config(text=f"Total Rides: {len(rides)}")
        self.completed_rides_label.config(text=f"Completed Rides: {completed}")
        self.total_earnings_label.config(text=f"Total Earnings: ${earnings:.2f}")
        
        self.update_lists()
        self.after(5000, self.update_stats)
class UberSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Uber Simulation")
        self.geometry("1200x800")
        self.current_user = None  # Initialize current_user as None
        
        # Create container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        # Create all pages
        for F in (LoginPage, RegisterPage, MenuPage, DriverDashboard, 
                 MainPage, BookingPage, RideHistoryPage, AccountPage, AdminDashboard):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_page("LoginPage")
    
    def show_page(self, page_name):
        protected_pages = ["MenuPage", "DriverDashboard", "AccountPage", "BookingPage", "RideHistoryPage"]
        if page_name in protected_pages and not hasattr(self, 'current_user'):
            self.show_page("LoginPage")
            return
        
        frame = self.frames.get(page_name)
        if frame:
            frame.tkraise()

if __name__ == "__main__":
    app = UberSimulationApp()
    app.mainloop()