# 1. Get a list of all TrafficSpace objects
# 2. Calculate the distance between the first and last point of each TrafficSpace objects geometry
# 3. Add the distance as a weight to the TrafficSpace object relationship "SUCCESSOR_OF" to the next TrafficSpace object

# =================================================================================

# Imports
from neo4j import GraphDatabase
from constants import username, password
import re
import numpy as np
import open3d as o3d
import utm
from geopy.geocoders import Nominatim


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
    
    # @staticmethod
    # def _insert_distance_weight(tx, vars):
    #     result = tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.segment_length=$weight RETURN a, b;', id=vars[0], weight=vars[1])
    
    def find_all_coordinates(self):
        with self.driver.session() as session:
            result = session.execute_read(self._find_trafficSpace_ids, vars)
            print(f"Number of TrafficSpace elements: {len(result)}")
            for record in result:
                print(record)
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
                        coord_list.append(np.array([lat, lon, height]))
                        coord_list.append(np.array([lat_2, lon_2, height_2]))  
                        id_list.append(id)
                        id_list.append(id)

            return coord_list, id_list                                        

if __name__ == '__main__':

    address = "Ingolstadt, Germany"
    # get the coordinates of the address
    geolocator = Nominatim(user_agent="TUM_GEOCODING")
    location = geolocator.geocode(address)
    print(location.address)
    print((location.latitude, location.longitude))
    # get UTM height for coordinates



    # point1 = [678044.3748199228, 5405267.015088416, 372.71302756703204]
    coords = utm.from_latlon(location.latitude, location.longitude)

    # point1 = [691602.17641492, 5334783.3397872, 512.0]
    point1 = [coords[0], coords[1], 0.0]
    # point1 = [678014, 5.40525e+06, 372.015]

    # point2 = [678066.2158401045, 5405269.0334091475, 372.80501766679157]
    # create numpy ndarray from list
    point1 = np.array(point1)

    # get the start and end point of every TrafficSpace object
    uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
    # create instance of Neo4jInteractor
    print("Connecting to Neo4j...")
    neo4j_interactor = Neo4jInteractor(uri, username, password)
    print("Interaction with Neo4j DB...")
    # find all sections
    coordinate_list, id_list=neo4j_interactor.find_all_coordinates()
    print(f"Number of points: {len(coordinate_list)}")


    # create a random list of numpy ndarrays with 3 elements
    # points = np.random.rand(100, 3)
    # print(points)
    

    # add points to open3d point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(coordinate_list) 
    
    # add points with attributes to open3d point cloud

    # print bounding box of point cloud
    print("Bounding box of point cloud:")
    print(pcd.get_axis_aligned_bounding_box())
    # show point cloud
    # o3d.visualization.draw_geometries([pcd])
    # o3d.visualization.draw([pcd])

    # create kdTree from point cloud
    kdTree = o3d.geometry.KDTreeFlann(pcd)
    # find the nearest neighbor of point1
    [k, idx, _] = kdTree.search_knn_vector_3d(point1, 1)
    print(f"K: {k}, Index: {idx}")
    # print the coordinates of the nearest neighbor
    print(f"The nearest node is: {coordinate_list[idx[0]]}, the corresponding TrafficSpace object has the \nID: \033[92m {id_list[idx[0]]} \033[0m")
    print(f"Coordinates of the point in lat, lon: {utm.to_latlon(coordinate_list[idx[0]][0], coordinate_list[idx[0]][1], 32, 'U')}")
    
    # create a second point cloud with the nearest point only, in a different color
    pcd_highlight_pnts = o3d.geometry.PointCloud()
    pcd_highlight_pnts.points = o3d.utility.Vector3dVector(np.asarray(pcd.points)[idx])
    pcd_highlight_pnts.colors = o3d.utility.Vector3dVector(np.asarray(pcd.points)[idx])
    o3d.visualization.draw([pcd, pcd_highlight_pnts])
    
    # # change the color of the nearest neighbor
    # np.asarray(pcd.colors)[idx[1:], :] = [0, 0.5, 0]
    # # np.asarray(pcd.colors)[idx[1:]] = [0, 1, 0]
    # print("Displaying the final point cloud ...\n")
    # o3d.visualization.draw([pcd])
   