import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import time
import threading

class BitStuffingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bit Stuffing & Unstuffing Tool with CRC")
        self.root.geometry("850x700")

        self.input_frame = ttk.LabelFrame(root, text="Input")
        self.input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.input_frame, text="Enter Binary Data (0s and 1s only):").pack(side="left", padx=5, pady=5)
        self.input_entry = ttk.Entry(self.input_frame, width=40)
        self.input_entry.pack(side="left", padx=5, pady=5)

        # New control for custom bit stuffing rule
        ttk.Label(self.input_frame, text="Stuff after").pack(side="left", padx=2)
        self.stuff_count = ttk.Spinbox(self.input_frame, from_=1, to=10, width=2)
        self.stuff_count.set(5)  # Default value
        self.stuff_count.pack(side="left")
        ttk.Label(self.input_frame, text="consecutive 1's").pack(side="left", padx=2)

        ttk.Label(self.input_frame, text="Integrity Check: CRC").pack(side="left", padx=10)

        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=5)

        self.stuffing_button = ttk.Button(self.button_frame, text="Perform Bit Stuffing", command=self.perform_stuffing)
        self.stuffing_button.pack(side="left", padx=5)

        self.unstuffing_button = ttk.Button(self.button_frame, text="Perform Bit Unstuffing", command=self.perform_unstuffing)
        self.unstuffing_button.pack(side="left", padx=5)

        # New simulate button
        self.simulate_button = ttk.Button(self.button_frame, text="Run Simulation", command=self.run_simulation)
        self.simulate_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="Clear All", command=self.clear_all)
        self.clear_button.pack(side="left", padx=5)

        # Simulation speed control
        speed_frame = ttk.Frame(root)
        speed_frame.pack(pady=2)
        ttk.Label(speed_frame, text="Simulation Speed:").pack(side="left", padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_scale = ttk.Scale(speed_frame, from_=0.1, to=3.0, orient="horizontal", 
                                     variable=self.speed_var, length=200)
        self.speed_scale.pack(side="left", padx=5)
        ttk.Label(speed_frame, textvariable=self.speed_var).pack(side="left")

        # Network visualization frame
        self.network_frame = ttk.LabelFrame(root, text="Network Simulation")
        self.network_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create canvas for network visualization
        self.network_canvas = tk.Canvas(self.network_frame, bg="white", height=150)
        self.network_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Draw network components
        self.draw_network_components()

        # Status message
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.network_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)

        self.graph_frame = ttk.LabelFrame(root, text="Bit Transmission Visualization")
        self.graph_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(6, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.output_frame = ttk.LabelFrame(root, text="Output")
        self.output_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.output_frame, text="Stuffed Data (with CRC):").pack(anchor="w", padx=5)
        self.stuffed_data_entry = ttk.Entry(self.output_frame, width=50)
        self.stuffed_data_entry.pack(fill="x", padx=5, pady=2)

        ttk.Label(self.output_frame, text="Unstuffed Data:").pack(anchor="w", padx=5)
        self.unstuffed_data_entry = ttk.Entry(self.output_frame, width=50)
        self.unstuffed_data_entry.pack(fill="x", padx=5, pady=2)

        self.animation = None
        self.data_sequence = []
        self.current_stuff_count = 5  # Default value
        
        # Network simulation variables
        self.simulation_running = False
        self.data_packets = []
        self.simulation_thread = None

    def draw_network_components(self):
        # Draw sender
        self.sender = self.network_canvas.create_rectangle(50, 50, 150, 100, fill="lightblue")
        self.network_canvas.create_text(100, 75, text="Sender\n(Bit Stuffing)")
        
        # Draw channel
        self.channel = self.network_canvas.create_rectangle(200, 60, 600, 90, fill="lightgray")
        self.network_canvas.create_text(400, 75, text="Transmission Channel")
        
        # Draw receiver
        self.receiver = self.network_canvas.create_rectangle(650, 50, 750, 100, fill="lightgreen")
        self.network_canvas.create_text(700, 75, text="Receiver\n(Bit Unstuffing)")
        
        # Draw arrows
        self.network_canvas.create_line(150, 75, 200, 75, arrow=tk.LAST)
        self.network_canvas.create_line(600, 75, 650, 75, arrow=tk.LAST)
        
        # Create data packet objects (initially invisible)
        self.data_packets = []

    def bit_stuff(self, data, max_ones=5):
        stuffed = ""
        count = 0
        for bit in data:
            stuffed += bit
            if bit == '1':
                count += 1
                if count == max_ones:
                    stuffed += '0'
                    count = 0
            else:
                count = 0
        return stuffed

    def bit_unstuff(self, data, max_ones=5):
        unstuffed = ""
        count = 0
        i = 0
        while i < len(data):
            unstuffed += data[i]
            if data[i] == '1':
                count += 1
                if count == max_ones and i + 1 < len(data) and data[i + 1] == '0':
                    i += 1
                    count = 0
            else:
                count = 0
            i += 1
        return unstuffed

    def calculate_crc(self, data, divisor='1101'):
        data = data + '0' * (len(divisor) - 1)
        data = list(data)
        divisor = list(divisor)
        for i in range(len(data) - len(divisor) + 1):
            if data[i] == '1':
                for j in range(len(divisor)):
                    data[i + j] = str(int(data[i + j] != divisor[j]))
        return ''.join(data[-(len(divisor)-1):])

    def verify_crc(self, data, divisor='1101'):
        data = list(data)
        divisor = list(divisor)
        for i in range(len(data) - len(divisor) + 1):
            if data[i] == '1':
                for j in range(len(divisor)):
                    data[i + j] = str(int(data[i + j] != divisor[j]))
        return all(bit == '0' for bit in data[-(len(divisor)-1):])

    def perform_stuffing(self):
        input_data = self.input_entry.get().strip()
        
        if not set(input_data).issubset({'0', '1'}) or not input_data:
            self.stuffed_data_entry.delete(0, tk.END)
            self.stuffed_data_entry.insert(0, "Invalid Input! Only 0s and 1s allowed.")
            return
        
        try:
            self.current_stuff_count = int(self.stuff_count.get())
            if self.current_stuff_count < 1:
                raise ValueError("Count must be at least 1")
        except ValueError:
            self.stuffed_data_entry.delete(0, tk.END)
            self.stuffed_data_entry.insert(0, "Invalid stuff count! Please enter a positive integer.")
            return

        crc = self.calculate_crc(input_data)
        full_data = input_data + crc
        stuffed_data = self.bit_stuff(full_data, self.current_stuff_count)

        self.stuffed_data_entry.delete(0, tk.END)
        self.stuffed_data_entry.insert(0, stuffed_data)

        self.data_sequence = [int(bit) for bit in stuffed_data]
        self.animate_graph()

    def perform_unstuffing(self):
        stuffed_data = self.stuffed_data_entry.get().strip()

        if not stuffed_data or any(bit not in '01' for bit in stuffed_data):
            self.unstuffed_data_entry.delete(0, tk.END)
            self.unstuffed_data_entry.insert(0, "Invalid Input! Only 0s and 1s allowed.")
            return
        
        try:
            self.current_stuff_count = int(self.stuff_count.get())
            if self.current_stuff_count < 1:
                raise ValueError("Count must be at least 1")
        except ValueError:
            self.unstuffed_data_entry.delete(0, tk.END)
            self.unstuffed_data_entry.insert(0, "Invalid stuff count! Please enter a positive integer.")
            return

        unstuffed_data = self.bit_unstuff(stuffed_data, self.current_stuff_count)
        original_data = unstuffed_data[:-3]  # Remove CRC
        is_valid = self.verify_crc(unstuffed_data)

        result = f"{original_data} (Valid CRC)" if is_valid else f"{original_data} (CRC Error Detected)"
        self.unstuffed_data_entry.delete(0, tk.END)
        self.unstuffed_data_entry.insert(0, result)

        self.data_sequence = [int(bit) for bit in unstuffed_data]
        self.animate_graph()

    def run_simulation(self):
        if self.simulation_running:
            return
            
        input_data = self.input_entry.get().strip()
        
        if not set(input_data).issubset({'0', '1'}) or not input_data:
            self.status_var.set("Invalid input data! Only 0s and 1s allowed.")
            return
            
        try:
            self.current_stuff_count = int(self.stuff_count.get())
            if self.current_stuff_count < 1:
                raise ValueError("Count must be at least 1")
        except ValueError:
            self.status_var.set("Invalid stuff count! Please enter a positive integer.")
            return
            
        # Clear previous simulation
        for packet in self.data_packets:
            self.network_canvas.delete(packet)
        self.data_packets = []
        
        # Start simulation in a separate thread
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self.simulation_thread_func)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def simulation_thread_func(self):
        try:
            # Get input data
            input_data = self.input_entry.get().strip()
            
            # Step 1: Calculate CRC
            self.status_var.set("Step 1: Calculating CRC...")
            time.sleep(1.0 / self.speed_var.get())
            
            crc = self.calculate_crc(input_data)
            full_data = input_data + crc
            
            self.status_var.set(f"Step 1: Added CRC {crc} to data")
            time.sleep(1.0 / self.speed_var.get())
            
            # Step 2: Perform bit stuffing
            self.status_var.set(f"Step 2: Performing bit stuffing (after {self.current_stuff_count} consecutive 1's)...")
            time.sleep(1.0 / self.speed_var.get())
            
            stuffed_data = self.bit_stuff(full_data, self.current_stuff_count)
            
            # Update UI
            self.root.after(0, lambda: self.stuffed_data_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.stuffed_data_entry.insert(0, stuffed_data))
            
            self.status_var.set(f"Step 2: Bit stuffing complete")
            time.sleep(1.0 / self.speed_var.get())
            
            # Step 3: Transmit data through channel
            self.status_var.set("Step 3: Transmitting data through channel...")
            
            # Animate packets moving through channel
            self.transmit_data(stuffed_data)
            
            # Step 4: Perform bit unstuffing
            self.status_var.set("Step 4: Performing bit unstuffing...")
            time.sleep(1.0 / self.speed_var.get())
            
            unstuffed_data = self.bit_unstuff(stuffed_data, self.current_stuff_count)
            
            # Step 5: Verify CRC
            self.status_var.set("Step 5: Verifying CRC...")
            time.sleep(1.0 / self.speed_var.get())
            
            is_valid = self.verify_crc(unstuffed_data)
            original_data = unstuffed_data[:-3]  # Remove CRC
            
            result = f"{original_data} (Valid CRC)" if is_valid else f"{original_data} (CRC Error Detected)"
            self.root.after(0, lambda: self.unstuffed_data_entry.delete(0, tk.END))
            self.root.after(0, lambda: self.unstuffed_data_entry.insert(0, result))
            
            if is_valid:
                self.status_var.set("Simulation complete: Data received successfully with valid CRC")
            else:
                self.status_var.set("Simulation complete: Error detected in received data")
                
            # Update graph animation
            self.data_sequence = [int(bit) for bit in stuffed_data]
            self.root.after(0, self.animate_graph)
                
        finally:
            self.simulation_running = False
            
    def transmit_data(self, data):
        # Create visual representation of data packets
        packet_size = 4  # Number of bits per packet for visualization
        packet_chunks = [data[i:i+packet_size] for i in range(0, len(data), packet_size)]
        
        # Starting positions
        start_x = 160
        start_y = 75
        end_x = 640
        
        for i, chunk in enumerate(packet_chunks):
            # Create a packet
            packet_color = "red" if '1' in chunk else "blue"
            packet = self.network_canvas.create_oval(start_x-10, start_y-10, start_x+10, start_y+10, 
                                                    fill=packet_color, outline="black")
            self.data_packets.append(packet)
            
            # Animate packet movement
            steps = 30
            dx = (end_x - start_x) / steps
            
            for step in range(steps + 1):
                if not self.simulation_running:
                    return
                    
                x = start_x + dx * step
                self.network_canvas.coords(packet, x-10, start_y-10, x+10, start_y+10)
                self.network_canvas.update()
                time.sleep(0.03 / self.speed_var.get())
                
            # Pause briefly between packets
            time.sleep(0.1 / self.speed_var.get())

    def clear_all(self):
        # Stop any running simulation
        self.simulation_running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=0.5)
            
        # Clear UI fields
        self.input_entry.delete(0, tk.END)
        self.stuffed_data_entry.delete(0, tk.END)
        self.unstuffed_data_entry.delete(0, tk.END)
        
        # Clear network visualization
        for packet in self.data_packets:
            self.network_canvas.delete(packet)
        self.data_packets = []
        
        # Clear graph
        self.ax.clear()
        self.ax.set_title("Bit Transmission Over Time (Square Wave)")
        self.canvas.draw()
        self.data_sequence = []
        
        # Reset status
        self.status_var.set("Ready")

    def animate_graph(self):
        if self.animation is not None:
            try:
                self.animation.event_source.stop()
            except AttributeError:
                pass

        self.ax.clear()
        self.ax.set_title("Bit Transmission Over Time (Square Wave)")
        self.ax.set_xlabel("Bit Position")
        self.ax.set_ylabel("Bit Value")
        self.ax.set_ylim(-0.5, 1.5)
        self.ax.grid(True, linestyle="--", alpha=0.6)

        self.time_steps = np.arange(len(self.data_sequence))
        self.bit_values = np.array(self.data_sequence)

        self.animation = animation.FuncAnimation(
            self.fig, self.update_graph, frames=len(self.time_steps),
            interval=500, repeat=False
        )

        self.canvas.draw()

    def update_graph(self, i):
        if i > 0:
            self.ax.clear()
            self.ax.step(self.time_steps[:i+1], self.bit_values[:i+1], where="post", color="blue", linewidth=2)
            self.ax.set_title("Bit Transmission Over Time (Square Wave)")
            self.ax.set_xlabel("Bit Position")
            self.ax.set_ylabel("Bit Value")
            self.ax.set_ylim(-0.5, 1.5)
            self.ax.grid(True, linestyle="--", alpha=0.6)

            for x in self.time_steps[:i+1]:
                self.ax.axvline(x, color="gray", linestyle="dotted", alpha=0.5)

            for x, y in zip(self.time_steps[:i+1], self.bit_values[:i+1]):
                self.ax.text(x, y + 0.1, str(y), ha="center", fontsize=10, color="red")

            self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = BitStuffingApp(root)
    root.mainloop()