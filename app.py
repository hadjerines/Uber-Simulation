import tkinter as tk
from ui import MenuPage, MainPage, BookingPage

class UberSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Uber Simulation")
        self.geometry("900x700")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        for Page in (MenuPage, MainPage, BookingPage):
            page_name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_page("MenuPage")

    def show_page(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def calculate_surge(driver_count, request_count):
        ratio = request_count / max(1, driver_count)
        return min(3.0, max(1.0, 1.0 + (ratio - 1) * 0.5))  # Caps at 3x

if __name__ == "__main__":
    app = UberSimulationApp()
    app.mainloop()
