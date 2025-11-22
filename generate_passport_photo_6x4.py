import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw

# Define a reasonable maximum size for display in pixels
MAX_DISPLAY_WIDTH = 800
MAX_DISPLAY_HEIGHT = 600

# --- Constants for Final Saved Image ---
TARGET_WIDTH_INCH = 6
TARGET_HEIGHT_INCH = 4
TARGET_PPI = 300 
# -------------------------------------------

class ImageApp:
    def __init__(self, master):
        # --- Core Setup ---
        self.master = master
        master.title("Image Selector and Replicator")
        
        self.image = None           # PIL Image object (Original, unscaled image)
        self.display_image_scaled = None # PIL Image object (Scaled version for display)
        self.photo = None           # Tkinter PhotoImage object for display
        self.canvas = None
        self.rect_id = None         # ID of the selection rectangle
        self.image_path = None
        self.scale_factor = 1.0     # Store the scaling factor (1.0 means no scaling)

        # --- Drag State Variables ---
        self._drag_data = {"x": 0, "y": 0} # Stores the mouse's starting position
        
        # --- GUI Structure ---
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # 1. Open Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        ttk.Button(button_frame, text="Open Image (JPEG)", command=self.open_image).pack(pady=5)
        
        # 2. Canvas Frame (Fixed size for display)
        self.canvas_frame = ttk.Frame(main_frame, relief="sunken", borderwidth=1, 
                                     width=MAX_DISPLAY_WIDTH, height=MAX_DISPLAY_HEIGHT)
        self.canvas_frame.pack(fill='both', expand=True, pady=10)
        self.canvas_frame.pack_propagate(False)
        
        # 3. Information Bar
        self.info_frame = ttk.LabelFrame(main_frame, text="Image Information", padding="5")
        self.info_frame.pack(fill='x', pady=5)
        self.info_label = ttk.Label(self.info_frame, text="No image loaded.")
        self.info_label.pack(fill='x')
        
        # 4. Selection Input and Action Frame (Bottom)
        self.control_frame = ttk.LabelFrame(main_frame, text="Selection and Action (in Original Pixels)", padding="10")
        self.control_frame.pack(fill='x', pady=10)
        
        # --- Selection Inputs ---
        self.x_var = tk.StringVar(value="0")
        self.y_var = tk.StringVar(value="0")
        self.size_var = tk.StringVar(value="100")
        
        input_frame = ttk.Frame(self.control_frame)
        input_frame.pack(fill='x')
        
        # X/Y Input
        ttk.Label(input_frame, text="Top-Left X:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        ttk.Entry(input_frame, textvariable=self.x_var, width=8).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(input_frame, text="Top-Left Y:").grid(row=0, column=2, padx=5, pady=2, sticky='w')
        ttk.Entry(input_frame, textvariable=self.y_var, width=8).grid(row=0, column=3, padx=5, pady=2)
        
        # Size Input
        ttk.Label(input_frame, text="Square Size:").grid(row=0, column=4, padx=5, pady=2, sticky='w')
        ttk.Entry(input_frame, textvariable=self.size_var, width=8).grid(row=0, column=5, padx=5, pady=2)
        
        # Buttons
        ttk.Button(self.control_frame, text="Show Selection", command=self.show_selection).pack(pady=5, side='left', padx=10)
        
        save_button_text = f"Accept, Replicate, & Save ({TARGET_WIDTH_INCH}x{TARGET_HEIGHT_INCH} in)"
        ttk.Button(self.control_frame, text=save_button_text, command=self.save_replicated_image).pack(pady=5, side='right', padx=10)
        
        self.set_controls_state('disabled')

    def set_controls_state(self, state):
        """Enables or disables the selection/action controls."""
        for child in self.control_frame.winfo_children():
            if child.winfo_class() not in ('TLabel', 'TFrame'):
                child.configure(state=state)

    def open_image(self):
        """Loads the image, calculates scaling, and updates the GUI."""
        f_types = [('JPEG files', '*.jpg'), ('JPEG files', '*.jpeg')]
        self.image_path = filedialog.askopenfilename(filetypes=f_types)
        
        if not self.image_path:
            return

        try:
            self.image = Image.open(self.image_path)
            self.display_image_scaled, self.scale_factor = self.prepare_display_image(self.image)
            
            self.display_image()
            self.update_info_bar()
            self.set_controls_state('normal')

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")
            self.image = None
            self.set_controls_state('disabled')
            
    def prepare_display_image(self, img):
        """Calculates the scaling factor to fit the image within MAX dimensions."""
        width, height = img.size
        scale_w = MAX_DISPLAY_WIDTH / width
        scale_h = MAX_DISPLAY_HEIGHT / height
        scale_factor = min(1.0, scale_w, scale_h) 
        
        if scale_factor < 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            scaled_img = img.resize((new_width, new_height), Image.LANCZOS)
        else:
            scaled_img = img.copy() 
            
        return scaled_img, scale_factor

    def display_image(self):
        """Displays the SCALED image on the canvas, and binds mouse events."""
        if self.canvas:
            self.canvas.destroy()
            
        if not self.display_image_scaled:
            return

        self.photo = ImageTk.PhotoImage(self.display_image_scaled)
        
        self.canvas = tk.Canvas(self.canvas_frame, 
                                width=self.photo.width(), 
                                height=self.photo.height())
        self.canvas.pack()
        self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        self.rect_id = None
        
        # Center lines are now drawn in show_selection()

    def update_info_bar(self):
        # ... (same as before)
        if not self.image:
            self.info_label.config(text="No image loaded.")
            return

        width_px, height_px = self.image.size
        ppi_x = self.image.info.get('dpi', (0, 0))[0] or 72
        ppi_y = self.image.info.get('dpi', (0, 0))[1] or 72
        
        width_in = width_px / ppi_x
        height_in = height_px / ppi_y
        
        info_text = (
            f"Resolution: **{width_px} x {height_px} px** (Original) | "
            f"Size: {width_in:.2f} x {height_in:.2f} inches | "
            f"PPI: {ppi_x} x {ppi_y} | "
            f"**Scale Factor: {self.scale_factor:.2f}**"
        )
        self.info_label.config(text=info_text)

    # --- Mouse Dragging Methods ---

    def start_drag(self, event):
        """Called when the left mouse button is clicked inside the selection."""
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag(self, event):
        """Called repeatedly while the mouse is held down and dragged."""
        if not self.rect_id:
            return

        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        
        # Move the rectangle and the center lines
        self.canvas.move('selection_rect', dx, dy)
        self.canvas.move('selection_center_line', dx, dy) 
        
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        

    def end_drag(self, event):
        """Called when the mouse button is released."""
        if not self.rect_id:
            return

        # Get the new scaled coordinates of the rectangle after potential dragging
        x1_scaled, y1_scaled, x2_scaled, y2_scaled = self.canvas.coords(self.rect_id)
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Clamp the rectangle to the canvas boundaries
        if x1_scaled < 0 or x2_scaled > canvas_width or y1_scaled < 0 or y2_scaled > canvas_height:
             # Calculate clamping offsets
            dx_clamp = 0
            dy_clamp = 0
            if x1_scaled < 0: dx_clamp = -x1_scaled
            elif x2_scaled > canvas_width: dx_clamp = canvas_width - x2_scaled

            if y1_scaled < 0: dy_clamp = -y1_scaled
            elif y2_scaled > canvas_height: dy_clamp = canvas_height - y2_scaled
            
            # Move the rectangle and its center lines by the clamped amount
            if dx_clamp != 0 or dy_clamp != 0:
                self.canvas.move('selection_rect', dx_clamp, dy_clamp)
                self.canvas.move('selection_center_line', dx_clamp, dy_clamp)
        
        # Re-fetch potentially clamped coordinates
        x1_scaled, y1_scaled, x2_scaled, y2_scaled = self.canvas.coords(self.rect_id)
        
        # Convert the scaled top-left coordinates back to original image pixels
        scale = self.scale_factor
        
        new_x = round(x1_scaled / scale)
        new_y = round(y1_scaled / scale)
        
        # Update the input fields with the new original pixel coordinates
        self.x_var.set(str(new_x))
        self.y_var.set(str(new_y))

        # Re-run show_selection to ensure input and selection box match precisely
        self.show_selection() 


    # --- Selection, Validation, and Saving Methods ---

    def get_selection_coords(self):
        """Retrieves and validates selection coordinates based on the ORIGINAL image size."""
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
            size = int(self.size_var.get())
            
            if size <= 0: raise ValueError("Size must be positive.")
            if not self.image: raise ValueError("No image loaded.")
            
            # Clamp selection to be fully within the image boundaries
            x = max(0, x)
            y = max(0, y)
            size = min(size, self.image.width - x, self.image.height - y)
            
            if size <= 0:
                return None
                
            x2 = x + size
            y2 = y + size
            
            # Update inputs if clamping changed them
            if x != int(self.x_var.get()) or y != int(self.y_var.get()) or size != int(self.size_var.get()):
                 self.x_var.set(str(x))
                 self.y_var.set(str(y))
                 self.size_var.set(str(size))
            
            return x, y, x2, y2, size
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Input error: {e}. Please ensure inputs are positive integers.")
            return None

    def show_selection(self):
        """Draws/updates the selection rectangle and its center lines on the canvas."""
        coords_orig = self.get_selection_coords()
        if not coords_orig or not self.canvas:
            return

        x1_orig, y1_orig, x2_orig, y2_orig, size_orig = coords_orig
        
        # Scale coordinates for accurate display
        scale = self.scale_factor
        x1_scaled = x1_orig * scale
        y1_scaled = y1_orig * scale
        x2_scaled = x2_orig * scale
        y2_scaled = y2_orig * scale
        
        # 1. Update/Create the Selection Rectangle
        if self.rect_id:
            self.canvas.coords(self.rect_id, x1_scaled, y1_scaled, x2_scaled, y2_scaled)
        else:
            self.rect_id = self.canvas.create_rectangle(
                x1_scaled, y1_scaled, x2_scaled, y2_scaled, 
                outline='red', 
                width=2, 
                tags='selection_rect'
            )
            # Ensure the drag bindings are applied immediately after creation
            self.canvas.tag_bind('selection_rect', '<Button-1>', self.start_drag)
            self.canvas.tag_bind('selection_rect', '<B1-Motion>', self.on_drag)
            self.canvas.tag_bind('selection_rect', '<ButtonRelease-1>', self.end_drag)

        # 2. Draw/Update the Center Lines relative to the selection box
        self.canvas.delete('selection_center_line') # Delete old lines

        center_x = (x1_scaled + x2_scaled) / 2
        center_y = (y1_scaled + y2_scaled) / 2
        
        # Horizontal line across the box
        self.canvas.create_line(x1_scaled, center_y, x2_scaled, center_y, 
                                fill='gray', dash=(4, 2), width=1, tags='selection_center_line')
        
        # Vertical line across the box
        self.canvas.create_line(center_x, y1_scaled, center_x, y2_scaled, 
                                fill='gray', dash=(4, 2), width=1, tags='selection_center_line')

    def save_replicated_image(self):
        """
        Crops the original image, replicates it 3x2, scales it to 6x4 inches 
        at 300 PPI, and saves the new file.
        """
        coords_orig = self.get_selection_coords()
        if not coords_orig or not self.image:
            return

        x1, y1, x2, y2, size = coords_orig
        
        try:
            cropped_region = self.image.crop((x1, y1, x2, y2))
            
            new_width_initial = size * 3
            new_height_initial = size * 2
            
            new_image = Image.new('RGB', (new_width_initial, new_height_initial))
            
            for row in range(2):
                for col in range(3):
                    x_offset = col * size
                    y_offset = row * size
                    new_image.paste(cropped_region, (x_offset, y_offset))
            
            final_width_px = int(TARGET_WIDTH_INCH * TARGET_PPI) 
            final_height_px = int(TARGET_HEIGHT_INCH * TARGET_PPI) 
            
            final_image = new_image.resize(
                (final_width_px, final_height_px), 
                Image.LANCZOS
            )

            save_path = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")],
                title=f"Save {TARGET_WIDTH_INCH}x{TARGET_HEIGHT_INCH} Inch Image As"
            )

            if save_path:
                dpi_setting = (TARGET_PPI, TARGET_PPI) 
                
                final_image.save(save_path, dpi=dpi_setting, quality=95)
                messagebox.showinfo("Success", 
                    f"Replicated and rescaled image saved to:\n{save_path}\n"
                    f"Final Size: {final_width_px} x {final_height_px} px ({TARGET_WIDTH_INCH}x{TARGET_HEIGHT_INCH} in @ {TARGET_PPI} PPI)"
                )
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process and save image: {e}")

# --- Run the Application ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.mainloop()
    