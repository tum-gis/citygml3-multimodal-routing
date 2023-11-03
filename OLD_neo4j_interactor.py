# Class to interact with neo4j database

# Imports
import re
import uuid

import numpy as np
import open3d as o3d
from neo4j import GraphDatabase
from tqdm import tqdm

# from constants import password, username

# uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
# driver = GraphDatabase.driver(uri, auth=(username, password))




# UUIDs for TrafficSpace elements
UUID_bottom_left = "UUID_666b845a-0860-3849-b81c-0b47c663b6aa"
UUID_bottom_right = "UUID_f66d4bd1-d97e-39a8-a712-1459ae9ca30b"
UUID_top_right = "UUID_6d5be29e-4813-368b-a71c-81524ef79367"

UUID_left_top = "UUID_f06c105d-9647-3f37-8ae6-23b70090d671"

#  Helper functions
def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))

        return True
    except ValueError:
        return False

# function to calculate the Euclidean distance between two points
def euclidean_distance(point1, point2):
    """Calculates the Euclidean distance between two points"""
    # Check if the points have the same dimension
    if len(point1) != len(point2):
        raise ValueError("The points have different dimensions")
    # Calculate the distance
    distance = 0
    for i in range(len(point1)):
        distance += (point1[i] - point2[i])**2
    return distance**0.5

class Neo4jInteractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    # def find_person(self, person_name):
    #     with self.driver.session() as session:
    #         result = session.execute_read(self._find_and_return_person, person_name)
    #         for record in result:
    #             print("Found person: {record}".format(record=record))

    # @staticmethod
    # def _find_and_return_person(tx, person_name):
    #     query = (
    #         "MATCH (p:Person) "
    #         "WHERE p.name = $person_name "
    #         "RETURN p.name AS name"
    #     )
    #     result = tx.run(query, person_name=person_name)
    #     return [record["name"] for record in result]

    @staticmethod
    def _find_all(tx, vars):
        query = (
            "MATCH (n) "
            "RETURN n"
        )
        result = tx.run(query, vars)
        return [record["n"] for record in result]
    
    @staticmethod
    def _count_nodes(tx, vars):
        query = (
            "MATCH (n) "
            "RETURN count(n)"
        )
        result = tx.run(query, vars)
        return [record["count(n)"] for record in result]

    @staticmethod
    def _count_relations(tx, vars):
        query = (
            "MATCH ()-[r]->() "
            "RETURN count(r)"
        )
        result = tx.run(query, vars)
        return [record["count(r)"] for record in result]
    
    @staticmethod
    def _get_labels(tx, vars):
        query = (
            "CALL db.labels()"
        )
        result = tx.run(query, vars)
        return [record["label"] for record in result]

    @staticmethod
    def _get_relationship_types(tx, vars):
        query = (
            "CALL db.relationshipTypes()"
        )
        result = tx.run(query, vars)
        return [record["relationshipType"] for record in result]

    @staticmethod
    def _get_startpoint(tx, vars):
        query = (
            "MATCH (n)-[r:successors|predecessors]->() "
            "RETURN n limit 2"
        )
        result = tx.run(query, vars)
        return [record["n"] for record in result]
    
    @staticmethod
    def _find_node(tx, vars):
        result = tx.run("MATCH (n WHERE n.id = $id ) "
            "RETURN n as node limit 2; ",
            id=vars)
        return [record["node"] for record in result]
    
    @staticmethod
    def _get_node_by_id(tx, vars):
        # To query a node by its ID the id must be converted to an integer, string IDs are not working!
        result = tx.run("MATCH (n)-[r:object]-(n2) WHERE ID(n) = $id RETURN n2;",
            id=int(vars[0]))
        # print([record["n2"] for record in result])
        return [record["n2"] for record in result]


    @staticmethod
    def _find_shortest_path(tx, vars):
        result = tx.run("MATCH (source:% WHERE source.id = $id1),(target:% WHERE target.id = $id2)"
            "MATCH p = shortestPath((source)-[*]-(target))"
            "return p;",
            id1=vars[0], id2=vars[1])
        return [record["p"] for record in result]
    
    @staticmethod
    def _find_shortest_path_apoc_djikstra(tx, vars):
        # //APOC Djikstra: Find shortest path between start and end node using SUCCESSOR_OF and NEIGHBOURS_LANE shortcut and segment_length weight MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_666b845a-0860-3849-b81c-0b47c663b6aa'}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_f66d4bd1-d97e-39a8-a712-1459ae9ca30b'}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF|NEIGHBOURS_LANE>', 'segment_length') yield path as path, weight as weight RETURN path, weight
        result = tx.run("MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id1}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id2}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF>|NEIGHBOURS_LANE', 'segment_length') yield path as path, weight as weight RETURN path, weight", id1=vars[0], id2=vars[1])
        # path = [record["path"] for record in result]
        # weight = [record["weight"] for record in result]
        for record in result:
            if len([record['path'], record['weight']]) == 2:
                return [record['path'], record['weight']]
        # return [path, weight]
    
    @staticmethod
    def _find_attribute_nodes(tx, vars):
        # //Return street segment attributes
        result = tx.run("MATCH (n)-[r:boundaries]-()-[r2:elementData]-()-[r3:ARRAY_MEMBER]-()-[r4:object]-(n2)-[r5:genericAttributes]-()-[r6:elementData]-(n3)-[r7:ARRAY_MEMBER]-(n4) WHERE n.id = $id1 RETURN n4;", id1=vars[0])
        return [record["n4"] for record in result]
    

    @staticmethod
    def _get_coordinates_traffic_space(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id= $id)-[:lod2MultiCurve]->()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(coords)  RETURN coords;", id = vars)
        return [record["coords"] for record in result]


    @staticmethod
    def _get_lanes_for_road_segment(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` )-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n2:`org.citygml4j.core.model.generics.StringAttribute` WHERE n2.name ="identifier_roadId" AND n2.value = $id) WITH n, n2 MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n3:`org.citygml4j.core.model.generics.IntAttribute` WHERE n3.name ="identifier_laneSectionId" AND n3.value = "0") RETURN n;', id = vars)
        return [record["n"] for record in result]

    @staticmethod
    def _get_lanes_by_type_for_road_segment(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` )-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n2:`org.citygml4j.core.model.generics.StringAttribute` WHERE n2.name ="identifier_roadId" AND n2.value = $id) WITH n, n2 MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n3:`org.citygml4j.core.model.generics.IntAttribute` WHERE n3.name ="identifier_laneSectionId" AND n3.value = "0") WITH n MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n4:`org.citygml4j.core.model.generics.StringAttribute` WHERE n4.name ="opendrive_lane_type" AND n4.value = $type) RETURN n;', id = vars[0], type = vars[1])
        return [record["n"] for record in result]

    @staticmethod
    def _get_specific_lane_for_road_segment(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` )-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n2:`org.citygml4j.core.model.generics.StringAttribute` WHERE n2.name ="identifier_roadId" AND n2.value = $id) WITH n, n2 MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n3:`org.citygml4j.core.model.generics.IntAttribute` WHERE n3.name ="identifier_laneSectionId" AND n3.value = $lane_section_id) WITH n MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n4:`org.citygml4j.core.model.generics.IntAttribute` WHERE n4.name ="identifier_laneId" AND n4.value =$lane_id)  RETURN n;', id = vars[0], lane_section_id = vars[1], lane_id = vars[2])
        return [record["n"] for record in result]

    @staticmethod
    def _find_trafficSpace_ids(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` ) RETURN n.id as gmlid;")
        return [record["gmlid"] for record in result]
    
    @staticmethod
    def _find_trafficSpace_geometry(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:lod2MultiCurve]-()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;', id=vars[0])
        return [record["m"] for record in result]
    
    @staticmethod
    def _find_trafficArea_SurfaceMembers(tx, vars):
        """Finds all TrafficArea SurfaceMember nodes to a TrafficSpace node"""
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(t)-[:lod2MultiSurface]-()-[:object]-()-[:surfaceMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-(m) RETURN ID(m) as id;', id=vars[0])
        return [record["id"] for record in result]

    @staticmethod
    def _find_trafficArea_geometry(tx, vars):
        result = tx.run('MATCH (s) WHERE ID(s) = $id WITH s MATCH (s)-[:object]-()-[:exterior]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;', id=vars[0])
        return [record["m"] for record in result]

    @staticmethod
    def _insert_distance_weight(tx, vars):
        result = tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.segment_length=$weight RETURN a, b;', id=vars[0], weight=vars[1])

    @staticmethod
    def _insert_TrafficSpace_coordinate_attributes(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id) SET n.lat= $lat, n.lon= $lon, n.height= $height RETURN n;', id=vars[0], lat=vars[1], lon=vars[2], height=vars[3])

    def find_all_coordinates(self):
        with self.driver.session() as session:
            result = session.execute_read(self._find_trafficSpace_ids, vars)
            print(f"Number of TrafficSpace elements: {len(result)}\n[INFO] Retrieving coordinates...")
            # for record in result:
            #     print(record)
            coord_list=[]
            id_list=[]
            for id in tqdm(result):
                # not all TrafficSpace objects have a gml UUID, therfore check if there is a string containing the UUID
                # check if the id is a string and follows the UUID pattern
                # if type(id) == str and is_valid_uuid(id):
                dist = -1
                if type(id) == str:
                    coord_node = session.execute_read(self._find_trafficSpace_geometry, [id])
                    for record in coord_node:
                        for key in list(record._properties.keys()):
                            # if only  a single digit number is in [] add a 0 in front
                            if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                record._properties.pop(key)
                            # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                            if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                record._properties[new_key] = record._properties[key]
                                record._properties.pop(key)

                        # sort the coordinates by the key
                        # print(sorted(record._properties.items(), key=lambda x: x[0]))
                        sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                        # get the lat, lon and height values of the first point 
                        lat = float(sorted_coords[0][1])
                        lon = float(sorted_coords[1][1])
                        height = float(sorted_coords[2][1])

                        lat_2 = float(sorted_coords[-3][1])
                        lon_2 = float(sorted_coords[-2][1])
                        height_2 = float(sorted_coords[-1][1])
                        coord_list.append(np.array([lat, lon, height]))
                        coord_list.append(np.array([lat_2, lon_2, height_2]))  
                        id_list.append(id)
                        id_list.append(id)

            return coord_list, id_list              

    

    
    def insert(self, query):
        with self.driver.session() as session:
            if query == "distance_weight":
                # Definition of reference point on TrafficSpace/TrafficArea element for length calculation
                # The direction of travel: left to right ==>
                # Reference point: X or O
                # TrafficSpace: 
                # |X===============================|
                # TrafficArea:
                # |O-------------------------------|
                # |--------------------------------|
                # |--------------------------------|
                # |--------------------------------|
                # |--------------------------------|
                # Combined:
                # |O-------------------------------|
                # |--------------------------------|
                # |X===============================|
                # |--------------------------------|
                # |--------------------------------|
                #
                # Length calculation for TrafficSpace a to TrafficSpace b successor relationship r:
                #                 a                                  b
                # |X===============================| |X===============================|
                # |<         distance in m        >| 
                # (a:TrafficSpace) -[r:successor {length: <distance in m>}]-> (b:TrafficSpace)

                # find all sections
                result = session.execute_read(self._find_trafficSpace_ids, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                for record in result:
                    print(record)

                print("\n\033[96m[INFO]: Adding weights to 'SUCCESSOR_OF' relationships\033[0m")
                for id in tqdm(result):
                    # not all TrafficSpace objects have a gml UUID, therfore check if there is a string containing the UUID
                    # check if the id is a string and follows the UUID pattern
                    # if type(id) == str and is_valid_uuid(id):
                    dist = -1
                    if type(id) == str:
                        coord_node = session.execute_read(self._find_trafficSpace_geometry, [id])
                        # print(coord_node)
                        # coords = coord_node[0]._properties
                        # print(coords)
                        for record in coord_node:
                            for key in list(record._properties.keys()):
                                # if only  a single digit number is in [] add a 0 in front
                                if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                    record._properties.pop(key)
                                # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                                if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                    new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                    record._properties[new_key] = record._properties[key]
                                    record._properties.pop(key)
                                
                                
                                # if re.search(r"\[\d\]", key):
                                #     new_key = key.replace("[", "[0")
                                #     record._properties[new_key] = record._properties[key]
                                #     record._properties.pop(key)
                                # make the if statement more general: depending on the number of digits in the array index if the largest number has 2 digits add a 0 in front of the single digit numbers, if the largest number has 3 digits add 00 in front of the single digit numbers
                                




                            # sort the coordinates by the key
                            # print(sorted(record._properties.items(), key=lambda x: x[0]))
                            sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                            # get the lat, lon and height values of the first point 
                            lat = float(sorted_coords[0][1])
                            lon = float(sorted_coords[1][1])
                            height = float(sorted_coords[2][1])

                            lat_2 = float(sorted_coords[-3][1])
                            lon_2 = float(sorted_coords[-2][1])
                            height_2 = float(sorted_coords[-1][1])
                            print("Point:  ",lat, lon, height)
                            print("Point 2:",lat_2, lon_2, height_2)
                            dist = euclidean_distance([lat, lon, height], [lat_2, lon_2, height_2])
                            print(f"Distance for {id}: \033[92m\033[1m{dist} \033[0m meters")
                        result = session.execute_write(self._insert_distance_weight, [id, dist])
            if query == "advanced_distance_weight":
                """Calculates the Eucleadian distance between all points along the TrafficSpace geometry to obtain a more accurate distance than the distance between the first and last point"""

                # find all sections
                result = session.execute_read(self._find_trafficSpace_ids, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                for record in result:
                    print(record)

                total_dist = 0
                trafficSpace_dists = []
                print("\n\033[96m[INFO]: Adding weights to 'SUCCESSOR_OF' relationships\033[0m")
                for id in tqdm(result):
                    # not all TrafficSpace objects have a gml UUID, therfore check if there is a string containing the UUID
                    # check if the id is a string and follows the UUID pattern
                    # if type(id) == str and is_valid_uuid(id):
                    dist = 0
                    if type(id) == str:
                        coord_node = session.execute_read(self._find_trafficSpace_geometry, [id])
                        # print(coord_node)
                        # coords = coord_node[0]._properties
                        # print(coords)
                        for record in coord_node:
                            for key in list(record._properties.keys()):
                                # if only  a single digit number is in [] add a 0 in front
                                if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                    record._properties.pop(key)
                                # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                                if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                    new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                    record._properties[new_key] = record._properties[key]
                                    record._properties.pop(key)
                            # sort the coordinates by the key
                            # print(sorted(record._properties.items(), key=lambda x: x[0]))
                            sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])

                            # create 3D points from the sorted coordinates
                            points=[]
                            for x, y, z in zip(sorted_coords[0::3], sorted_coords[1::3], sorted_coords[2::3]):
                                # print(float(x[1]), float(y[1]), float(z[1]))
                                points.append([float(x[1]), float(y[1]), float(z[1])])
                            
                            # calculate the distance between two following points and add it to the total distance
                            for i in range(len(points)-1):
                                dist += euclidean_distance(points[i], points[i+1])
                            print(f"\033[96m[INFO] Length of TrafficSpace object: {dist} meters \033[0m")

                            # # get the lat, lon and height values of the first point 
                            # lat = float(sorted_coords[0][1])
                            # lon = float(sorted_coords[1][1])
                            # height = float(sorted_coords[2][1])

                            # lat_2 = float(sorted_coords[-3][1])
                            # lon_2 = float(sorted_coords[-2][1])
                            # height_2 = float(sorted_coords[-1][1])
                            # print("Point:  ",lat, lon, height)
                            # print("Point 2:",lat_2, lon_2, height_2)
                            # dist = euclidean_distance([lat, lon, height], [lat_2, lon_2, height_2])
                            # print(f"Distance for {id}: \033[92m\033[1m{dist} \033[0m meters")
                            total_dist += dist
                            trafficSpace_dists.append(dist)
                        # result = session.execute_write(self._insert_distance_weight, [id, dist])
                print(f"\033[96m[INFO] Total length of all TrafficSpace objects: {total_dist} meters \033[0m")
                print(f"\033[96m[INFO] Minimum length of a TrafficSpace object: {min(trafficSpace_dists)} meters \033[0m")
                print(f"\033[96m[INFO] Maximum length of a TrafficSpace object: {max(trafficSpace_dists)} meters \033[0m")

            if query == "coords":
                """Add coordinates of first point to TrafficSpace elements"""
                # find all trafficSpace elements
                result = session.execute_read(self._find_trafficSpace_ids, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                for record in result:
                    print(record)
                
                print("\n\033[96m[INFO]: Adding coordinates to 'TrafficSpace' nodes\033[0m")
                for id in tqdm(result):
                    coord_node = session.execute_read(self._find_trafficSpace_geometry, [id])
                    for record in coord_node:
                        for key in list(record._properties.keys()):
                            # if only  a single digit number is in [] add a 0 in front
                            if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                record._properties.pop(key)
                            # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                            if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                record._properties[new_key] = record._properties[key]
                                record._properties.pop(key)
                        # sort the coordinates by the key
                        # print(sorted(record._properties.items(), key=lambda x: x[0]))
                        sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                        # get the lat, lon and height values of the first point 
                        lat = float(sorted_coords[0][1])
                        lon = float(sorted_coords[1][1])
                        height = float(sorted_coords[2][1])
                    result = session.execute_write(self._insert_TrafficSpace_coordinate_attributes, [id, lat, lon, height])

            if query == "inclination":
                """Add inclination between first and last point of TrafficSpace objects geometry to TrafficSpace nodes"""
                # find all trafficSpace elements
                result = session.execute_read(self._find_trafficSpace_ids, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                # for record in result:
                #     print(record)
                
                inclinations = []
                print("\n\033[96m[INFO]: Adding inclination to 'TrafficSpace' nodes\033[0m")
                for id in tqdm(result):
                    coord_node = session.execute_read(self._find_trafficSpace_geometry, [id])
                    for record in coord_node:
                        for key in list(record._properties.keys()):
                            # if only  a single digit number is in [] add a 0 in front
                            if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                record._properties.pop(key)
                            # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                            if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                record._properties[new_key] = record._properties[key]
                                record._properties.pop(key)
                        # sort the coordinates by the key
                        # print(sorted(record._properties.items(), key=lambda x: x[0]))
                        sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                        # get the lat, lon and height values of the first point 
                        # lat = float(sorted_coords[0][1])
                        # lon = float(sorted_coords[1][1])
                        # height = float(sorted_coords[2][1])

                        # create 3D point for the first and last point of the sorted coordinates
                        point1 = [float(sorted_coords[0][1]), float(sorted_coords[1][1]), float(sorted_coords[2][1])]
                        point2 = [float(sorted_coords[-3][1]), float(sorted_coords[-2][1]), float(sorted_coords[-1][1])]

                        # calculate the inclination between the two points
                        inclination = (point2[2] - point1[2]) / euclidean_distance(point1, point2)
                        inclinations.append(inclination)
                        print(f"\033[96m[INFO] Inclination of the TrafficSpace: {inclination*100} % \033[0m")
                print(f"\033[96m[INFO] Minimum inclination of the TrafficSpace: {min(inclinations)*100} % \033[0m")
                print(f"\033[96m[INFO] Maximum inclination of the TrafficSpace: {max(inclinations)*100} % \033[0m")

            if query == "width":
                """Add width of the road lanes to the TrafficSpace elements"""
                # find all trafficSpace elements
                result = session.execute_read(self._find_trafficSpace_ids, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                for record in result:
                    print(record)
                
                list_of_widths = []
                print("\n\033[96m[INFO]: Adding width to 'TrafficSpace' nodes\033[0m")
                for id in tqdm(result):
                    # find all trafficArea surfaceMember elements
                    surfaceMember_ids = session.execute_read(self._find_trafficArea_SurfaceMembers, [id])
                    print(f"\033[96m[INFO] Found {len(surfaceMember_ids)} surfaceMember elements\033[0m")

                    minimum_width = -1
                    for surfaceMember_id in surfaceMember_ids:
                        # find the geometry of the surfaceMember
                        coord_node = session.execute_read(self._find_trafficArea_geometry, [surfaceMember_id])
                                        
                        for record in coord_node:
                            for key in list(record._properties.keys()):
                                # if only  a single digit number is in [] add a 0 in front
                                if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                                    record._properties.pop(key)
                                # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                                if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                                    new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                                    record._properties[new_key] = record._properties[key]
                                    record._properties.pop(key)
                            # sort the coordinates by the key
                            # print(sorted(record._properties.items(), key=lambda x: x[0]))
                            sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                            # get the lat, lon and height values of the first point 
                            lat = float(sorted_coords[0][1])
                            lon = float(sorted_coords[1][1])
                            height = float(sorted_coords[2][1])

                            points=[]
                            # create 3D points from the sorted coordinates
                            for x, y, z in zip(sorted_coords[0::3], sorted_coords[1::3], sorted_coords[2::3]):
                                # print(float(x[1]), float(y[1]), float(z[1]))
                                points.append([float(x[1]), float(y[1]), float(z[1])])

                            # drop the last point because it is the same as the first point
                            points.pop()
                            # print(f"Number of points: {len(points)}")
                            
                            # calculate the minimum width of the road lane by comparing the distance between the first and last point of the surfaceMember and the second and second last point of the surfaceMember and so on
                            dist = -1
                            for i in range(len(points)//2):
                                temp_dist = euclidean_distance(points[i], points[-1-i])
                                if temp_dist < dist or dist == -1:
                                    dist = temp_dist
                            # print(f"Minimum width of the SurfaceMember: {dist} meters")

                            if minimum_width == -1 or dist < minimum_width:
                                minimum_width = dist
                    print(f"\033[96m[INFO] Minimum width of the TrafficSpace: {minimum_width} meters \033[0m")
                    list_of_widths.append(minimum_width)
                print(list_of_widths)
                # print minimum and maximum width of the list_of_widths
                # remove all -1 values from the list and count the number of -1 values
                print(f"\033[96m[INFO] Number of TrafficSpace elements without a width: {list_of_widths.count(-1)} \033[0m") # Those should be the TrafficSpace elements used for storing data but do not have a own citygml id
                list_of_widths = [x for x in list_of_widths if x != -1]
                print(f"\033[96m[INFO] Minimum width of the TrafficSpace: {min(list_of_widths)} meters \033[0m")
                print(f"\033[96m[INFO] Maximum width of the TrafficSpace: {max(list_of_widths)} meters \033[0m")


    def shortest_path_APOC_dijkstra(self, ids):
        print("Searching for the shortest_path using APOC Djikstra")
        with self.driver.session() as session:
            result = session.execute_read(self._find_shortest_path_apoc_djikstra, ids)
            
            # throw an error if the result is None
            if result is None:
                raise ValueError("\033[91m[ERROR] No shortest path could be found!\033[0m")
                


            path = result[0] # type: ignore           
            for node in path._nodes:
                print(node['id'])
            nodes = path.nodes
            print(f"\033[94mRouting over {len(nodes)} nodes with a lenght of {result[1]} meters!\033[0m") # type: ignore
            return [path._nodes, result[1]]


    def get_TrafficSpace_geometry_coordinates(self, uuid):
        with self.driver.session() as session:
            result = session.execute_read(self._get_coordinates_traffic_space, uuid)
            for record in result:
                # print(list(record._properties.keys()))
                # print()
                # for keys with a single digit number in [] add a 0 in front and save it as a new key
                for key in list(record._properties.keys()):
                    # if only  a single digit number is in [] add a 0 in front
                    if key == "ARRAY_MEMBER_TYPE" or key == "ARRAY_SIZE":
                        record._properties.pop(key)
                    # if the key contains the pattern "ARRAY_MEMBER[#number]" remove the text and only keep the number
                    if re.search(r"ARRAY_MEMBER\[[0-9]+\]", key):
                        new_key = int(key.replace("ARRAY_MEMBER[", "").replace("]", ""))
                        record._properties[new_key] = record._properties[key]
                        record._properties.pop(key)
                # sort the coordinates by the key
                # print(sorted(record._properties.items(), key=lambda x: x[0]))
                sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                # remove the first value of each tuple in the list
                sorted_coords = [x[1] for x in sorted_coords]
                # make points out of three consecutive values and convert them to floats
                sorted_points = [sorted_coords[i:i+3] for i in range(0, len(sorted_coords), 3)]
                sorted_points = [[float(x) for x in point] for point in sorted_points]
                return sorted_points
    def find(self, query):
        result = []
        with self.driver.session() as session:
            if query == "all":
                result = session.execute_read(self._find_all, "")
            if query == "num_nodes":
                result = session.execute_read(self._count_nodes, "")
            if query == "num_relations":
                result = session.execute_read(self._count_relations, "")
            if query == "labels":
                result = session.execute_read(self._get_labels, "")
            if query == "relationship_types":
                result = session.execute_read(self._get_relationship_types, "")
            if query == "startpoint":
                result = session.execute_read(self._get_startpoint, "")
            if query == "node":
                result = session.execute_read(self._find_node, 
                UUID_bottom_left)
                # print(result)
            if query == "shortest_path":
                print("Searching for the shortest_path")
                result = session.execute_read(self._find_shortest_path, [UUID_bottom_left, UUID_bottom_right])
                print(len(result))
                for record in result:
                    for node in record.nodes:
                        print(node)
                    # print("Found: {record}".format(record=record))
            if query == "apoc_djikstra":
                print("Searching for the shortest_path using APOC Djikstra")
                result = session.execute_read(self._find_shortest_path_apoc_djikstra, [UUID_bottom_left, UUID_bottom_right])
                
                path = result[0] # type: ignore
                nodes = path.nodes
                print(f"\033[94mRouting over {len(nodes)} nodes with a lenght of {result[1]} meters!\033[0m") # type: ignore
                
                for node in path._nodes:
                    print(node['id'])


            if query == "attributes":
                result = session.execute_read(self._find_attribute_nodes, [UUID_bottom_left])
                # print(result)
                for record in result:
                    print("=====\n",record.element_id.split(":")[-1])
                    result2 = session.execute_read(self._get_node_by_id, [record.element_id.split(":")[-1]])
                    for record2 in result2:
                        print(record2.id)
                        if "name" in record2._properties and "value" in record2._properties:
                            print(record2._properties["name"], ": ", record2._properties["value"])
                        elif "name" in record2._properties:
                            print(record2._properties["name"])
                            
                        else:
                            print(record2)
                        
                        # print(record2)
            if query == "coordinates":
                result = session.execute_read(self._get_coordinates_traffic_space, UUID_bottom_left)
                for record in result:
                    # print(list(record._properties.keys()))
                    # print()
                    # for keys with a single digit number in [] add a 0 in front and save it as a new key
                    for key in list(record._properties.keys()):
                        # if only  a single digit number is in [] add a 0 in front
                        if re.search(r"\[\d\]", key):
                            new_key = key.replace("[", "[0")
                            record._properties[new_key] = record._properties[key]
                            record._properties.pop(key)
                    # sort the coordinates by the key
                    print(sorted(record._properties.items(), key=lambda x: x[0]))
                    sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
                    # get the lat and lon values of the first coordinate
                    lat = sorted_coords[0][1]
                    lon = sorted_coords[1][1]
                    height = sorted_coords[2][1]
                    print("Point:",lat, lon, height)

            if query == "lanes_for_road_segment":
                segment_id = "1010000"
                result = session.execute_read(self._get_lanes_for_road_segment, segment_id)
            if query == "lane_type_for_road_segment":
                segment_id = "1010000"
                lane_type = ["DRIVING","SIDEWALK","BIKING", ][0]
                result = session.execute_read(self._get_lanes_by_type_for_road_segment, [segment_id, lane_type])
            if query == "specific_lane_for_road_segment":
                segment_id = "1010000"
                lane_section_id = "0"
                lane_id = "1"
                result = session.execute_read(self._get_specific_lane_for_road_segment, [segment_id, lane_section_id, lane_id])

           
            # print the number of results in blue to the console
            print("\n\033[94mFound {num} results:\033[0m".format(num=len(result))) # type: ignore


            for record in result: # type: ignore
                # print found in green to make it easier to spot in the console
                print("\n\033[92mFound:\033[0m {record}".format(record=record))
                



    # # transaction
    # def transaction(self, tx, variables):
    #     # TODO: check if query is a string, probably there are more checks needed, probably the variables need to be assigned individually
    #     result = tx.run(self.query, variables)       
    #     for record in result:
    #         print(record['n'])
    #     return result

    # # function to READ from the database
    # def read(self, query, vars):
    #     self.query = query
    #     with self.driver.session() as session:
    #         response = session.execute_read(self.transaction, vars)
    #         results = []
    #         for record in response:
    #             results.append(record)
    #         return results

    # # function to WRITE to the database
    # def write(self, query, vars):
    #     with self.driver.session() as session:
    #         results = session.write_transaction(self.transaction, query, vars)
    #         return results

# # Test
# # main method
# if __name__ == '__main__':
#     uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
#     # create instance of Neo4jInteractor
#     print("Connecting to Neo4j...")
#     neo4j_interactor = Neo4jInteractor(uri, username, password)
#     # test read
#     print("Interaction with Neo4j DB...")
#     neo4j_interactor.find("apoc_djikstra")
#     # query = "MATCH (n:%)-[r:successors|predecessors]->() RETURN n as test_nodes limit 2;"
#     # vars = ""
#     # results = neo4j_interactor.read(query, vars)
#     # for result in results:
#     #     print(result)
    
#     # test write
#     # query = "CREATE (n:Test {name: $name, title: $title}) RETURN n.name, n.title"
#     # vars = {"name": "Test", "title": "Test"}
#     # results = neo4j_interactor.write(query, vars)
#     # for result in results:
#     #     print(result)
#     # close connection
#     neo4j_interactor.close()
#     print("Done")


# TODO: Aufbereiten der Richtungsunabhängigkeit für SIDEWALK elemente. Hier können Fußgänger die Straße in beide Richtungen nutzen.
# TODO: Hinzufügen von Überquerungsmöglichkeiten für Fußgänger und Fahrradfahrer
# TODO: Nutzen von Informationen aus CityFurniture Objekten
# - Geschwindigkeitsbegrenzungen
# - Ampeln und Stoppschilder für Wartezeiten
# TODO: Füge die Gewichte in die Datenbank ein
# - Genauere Berechnung der Länge der Straßenabschnitte
# - Berechnung der Steigung der Straßenabschnitte
# - Berechnung der Breite der Straßenabschnitte
# ? Berechnen der Straßenabschnittsbreite muss eventuell nochmals überdacht werden!
# TODO: Finde einen Weg Wartezeiten zu berücksichtigen
# TODO: Sperren von Straßenabschnitten
# TODO: Einführen von Umstiegspunkten zwischen Transportmitteln!
# - Wie könnten Switch nodes automatisch ermittelt werden?
# - Wie können Switch nodes automatisch erzeugt werden?
# - Beispielhafte manuelle Ergänzung des Datensatzes in der Graphdatenbank
# TODO: Tests mit größerem Datensatz