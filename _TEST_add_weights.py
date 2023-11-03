# 1. Get a list of all TrafficSpace objects
# 2. Calculate the distance between the first and last point of each TrafficSpace objects geometry
# 3. Add the distance as a weight to the TrafficSpace object relationship "SUCCESSOR_OF" to the next TrafficSpace object

# =================================================================================

# Imports
from neo4j import GraphDatabase
from constants import username, password
import re

from tqdm import tqdm
import uuid
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

# Class for interacting with Neo4j DB
class Neo4jInteractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()
# 1. Get all Sections in the graph database: MATCH (n:`org.citygml4j.core.model.transportation.Section` ) RETURN n;
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
                            
                            




if __name__ == '__main__':
    # point1 = [678044.3748199228, 5405267.015088416, 372.71302756703204]
    # point2 = [678066.2158401045, 5405269.0334091475, 372.80501766679157]
    # # CHECK THE COORDINATE SYSTEM IN ORDER TO CALCULATE THE DISTANCE 
    # # Here it is in EPSG:32632 - WGS 84 / UTM zone 32N which is in meters
    # print(f"Euclidean distance between {point1} and {point2} is {euclidean_distance(point1, point2)} meters")
    

    uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
    # create instance of Neo4jInteractor
    print("Connecting to Neo4j...")
    neo4j_interactor = Neo4jInteractor(uri, username, password)
    print("Interaction with Neo4j DB...")
    # print("[INFO] Adding distance weights to 'SUCCESSOR_OF' relationships")
    # # add distance weights to the relationships
    # neo4j_interactor.insert("distance_weight")
    print("[INFO] Adding advanced distance weights to 'SUCCESSOR_OF' relationships")
    # add distance weights to the relationships
    neo4j_interactor.insert("advanced_distance_weight")

    # print("[INFO] Adding coordinates to 'TrafficSpace' nodes")
    # # add coordinates to the TrafficSpace nodes
    # neo4j_interactor.insert("coords")

    # print("\n\033[96m[INFO] Adding width to 'TrafficSpace' nodes \033[0m")
    # # add width to the TrafficSpace nodes
    # neo4j_interactor.insert("width")

    # print("[INFO] Adding inclination to 'TrafficSpace' nodes")
    # # add inclination to the TrafficSpace nodes
    # neo4j_interactor.insert("inclination")
