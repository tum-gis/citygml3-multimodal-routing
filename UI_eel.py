# Imports
import datetime
import re
from math import e
from tkinter import Label, PhotoImage, Tk, mainloop

import eel
import utm
from geopy.geocoders import Nominatim

from constants import password, username
from interactor4neo4j import Neo4jNavigator

if __name__ == "__main__":

    # Constants
    uri = "bolt://localhost:7687"
    geolocator = Nominatim(user_agent="navigator")

    # Set web files folder and optionally specify which file types to check for eel.expose()
    #   *Default allowed_extensions are: ['.js', '.html', '.txt', '.htm', '.xhtml']
    eel.init('web', allowed_extensions=['.js', '.html'])

    @eel.expose                         # Expose this function to Javascript
    def say_hello_py(x):
        print('Hello from %s' % x)
    # Call a Javascript function
    say_hello_py('Python World!')
    eel.say_hello_js('Python World!')   




    # Create object
    splash_root = Tk()

    w = 350
    h = 350
    eel_width = 1500
    eel_height = 1050
    # get screen width and height
    ws = splash_root.winfo_screenwidth() # width of the screen
    hs = splash_root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    eel_x = (ws/2) - (eel_width/2)
    eel_y = (hs/2) - (eel_height/2)

    # Adjust size
    splash_root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    # Adjust background color
    splash_root.config(bg="white")
    # Adjust title
    splash_root.title("Welcome")
    # add icon
    splash_root.iconbitmap("./img/map-place-pin-location-svgrepo-com-white.ico")
    # empty Label as puffer on top
    puffer_label = Label(text=" ")
    puffer_label.pack()
    # Add image file
    photo = PhotoImage(file="./img/map-place-pin-location-svgrepo-com.png")
    # Create Label
    splash_image_label = Label(splash_root, image=photo)
    # Display Label
    splash_image_label.pack()

    # main window function
    def main():
        navigator = Neo4jNavigator(uri, username, password)
        navigator.generate_kd_tree()
        # destroy splash window
        splash_root.destroy()

        @eel.expose
        def get_bounding_box():
            bounding_box = navigator.get_bounding_box()
            # convert to WGS84
            wgs84_coords = utm.to_latlon(bounding_box[0][0], bounding_box[0][1], 32, 'U')
            wgs84_coords2 = utm.to_latlon(bounding_box[1][0], bounding_box[1][1], 32, 'U')
            return [wgs84_coords[0], wgs84_coords[1], wgs84_coords2[0], wgs84_coords2[1]]

        @eel.expose
        def routing(locations, weight, alg):
            weight = int(weight)
            alg = int(alg)
            print(locations, weight, alg)

            # return the nearest node ids to be used in the routing algorithm
            # analyse pattern of locations either match coordinates or street names
            # Match regex pattern of locations: "number, number"
            # if pattern matches, use coordinates directly
            find_nearest_node_start = True
            find_nearest_node_dest = True
            if re.match(r"(\d+\.?\d*),\s*(\d+\.?\d*)", locations[0]):
                coordinates_start = [float(x) for x in re.findall(r"(\d+\.?\d*),\s*(\d+\.?\d*)", locations[0])[0]]
            elif locations[0].startswith("UUID_"):
                start_id = locations[0]
                find_nearest_node_start = False
                # get coordinates of ids from database
                res = navigator.get_TrafficSpace_geometry_coordinates(start_id, "forwards")
                # convert to WGS84
                wgs84_coords = utm.to_latlon(res[0][0], res[0][1], 32, 'U')
                navigator.start_coords = [wgs84_coords[0], wgs84_coords[1]]
            else:
                # TODO geocoding
                location = geolocator.geocode(locations[0])
                coordinates_start = [location.latitude, location.longitude]
                
            if re.match(r"(\d+\.?\d*),\s*(\d+\.?\d*)", locations[1]):
                coordinates_destination = [float(x) for x in re.findall(r"(\d+\.?\d*),\s*(\d+\.?\d*)", locations[1])[0]]
            elif locations[1].startswith("UUID_"):
                destination_id = locations[1]
                find_nearest_node_dest = False
                res = navigator.get_TrafficSpace_geometry_coordinates(destination_id, "forwards")
                wgs84_coords = utm.to_latlon(res[0][0], res[0][1], 32, 'U')
                navigator.destination_coords = [wgs84_coords[0], wgs84_coords[1]]
            else:
                location = geolocator.geocode(locations[1])
                coordinates_destination = [location.latitude, location.longitude]
                
            
            if find_nearest_node_start:
                print(f"[INFO] Start coordinates: {coordinates_start}")
                navigator.start_coords = coordinates_start
                
                # Convert coordinates to utm
                start_location = list(utm.from_latlon(coordinates_start[0], coordinates_start[1])[:2])
                

                trafficSpace_ids = navigator.get_nearest_TrafficSpace_id([start_location])
                print(f"[INFO] TrafficSpace IDs: {trafficSpace_ids}")
                start_id = trafficSpace_ids[0]
            if find_nearest_node_dest:
                print(f"[INFO] Destination coordinates: {coordinates_destination}")
                navigator.destination_coords = coordinates_destination
                # Convert coordinates to utm
                destination_location = list(utm.from_latlon(coordinates_destination[0], coordinates_destination[1])[:2])
                trafficSpace_ids = navigator.get_nearest_TrafficSpace_id([destination_location])
                print(f"[INFO] TrafficSpace IDs: {trafficSpace_ids}")
                destination_id = trafficSpace_ids[0]
            # else:
            #     pass
                # # get coordinates of ids from database
                # res = navigator.get_TrafficSpace_geometry_coordinates(start_id, "forwards")
                # # convert to WGS84
                # wgs84_coords = utm.to_latlon(res[0][0], res[0][1], 32, 'U')
                # navigator.start_coords = [wgs84_coords[0], wgs84_coords[1]]
                # res = navigator.get_TrafficSpace_geometry_coordinates(destination_id, "forwards")
                # wgs84_coords = utm.to_latlon(res[0][0], res[0][1], 32, 'U')
                # navigator.destination_coords = [wgs84_coords[0], wgs84_coords[1]]

            
            

            # Uncomment for Grafing Datasets
            # self.start_coords = [self.config_data['start']['lat_grafing'], self.config_data['start']['lon_grafing']]
            # self.destination_coords = [self.config_data['destination']['lat_grafing'], self.config_data['destination']['lon_grafing']]
            # self.start_location = list(utm.from_latlon(self.config_data['start']['lat_grafing'], self.config_data['start']['lon_grafing'])[:2])
            # self.destination_location = list(utm.from_latlon(self.config_data['destination']['lat_grafing'], self.config_data['destination']['lon_grafing'])[:2])

            # Uncomment for May Ingolstadt Database
            # self.start_coords = [self.config_data['start']['lat'], self.config_data['start']['lon']]
            # self.destination_coords = [self.config_data['destination']['lat'], self.config_data['destination']['lon']]
            # self.start_location = list(utm.from_latlon(self.config_data['start']['lat'], self.config_data['start']['lon'])[:2])
            # self.destination_location = list(utm.from_latlon(self.config_data['destination']['lat'], self.config_data['destination']['lon'])[:2])


            # print(f"[INFO] Start location: {self.start_location}, Destination location: {self.destination_location}")

            

            
            print(f"Using start id: {start_id}, destination id: {destination_id}")
            if alg == 0: # Dijkstra
                if weight == 0: # distance simple
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "euclidean_segment_length"])
                elif weight == 1: # distance advanced
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "advanced_segment_length"])
                elif weight == 2: # inclination
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "inclination_weight"])
                elif weight == 3: # width
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "width_weight"])
                elif weight == 4: # speed
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "speed_weight"])
                elif weight == 5: # time
                    [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal([start_id, destination_id, "time_weight"])
            elif alg == 1: # A*
                if weight == 0: # distance simple
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "euclidean_segment_length"])
                elif weight == 1: # distance advanced
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "advanced_segment_length"])
                elif weight == 2: # inclination
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "inclination_weight"])
                elif weight == 3: # width
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "width_weight"])
                elif weight == 4: # speed
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "speed_weight"])
                elif weight == 5: # time
                    [route_nodes, weight] = navigator.shortest_path_APOC_astar([start_id, destination_id, "time_weight"])
            else:
                # TODO error handling
                pass
            if route_nodes == None or weight == None:
                return False
            
            [start_coords, destination_coords, geometry_converted, distance, weight, transportation] = navigator.visualize_shortest_path_leaflet(route_nodes, weight)

            return [start_coords, destination_coords, geometry_converted, distance, weight, transportation]
    # Set Interval
    splash_root.after(3000, main)




    # Execute tkinter
    mainloop()

    def end_app(arg1, arg2):
        print("Application closed")
        exit(0)
    # end application when window is closed
    eel.start('UI_eel_main.html', size=(eel_width, eel_height), position=(eel_x, eel_y),close_callback=end_app)    
