# Script for testing the navigator class

# Imports
import datetime
import random

from constants import password, username
from interactor4neo4j import Neo4jNavigator

# Constants
uri = "bolt://localhost:7687"

def routing_test():
    # ids = ["UUID_07b1fe85-e08a-3917-9b65-b98b1f07986a", "UUID_ad8cf1d8-cd8a-3626-a49b-93bf8ac8c546"]

    navigator = Neo4jNavigator(uri, username, password)
    # [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra(navigator.trafficSpace_ids)
    vars= navigator.trafficSpace_ids
    vars.append("advanced_segment_length") #advanced_segment_length, euclidean_segment_length, inclination, width 
    # [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra_multimodal(vars)
    [route_nodes, weight] = navigator.shortest_path_APOC_astar(vars)
    navigator.visualize_shortest_path_leaflet(route_nodes, weight)


    # start_coords = [navigator.config_data['start']['lat_grafing'], navigator.config_data['start']['lon_grafing']]
    # destination_coords = [navigator.config_data['destination']['lat_grafing1'], navigator.config_data['destination']['lon_grafing1']]
    # start_location = list(utm.from_latlon(navigator.config_data['start']['lat_grafing'], navigator.config_data['start']['lon_grafing'])[:2])
    # destination_location = list(utm.from_latlon(navigator.config_data['destination']['lat_grafing1'], navigator.config_data['destination']['lon_grafing1'])[:2])

    # ids = []
    # coordinates = [start_location, destination_location]
    # for point in coordinates:
    #     idx = navigator.get_nearest_points_kd_tree(point)
    #     ids.append(navigator.id_list[idx[0]])
    
    # [route_nodes, weight] = navigator.shortest_path_APOC_dijkstra(ids)
    # navigator.visualize_shortest_path_leaflet(route_nodes, weight)

    navigator.close()

    # print("\n\033[92m[INFO] Route nodes:\033[0m")
    # for node in route_nodes:
    #     print(node['id'])
    print(f"\n\033[92m[INFO] Routing over {len(route_nodes)} nodes with a weight of {weight} [unit]!\033[0m")

def garage_routing(navigator, entrance_id, parking_lot_id, destination_id):
    secondary_route_ids = []
    tertiary_route_ids = []
    
    # secondary routing to the parking lot
    secondary_route = navigator.shortest_path_APOC_dijkstra_multimodal([entrance_id, parking_lot_id, ''])
    # get the secondary route ids
    for node in secondary_route[0]:
        secondary_route_ids.append(node['id'])
    # tertiary routing from parking lot to the destination
    tertiary_route = navigator.shortest_path_APOC_dijkstra_multimodal([parking_lot_id, destination_id, ''])
    # get the tertiary route ids
    for node in tertiary_route[0]:
        tertiary_route_ids.append(node['id'])

    return [secondary_route_ids, tertiary_route_ids]

def parking_garage_routing_test(start_node_id = "UUID_b363645e-85cd-397b-a22a-3d23cc6c90a1", destination_node_id =  "UUID_0ea2adaf-a3b5-36d8-9cb4-29878905c9c7"):
    # Starting from DRIVING
    # start_node_id = "UUID_86ea15c6-1af5-3e50-930c-1e4ee620af2f" # "UUID_b363645e-85cd-397b-a22a-3d23cc6c90a1"
    # destination_node_id = "UUID_9d6a7db9-2b78-3b84-a2b8-e364610893fb" # "UUID_0ea2adaf-a3b5-36d8-9cb4-29878905c9c7"
    # reverse test starting from SIDWALK
    # start_node_id = "UUID_b363645e-85cd-397b-a22a-3d23cc6c90a1"
    # destination_node_id =  "UUID_ed4431da-06fc-3633-aa58-f67423858361"
    parking_lot_ids = ["trafficspace8", "trafficspace7", "trafficspace6", "trafficspace5", "trafficspace4", "trafficspace3", "trafficspace2"]
    entrance_id="TS_section12"

    navigator = Neo4jNavigator(uri, username, password)
    primary_route = navigator.shortest_path_APOC_dijkstra_multimodal([start_node_id, destination_node_id, ''])

    print(f"\n\033[92m[INFO] Primary route: {len(primary_route[0])} nodes \033[0m")

    # get the primary route ids
    primary_route_ids = []
    for node in primary_route[0]:
        if node['id'] == entrance_id:
            secondary_tertiary_route_ids = garage_routing(navigator, entrance_id, random.choice(parking_lot_ids), destination_node_id)
            break
        primary_route_ids.append(node['id'])

    # combine the primary route ids with the secondary and tertiary route ids
    route_ids = [primary_route_ids] + secondary_tertiary_route_ids

    # visualize the route
    color_strings = ["\033[93m", "\033[91m", "\033[94m"]
    print(f"\n\033[92m[INFO] Routing over {sum([len(route) for route in route_ids])} nodes!\033[0m")
    for route in route_ids:
        for id in route:
            # change console print color
            print(color_strings[route_ids.index(route)] + id + "\033[0m")
            
    
    # store the routes in a .csv file with a column for each route and a header
    with open("route.csv", "w") as route_file:
        # Header
        route_file.write(f"{','.join([f'route_{i}' for i in range(len(route_ids))])}\n")
        # Routes
        for i in range(max([len(route) for route in route_ids])):
            route_file.write(f"{','.join([route[i] if i < len(route) else '' for route in route_ids])}\n")

    navigator.close()

# Start time
print(datetime.datetime.now()) 
# routing_test()

parking_garage_routing_test()