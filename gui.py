import customtkinter as ctk
import tkinter as tk
import math
import time
import os
import psutil
import cv2
import threading
from PIL import Image, ImageTk
from datetime import datetime

class A9HUD(ctk.CTk):
    def __init__(self, callback_func):
        super().__init__()
        self.callback_func = callback_func
        
        self.title("A.9 HUD")
        self.geometry("1300x800")
        self.configure(fg_color="black")
        
        # Performance optimization
        self.attributes("-alpha", 0.98) 
        
        # HUD Colors (Vibrant JARVIS Blue)
        self.color_teal = "#00d2ff" # Vibrant electric blue
        self.color_teal_glow = "#005577" # Glow shade
        self.color_bg = "black"
        
        # State for smoothing
        self.energy_level = 0.0
        self.target_energy = 0.0
        self.rotation_angle = 0
        self.noise_offset = 0 # For uneven core animation
        
        self.status_text = "SYSTEM ONLINE"
        self.subtitle_text = "Awaiting command..."
        
        # Aesthetic Hacker Code (Randomized)
        self.hacker_code = [
            "0x88AF8 - BUFFER_INIT", 
            "LOAD_CORE_V2.01", 
            "MEM_SYNC_ACTIVE",
            "SCANNING_OS_SUBSYSTEM",
            "ENCRYPTION: AES-256",
            "SATELLITE_LINK_ESTABLISHED",
            "THREAT_LEVEL: ZERO",
            "VORTEX_CORE_SYNC: OK"
        ]
        
        # Camera Feed State
        self.cap = None
        self.cam_image = None
        self.last_raw_frame = None
        self.camera_running = False
        
        self._init_ui()
        self._draw_hud_static() # Initial static draw
        self._start_animations()
        self._update_system_data()
        
        # Auto-initialize core after 1 second
        self.after(1000, self.on_start)

    def _init_ui(self):
        # Create Main HUD Canvas
        self.canvas = tk.Canvas(
            self, 
            bg="black", 
            highlightthickness=0, 
            width=1300, 
            height=800
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Centering coordinates
        self.cx = 650
        self.cy = 350
        self.base_r = 150
        
        # Particle System for Core (Higher count for denser look)
        self.num_particles = 300 # Increased for rounder "organic" feel
        self.particles = []
        for i in range(self.num_particles):
            # Fibonacci Sphere algorithm for even distribution
            phi = math.acos(1 - 2 * (i + 0.5) / self.num_particles)
            theta = math.pi * (1 + 5**0.5) * (i + 0.5)
            self.particles.append([phi, theta])
            
        # Bind Resize Event
        self.bind("<Configure>", self._on_resize)
            
        # Start button (Hidden, used for auto-trigger)
        self.start_btn = None

    def _on_resize(self, event):
        # Update center points when window is resized
        self.cx = self.winfo_width() / 2
        self.cy = self.winfo_height() / 2
        # Dynamic base radius based on window size
        self.base_r = min(self.winfo_width(), self.winfo_height()) / 6
        # Redraw static only when resized
        self._draw_hud_static()

    def _draw_hud_static(self):
        self.canvas.delete("static")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 100: return # Skip if too small
        
        # Draw Technical Grid (Very subtle)
        grid_step = 100
        for x in range(0, w, grid_step):
            self.canvas.create_line(x, 0, x, h, fill="#001122", width=1, tags="static")
        for y in range(0, h, grid_step):
            self.canvas.create_line(0, y, w, y, fill="#001122", width=1, tags="static")
            
        # 1. Top Left - Chronometer
        now = datetime.now()
        date_str = now.strftime("%B %d").upper()
        time_str = now.strftime("%I:%M %p").upper()
        
        self.canvas.create_text(
            50, 50, text=now.strftime("%Y").upper(), fill=self.color_teal_glow,
            font=("Courier", 10), anchor="nw", tags="static"
        )
        self.canvas.create_text(
            50, 65, text=date_str, fill=self.color_teal, 
            font=("Courier", 28, "bold"), anchor="nw", tags="static"
        )
        self.canvas.create_text(
            50, 105, text=time_str, fill=self.color_teal, 
            font=("Courier", 16), anchor="nw", tags="static"
        )
        
        # 2. Left Panel - Resource Monitor
        self.canvas.create_line(50, 180, 250, 180, fill=self.color_teal, width=1, tags="static")
        self.canvas.create_text(50, 200, text="PRI: SYSTEM_STORAGE", fill=self.color_teal_glow, font=("Courier", 8), anchor="nw", tags="static")
        self.canvas.create_text(50, 220, text="FL: 886GB | FR: 66GB", fill=self.color_teal, font=("Courier", 10), anchor="nw", tags="static")
        
        # Power meter
        battery = psutil.sensors_battery()
        bat_percent = battery.percent if battery else 95
        self.canvas.create_oval(50, 300, 130, 380, outline=self.color_teal_glow, width=1, tags="static")
        self.canvas.create_text(90, 340, text=f"{bat_percent}%", fill=self.color_teal, font=("Courier", 14, "bold"), tags="static")
        self.canvas.create_text(90, 360, text="CORE_PWR", fill=self.color_teal_glow, font=("Courier", 6), tags="static")
        
        # Aesthetic "Random Code" Overlays
        for i, code in enumerate(self.hacker_code):
            self.canvas.create_text(
                50, h - 300 + (i*15), text=code, fill="#002233", 
                font=("Courier", 8), anchor="nw", tags="static"
            )
            
        for i, code in enumerate(reversed(self.hacker_code)):
            self.canvas.create_text(
                w - 200, 50 + (i*15), text=code, fill="#002233", 
                font=("Courier", 8), anchor="nw", tags="static"
            )

        # 3. Right Panels (Relative to Width)
        rx = w - 300
        self.canvas.create_line(rx, 400, w - 50, 400, fill=self.color_teal, width=1, tags="static")
        self.canvas.create_text(rx + 10, 410, text="DATA_NOTES", fill=self.color_teal, font=("Courier", 12, "bold"), anchor="nw", tags="static")
        
        tasks = ["- STARK EXPO BOARD MEET", "- RECHARGE CORE", "- PEPPER DINNER AT 8", "- CHECK MARK L"]
        for i, task in enumerate(tasks):
            self.canvas.create_text(rx + 15, 440 + (i*20), text=task, fill=self.color_teal, font=("Courier", 9), anchor="nw", tags="static")

        # 4. SIGHT FEED - Bottom Right
        self.canvas.create_line(rx, h - 300, w - 50, h - 300, fill=self.color_teal, width=1, tags="static")
        self.canvas.create_text(rx + 10, h - 290, text="SIGHT_FEED", fill=self.color_teal, font=("Courier", 12, "bold"), anchor="nw", tags="static")
        self.canvas.create_rectangle(rx + 10, h - 270, w - 50, h - 100, outline=self.color_teal_glow, width=1, tags="static")
        
        # Start the camera feed thread
        self.start_camera()

    def _draw_hud_dynamic(self):
        self.canvas.delete("dynamic")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 100 or h < 100: return
        
        # SMOOTHING Logic
        lerp_factor = 0.15 
        self.energy_level += (self.target_energy - self.energy_level) * lerp_factor
        
        # Update Noise for uneven core
        self.noise_offset += 0.04 # Slightly slower for smoother wobble
        
        # Convert rotation angle to radians
        rad = math.radians(self.rotation_angle)
        
        # Draw Secondary HUD Rings (Tech feel)
        ring_r = self.base_r * 1.5
        self.canvas.create_oval(
            self.cx - ring_r, self.cy - ring_r,
            self.cx + ring_r, self.cy + ring_r,
            outline="#001a2a", width=1, tags="dynamic"
        )
        
        # Project 3D points
        # Spin parallel to Y-axis means rotating theta. 
        for phi, theta in self.particles:
            rotated_theta = theta + rad
            
            # UNEVEN SHAPING: Refined to be uneven but circular/cloud-like, not square
            # Using multiple sine harmonics creates a "wobbly gas" look rather than hard edges
            noise = (
                0.06 * math.sin(phi * 4 + self.noise_offset) + 
                0.04 * math.cos(theta * 3 - self.noise_offset) + 
                0.02 * math.sin(phi * theta + self.noise_offset)
            )
            current_particle_r = self.base_r * (1 + self.energy_level * 0.5 + noise)
            
            # 3D Coordinates
            x = current_particle_r * math.sin(phi) * math.cos(rotated_theta)
            y = current_particle_r * math.sin(phi) * math.sin(rotated_theta)
            z = current_particle_r * math.cos(phi)
            
            px = self.cx + x
            py = self.cy + y
            depth_ratio = (z + current_particle_r) / (2 * current_particle_r)
            
            if depth_ratio > 0.8:
                col = "white"; size = 2
            elif depth_ratio > 0.5:
                col = self.color_teal; size = 2
            else:
                col = self.color_teal_glow; size = 1
                
            self.canvas.create_oval(
                px - size, py - size, px + size, py + size, 
                fill=col, outline="", tags="dynamic"
            )
            
        # Status Readout
        self.canvas.create_text(
            self.cx, self.cy - (self.base_r + 80), text=self.status_text, 
            fill=self.color_teal, font=("Courier", 12, "bold"), tags="dynamic"
        )
        
        # 5. Bottom Subtitle
        sub_w = min(1000, w - 100)
        self.canvas.create_rectangle(
            (w - sub_w)/2, h - 80, (w + sub_w)/2, h - 30, 
            fill="#050505", outline="#003344", tags="dynamic" 
        )
        self.canvas.create_text(
            w/2, h - 55, text=self.subtitle_text, fill="white", 
            font=("Courier", 12), width=sub_w - 40, tags="dynamic"
        )
        
        # Draw Camera Frame (Thread-safe conversion)
        if hasattr(self, 'last_raw_frame') and self.last_raw_frame is not None:
            try:
                frame_rgb = cv2.cvtColor(self.last_raw_frame, cv2.COLOR_BGR2RGB)
                frame_small = cv2.resize(frame_rgb, (240, 170))
                img = Image.fromarray(frame_small)
                self.cam_image = ImageTk.PhotoImage(image=img)
                
                self.canvas.create_image(
                    self.winfo_width() - 175, 
                    self.winfo_height() - 185, 
                    image=self.cam_image, 
                    tags="dynamic"
                )
            except Exception as e:
                print(f"Cam display error: {e}")

    def _start_animations(self):
        def animate():
            self.rotation_angle = (self.rotation_angle + 2) % 360
            self._draw_hud_dynamic()
            # Static HUD is now only redrawn on resize (massive FPS gain)
            self.after(30, animate) # ~33 FPS
            
        animate()

    def _update_system_data(self):
        def update_loop():
            # Update system stats every 5 seconds
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                self.set_status(f"CPU: {cpu}% | RAM: {ram}%")
            except: pass
            self.after(5000, update_loop)
        
        update_loop()

    def start_camera(self):
        self.camera_running = True
        self.cap = cv2.VideoCapture(0)
        self.cam_thread = threading.Thread(target=self._update_camera, daemon=True)
        self.cam_thread.start()

    def _update_camera(self):
        while self.camera_running:
            if self.cap and self.cap.isOpened():
                try:
                    ret, frame = self.cap.read()
                    if ret:
                        self.last_raw_frame = frame
                except: pass
            time.sleep(0.04)

    def stop_camera(self):
        self.camera_running = False
        if self.cap:
            self.cap.release()

    def set_status(self, text):
        self.status_text = text.upper()

    def add_message(self, role, message):
        # For the HUD, we show the latest message as a "Subtitle"
        self.subtitle_text = f"[{role.upper()}]: {message}"

    def update_energy(self, level):
        """Update energy level (0.0 to 1.0) for orb pulsing."""
        self.target_energy = level

    def on_start(self):
        if self.start_btn:
            self.start_btn.destroy()
        self.callback_func(self)
        
    def start_gui(self):
        self.mainloop()

# Compatibility class for main.py integration
class A9GUI(A9HUD):
    pass
