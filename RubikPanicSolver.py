import os
import sys
import cv2
import numpy as np
import tkinter as tk
import twophase.solver as sv
from tkinter import messagebox
from PIL import Image, ImageTk

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

class App:
    def __init__(self, window, window_title, image_size=(100, 100)): 
        self.window = window
        self.window.title(window_title)

        # Desired window size
        self.window_width = 900
        self.window_height = 550
        self.window.geometry(f'{self.window_width}x{self.window_height}')
        
        icon_path = os.path.join(base_dir, "src/icon.ico")
        self.window.iconbitmap(icon_path)
        
        self.window.update_idletasks()
        # Calculate x and y position to center the window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        center_x = int((screen_width - self.window_width) / 2)
        center_y = int((screen_height - self.window_height) / 2)

        # Set window position
        self.window.geometry(f'{self.window_width}x{self.window_height}+{center_x}+{center_y}')
        
        self.window.resizable(False, False)
        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)
        if not self.vid.isOpened():
            print("No camera detected. Please connect a camera and try again.")
            sys.exit(1)
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        self.image_size = image_size

        self.tk_image = None
        self.popup = None

        # Create a frame for the camera and another for the captured images
        self.camera_frame = tk.Frame(window)
        self.camera_frame.grid(row=0, column=0)  # Use grid here
        self.images_frame = tk.Frame(window)
        self.images_frame.grid(row=0, column=1)  # Use grid here

        self.canvas = tk.Canvas(self.camera_frame, width=self.width, height=self.height)
        self.canvas.grid(row=1, column=0, columnspan=6)  # Use grid for the canvas

        self.colors = ['white', 'green', 'red', 'blue', 'orange', 'yellow']
        self.color_button_styles = {
            'white': {'bg': '#FFFFFF'},
            'green': {'bg': '#caffbf'},
            'red': {'bg': '#ffadad'},
            'blue': {'bg': '#a0c4ff'},
            'orange': {'bg': '#ffd6a5'},
            'yellow': {'bg': '#fdffb6'}
        }
     
        self.image_labels = {}  # To store image tags
        
        for i, color in enumerate(self.colors):
            button_style = {'font': ('Helvetica', 12), 'fg': 'black', **self.color_button_styles[color]}
            solve_button_style = {'font': ('Helvetica', 12), 'bg': '#bdb2ff', 'fg': 'black'}  #
            btn = tk.Button(self.camera_frame, text=f"{color.capitalize()}", width=10, **button_style,
                            command=lambda c=color: self.snapshot(c))
            btn.grid(row=0, column=i)  # Place buttons in a row and in separate columns

            # Organize labels and spaces for images in a grid
            row = 2 * (i // 2)  # Calculate row for grid
            column = i % 2  # Calculate column for grid
            label = tk.Label(self.images_frame, text=color.capitalize(), font=("Arial", 12))
            label.grid(row=row, column=column, padx=5, pady=5)

            # Define a fixed size for image Labels and add a border
            image_label = tk.Label(self.images_frame, borderwidth=2, relief="groove", width=self.image_size[0], height=self.image_size[1])
            image_label.grid(row=row+1, column=column, padx=5, pady=5)
            self.image_labels[color] = image_label

            # Upload image if it exists
            self.load_initial_image(color)
        self.solve_button = tk.Button(self.camera_frame, text="Solve", width=20, **solve_button_style, command=self.solve_rubik)     
        self.solve_button.grid(row=3, column=0, columnspan=6)
        self.update()
        self.window.mainloop()

    def load_initial_image(self, color):
        # Color dictionary in RGB format
        color_rgb_values = {
            'white': '#FFFFFF',
            'green': '#caffbf',
            'red': '#ffadad',
            'orange': '#ffd6a5',
            'blue': '#a0c4ff',
            'yellow': '#fdffb6'
        }

        # Create a blank image of the specified size
        img = Image.new('RGB', self.image_size, color_rgb_values[color])

        # Convert PIL image to PhotoImage and display it in the corresponding label
        photo = ImageTk.PhotoImage(img)
        self.image_labels[color].config(image=photo)
        self.image_labels[color].image = photo  # Maintain a reference

    def snapshot(self, color):
        ret, frame = self.vid.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            x1 = int(self.width / 2 - 150)
            y1 = int(self.height / 2 - 150)
            x2 = int(self.width / 2 + 150)
            y2 = int(self.height / 2 + 150)
            cropped_frame = frame[y1:y2, x1:x2]
            image = Image.fromarray(cropped_frame)
            image.save(f"{color}.png")

            # Show the captured image in the corresponding label
            self.display_image(image, color)

    def display_image(self, image, color):
        image.thumbnail((100, 100))  # Resize the image to display it
        photo = ImageTk.PhotoImage(image)
        self.image_labels[color].config(image=photo)
        self.image_labels[color].image = photo  # Maintain a reference

    def update(self):
        ret, frame = self.vid.read()
        if ret:
            x1 = int(self.width / 2 - 150)
            y1 = int(self.height / 2 - 150)
            x2 = int(self.width / 2 + 150)
            y2 = int(self.height / 2 + 150)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.window.after(10, self.update)
 
    def solve_rubik_cube(self):
        def show_cube(codes):
            # Mapping from letters to colors
            colors2 = {'U': 'W', 'F': 'G', 'D': 'Y', 'R': 'R', 'B': 'B', 'L': 'O'}

            # Check if the code is the correct length
            if len(codes) != 54:
                return "Invalid code"

            # Creating the faces dictionary in a more compact way
            faces = {side: codes[i*9:(i+1)*9] for i, side in enumerate('URFDLB')}

            # Convert letters to colors using list comprehension
            faces = {side: ''.join(colors2[letter] for letter in face) for side, face in faces.items()}

            # Build the 2D representation using join and list comprehension
            upper = '\n   '.join([''] + [''.join(faces['U'][i:i+3]) for i in range(0, 9, 3)])
            middle = '\n'.join([''.join(faces[side][i:i+3] for side in 'LFRB') for i in range(0, 9, 3)])
            lower = '\n   '.join([''] + [''.join(faces['D'][i:i+3]) for i in range(0, 9, 3)])

            return upper + '\n' + middle + lower

        def draw_cube_img(codes):
            colors_rgba = {
                'U': (255, 255, 255, 255),  # White
                'F': (202, 255, 191, 255),      # Green
                'D': (253, 255, 182, 255),    # Yellow
                'R': (255, 173, 173, 255),      # Red
                'B': (160, 196, 255, 255),      # Blue
                'L': (255, 214, 165, 255)     # Orange
            }

            size_cell = 24
            img_drawed = Image.new("RGBA", (12 * size_cell, 9 * size_cell), (0, 0, 0, 0))

            def draw_cell(x, y, color):
                x1, y1 = x + 1, y + 1
                x2, y2 = x + size_cell - 1, y + size_cell - 1
                for dy in range(y, y2):
                    for dx in range(x, x2):
                        img_drawed.putpixel((dx, dy), (0, 0, 0, 255) if dy == y or dy == y2 - 1 or dx == x or dx == x2 - 1 else color)

            def draw_side(offset_x, offset_y, indices):
                for i, idx in enumerate(indices):
                    x = (i % 3) * size_cell + offset_x
                    y = (i // 3) * size_cell + offset_y
                    draw_cell(x, y, colors_rgba[codes[idx]])

            face_positions = {
                'U': (3, 0), 'F': (3, 3), 'D': (3, 6),
                'L': (0, 3), 'R': (6, 3), 'B': (9, 3)
            }
            for i, face in enumerate('URFDLB'):
                draw_side(*[v * size_cell for v in face_positions[face]], range(i*9, (i+1)*9))

            return img_drawed
    
        filenames = [
            'white.png', 
            'red.png', 
            'green.png',
            'yellow.png', 
            'orange.png', 
            'blue.png'
        ]

        # Dictionary to convert color names to Rubik's letters
        color_to_letter = {
            'white': 'U',
            'red': 'R',
            'green': 'F',
            'yellow': 'D',
            'blue': 'B',
            'orange': 'L'
        }

        # Color calibration (these values are only examples and must be adjusted)
        color_ranges = {
            'red': ((0, 100, 100), (10, 255, 255)),
            'blue': ((100, 150, 0), (140, 255, 255)),
            'yellow': ((20, 100, 100), (30, 255, 255)),
            'orange': ((10, 150, 150), (20, 255, 255)),
            'green': ((40, 50, 50), (80, 255, 255)),
            'white': ((0, 0, 180), (180, 60, 255))
        }

        def detect_color(cell_hsv):
            color_name = 'unknown'
            max_count = 0
            for name, (lower, upper) in color_ranges.items():
                mask = cv2.inRange(cell_hsv, np.array(lower, dtype=np.uint8), np.array(upper, dtype=np.uint8))
                count = cv2.countNonZero(mask)
                if count > max_count:
                    max_count = count
                    color_name = name
            return color_name

        rubik_code = ''

        for filename in filenames:
            # Upload image
            image = cv2.imread(filename)
            height, width, _ = image.shape

            # We assume the image is square, divide it into a 3x3 grid
            cell_height = height // 3
            cell_width = width // 3

            # Convert image to HSV
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # List to store the letters of the colors detected in the current image
            detected_colors_letters = []

            # Analyze each grid cell
            for i in range(3):
                for j in range(3):
                    # Coordinates of the upper left corner of the box
                    x_start = j * cell_width
                    y_start = i * cell_height
                    
                    # Extract the box from the image
                    cell = hsv_image[y_start:y_start + cell_height, x_start:x_start + cell_width]
                    
                    # Take a sample from the center of the box to avoid edges
                    sample = cell[cell_height//4:3*cell_height//4, cell_width//4:3*cell_width//4]

                    # Detect the color in the sample
                    color = detect_color(sample)
                    detected_colors_letters.append(color_to_letter.get(color, 'U'))

            # Concatenate the letter sequence of the current image to the cube code
            rubik_code += ''.join(detected_colors_letters)

        # Print the complete Rubik's Cube code
        #print(rubik_code)
        adjust = rubik_code[:4] + 'U' + rubik_code[5:]
        codes = adjust
        print(adjust)
        print(show_cube(codes))
        # At the end of your solve_rubik_cube method, after generating the image:
        img_drawed = draw_cube_img(codes)
        img_drawed.save("cube_rubik.png")

        # Create a new popup window
        self.popup_window = tk.Toplevel(self.window)
        self.popup_window.title("Rubik's Cube Solution")

        # Create a label widget and add the image
        self.tk_image = ImageTk.PhotoImage(img_drawed)
        label = tk.Label(self.popup_window, image=self.tk_image)
        label.image = self.tk_image  # Keep a reference.
        label.pack()
        
        # Trying to solve the Rubik's cube
        solution = sv.solve(adjust, 19, 2)
        print(solution)
        # Check if the solution contains an error message
        if "Error" in solution:
            messagebox.showerror("Error", "Error solving Rubik's cube. Please take some photos with better lighting..")
        else:
            messagebox.showinfo("Solution", solution) 
        
    def solve_rubik(self):
        filenames = ['white.png', 'red.png', 'green.png', 'yellow.png', 'orange.png', 'blue.png']

        # Check if all files exist using list comprehension and all()
        if not all(os.path.exists(filename) for filename in filenames):
            missing_files = [filename for filename in filenames if not os.path.exists(filename)]
            messagebox.showerror("Error", f"Files not found: {', '.join(missing_files)}")
            return

        # If all files exist, proceed to solve the cube
        rubik_code = self.solve_rubik_cube()
# Create a window and pass it to the App class
App(tk.Tk(), "RubikPanicSolver 1.0.0 by zkrvf")