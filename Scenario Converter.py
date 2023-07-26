import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image
import json
import numpy as np

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master.geometry('200x225')  # Change the numbers as you see fit
        self.pack()
        self.create_widgets()
    
    def create_widgets(self):
        # Terrain file
        self.terrain_label = tk.Label(self, text="Terrain File")
        self.terrain_label.pack(side="top")
        self.terrain_entry = tk.Entry(self, bd=2)
        self.terrain_entry.pack(side="top")
        self.terrain_btn = tk.Button(self, text="SELECT", command=self.load_terrain)
        self.terrain_btn.pack(side="top")

        # Borders file
        self.border_label = tk.Label(self, text="Borders File")
        self.border_label.pack(side="top")
        self.border_entry = tk.Entry(self, bd=2)
        self.border_entry.pack(side="top")
        self.border_btn = tk.Button(self, text="SELECT", command=self.load_border)
        self.border_btn.pack(side="top")

        # Scenario name
        self.name_label = tk.Label(self, text="Scenario Name")
        self.name_label.pack(side="top")
        self.name_entry = tk.Entry(self, bd=2)
        self.name_entry.pack(side="top")

        # Generate button
        self.generate_button = tk.Button(self, text="GENERATE", command=self.generate_file)
        self.generate_button.pack(side="bottom")

    def load_terrain(self):
        filename = filedialog.askopenfilename(title = "Please select the Terrain file", filetypes = (("PNG Files", "*.png"),))
        self.terrain_entry.delete(0, tk.END)
        self.terrain_entry.insert(0, filename)

    def load_border(self):
        filename = filedialog.askopenfilename(title = "Please select the Borders file", filetypes = (("PNG Files", "*.png"),))
        self.border_entry.delete(0, tk.END)
        self.border_entry.insert(0, filename)

    def generate_file(self):
        terrain_path = self.terrain_entry.get()
        borders_path = self.border_entry.get()
        scenario_name = self.name_entry.get()

        # Reading image data
        def get_image_data(image_path):
            image = Image.open(image_path)
            # Added a debugging print statement here to check the mode
            print(f"Image mode: {image.mode}")
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image = image.transpose(Image.FLIP_LEFT_RIGHT).rotate(180)
            width, height = image.size
            pixels = list(image.getdata())
            # pixels = list(zip(*(iter(pixels),) * 3))
            
            return pixels, width, height


        terrain_pixels, terrain_width, terrain_height = get_image_data(terrain_path)
        borders_pixels, borders_width, borders_height = get_image_data(borders_path)

        # Convert hex color to rgb color tuple
        def hex_to_rgb(color_code):
            return tuple(int(color_code[i:i+2], 16) for i in (0, 2, 4))

        # Calculate the Euclidean distance between two color codes
        def color_dist(c1, c2):
            return np.sqrt(sum((p-q)**2 for p,q in zip(c1, c2)))

        # Find the closest color in the terrain_types map
        def closest_color(pixel_color, color_map):
            min_colors = min(color_map.items(), key=lambda item: color_dist(pixel_color, hex_to_rgb(item[0])))
            return min_colors[1]

        # Processing terrain pixels
        def process_terrain_pixels(pixels):
            terrain_types = {
                "FFFFFF": {"type": 0, "name": "water", "value": 0},
                "000000": {"type": 1, "name": "basic land", "value": 10},
                "CCCCCC": {"type": 2, "name": "crossing", "value": 0},
                "666666": {"type": 3, "name": "desert/tundra", "value": 1},
                "333333": {"type": 4, "name": "hills", "value": 3},
                "999999": {"type": 5, "name": "mountains", "value": 0}
            }

            processed_pixels = []

            for pixel in pixels:
                color = "".join([f"{i:02x}" for i in pixel[:3]]).upper()
                if color in terrain_types:
                    processed_pixels.append(terrain_types[color]["type"])
                else:
                    nearest_terrain = closest_color(pixel, terrain_types)
                    processed_pixels.append(nearest_terrain["type"])
                    
            return processed_pixels

        terrain_data = process_terrain_pixels(terrain_pixels)

        # Processing borders pixels
        def process_borders_pixels(pixels, width):
            id_counter = 1
            color_ids = {}
            positions = {}
            processed_pixels = []

            for i, pixel in enumerate(pixels):
                color = "".join([f"{i:02x}" for i in pixel[:3]]).upper()
                x = i % width
                y = i // width

                # Ignore black, white, and "0099FF" pixels
                if color in ["000000", "FFFFFF", "0099FF"]:
                    processed_pixels.append(0)
                elif color in color_ids:
                    processed_pixels.append(color_ids[color])
                else:
                    color_ids[color] = id_counter
                    positions[id_counter] = {"x": x, "y": y}
                    processed_pixels.append(id_counter)
                    id_counter += 1

            return processed_pixels, color_ids, positions



        processed_pixels, color_ids, positions = process_borders_pixels(borders_pixels, borders_width)
        borders_data = processed_pixels  # Assign the processed pixels to borders_data

        def calculate_nation_properties(terrain_data, borders_data, terrain_values):
            nation_properties = {}

            for terrain_type, nation_id in zip(terrain_data, borders_data):
                if nation_id != 0:
                    if nation_id not in nation_properties:
                        nation_properties[nation_id] = {"landValue": 0, "maxArea": 0}
                    nation_properties[nation_id]["landValue"] += terrain_values[terrain_type]
                    nation_properties[nation_id]["maxArea"] += 1

            return nation_properties

        terrain_values = {0: 0, 1: 10, 2: 0, 3: 1, 4: 3, 5: 0}
        nation_properties = calculate_nation_properties(terrain_data, borders_data, terrain_values)

        data = {
            "version": "2.3.2",
            "width": terrain_width,
            "height": terrain_height,
            "currentGameTime": 0,
            "nations": [],
            "cities": [],
            "alliances": [],
            "wars": [],
            "terrain": terrain_data,
            "owner": borders_data
        }

        # Creating nations
        for color, id in color_ids.items():
            print(str(color))
            nation = {
                "id": id,
                "name": str(id),
                "destroyed": False,
                "color": {
                    "r": int(color[0:2], 16) / 255,
                    "g": int(color[2:4], 16) / 255,
                    "b": int(color[4:6], 16) / 255,
                    "a": 1
                },
                "pos": positions[id],
                "startYear": 0,
                "endYear": 0,
                "revoltId": [],
                "lives": [],
                "killedId": [],
                "gold": 50,
                "landValue": nation_properties.get(id, {}).get("landValue", 0),
                "maxArea": nation_properties.get(id, {}).get("maxArea", 0),
                "revoltValue": 0,
                "aiDisabled": False,
                "stress": 0,
                "totalWars": 0,
                "incomeModifier": 1
            }
            
            data["nations"].append(nation)

        # Writing to JSON file
        with open(f"{scenario_name}.aoc", "w") as file:
            json.dump(data, file, indent=4)
    
root = tk.Tk()
root.title("PNG to .aoc Scenario v1.0")  # Set the title for the window
app = Application(master=root)
app.mainloop()