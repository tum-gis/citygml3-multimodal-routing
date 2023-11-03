# Test script for the Neo4jPreProcessor class

# Imports
import datetime
import json

from constants import password, username
from interactor4neo4j import Neo4jPreProcessor

# Constants
uri = "bolt://localhost:7687"

# # Test metadata retrieval
# start = datetime.datetime.now()
# print(start)
# preprocessor = Neo4jPreProcessor(uri, username, password)
# preprocessor.get_metadata_information()
# preprocessor.close()
# print(f"Metadata retrieval took: {datetime.datetime.now() - start}")



# Test Functions
def default_preprocessing():
    # Stop the time for the pre-processing
    now = datetime.datetime.now()
    preprocessor = Neo4jPreProcessor(uri, username, password)
    # Adding relationships
    # ! Call these functions only once to prepare the database!
    preprocessor.create("predecessor_shortcut")
    preprocessor.create("successor_shortcut")
    preprocessor.create("lane_changes")
    preprocessor.create("transport_mode_switch") # TODO: Check, not working anymore with new dataset
    # Adding properties
    # Setting the transportation type 
    # (can be run multiple times to update the values in the database) 
    # but most likely only needed when the routing network changes
    preprocessor.create("transportation_type")
    # add bidirectional successor relationships
    # SUCCESSOR_OF relationship and transportation type must be set before!
    # preprocessor.create("bidirectional_successor_relationship")
    # REMOVE SUCCESSOR_OF_2 relationship from the BIDIRECTIONAL successor connections as it is not needed anymore due to an update in the converter software
    preprocessor.insert("speed_limits", [])
    # Can be called multiple times to update the values in the database
    # Useful if dynamic weights are used in the future
    preprocessor.create("weight_attributes")
    preprocessor.insert("coords", [])
    # Adding routing weights
    # TODO: Calculate routing weights using the added weight information, e.g., traversal time = distance / speed limit 

    # The reversed successor relationship for SIDEWALK elements is added last as it copies the weight information from the SUCCESSOR_OF relationship. Only a change in the inclination of the SIDEWALK element is needed to update the weight information. This also applies to all weights derived using the weight information.
    preprocessor.insert("add_bidirectional_successor_sidewalk_relationship", [])

    preprocessor.close()
    # Stop the time for the pre-processing
    print(f"Pre-Processing took: {datetime.datetime.now() - now}")

def parking_garage_dataset_preprocessing():
    print("Pre-processing the parking garage dataset")
    # Stop the time for the pre-processing
    now = datetime.datetime.now()
    preprocessor = Neo4jPreProcessor(uri, username, password)
    # Adding relationships
    # ! Call these functions only once to prepare the database!
    preprocessor.create("predecessor_shortcut")
    preprocessor.create("successor_shortcut")
    preprocessor.create("lane_changes")
    preprocessor.create("transport_mode_switch")

    # This query must be added to link the incoming driving lane correctly to the parking lot entrance
    """MATCH (n WHERE n.id="UUID_8e583928-2103-3512-a1be-44d8631f19ad")
    WITH n MATCH (m WHERE m.id="TS_section12")
    CREATE (n)-[:SUCCESSOR_OF]->(m)
    RETURN n,m"""
    # AND a connection from the SIDEWALK element to the parking lot entrance
    """MATCH (n WHERE n.id="UUID_9ca0564b-b53d-3bf9-af35-b25ec3d3e7b0")
    WITH n MATCH (m WHERE m.id="TS_section12")
    CREATE (n)-[:SUCCESSOR_OF]->(m)
    RETURN n,m"""
    # Hardcoded for the parking garage dataset
    preprocessor.insert_parking_garage_entrance_connection()
    # Also for trafficDirection="both" a second relationship for successor_of and predecessor_of must be added
    """MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:PREDECESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="both") CREATE (a)-[:SUCCESSOR_OF]->(b);""" # This is covered by the default create(successorShortcut) function call, however the predecessor relationship is not added as it is not used in the routing network!
    # AND for predecessor_of
    """MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="both") CREATE (a)-[:PREDECESSOR_OF]->(b);"""


    # preprocessor.insert("coords", []) # TODO: Needs updated version for volumetric TrafficSpace elements
    preprocessor.create("transportation_type")
    preprocessor.insert("add_bidirectional_successor_sidewalk_relationship", []) # TODO: probably needs some updates to not add weight properties if there are none available at successor_of relationship
    preprocessor.close()
    # Stop the time for the pre-processing
    print(f"Pre-Processing took: {datetime.datetime.now() - now}")

# TODO: RUN ONCE TO PREPARE THE DATABASE
if __name__ == "__main__":
    # Start time of the script
    print(datetime.datetime.now())
    # Use the default pre-processing
    default_preprocessing()
    # OR 
    # Pre-processing of the parking garage dataset
    # parking_garage_dataset_preprocessing()
    
    

# # test the output of the traffic sign information
# def test_traffic_sign_info():
#     # load the traffic sign codes from the trafficSignCodes.json file
#     with open('trafficSignCodes.json', 'r', encoding='utf-8') as traffic_sign_codes_file:
#         traffic_sign_codes = json.load(traffic_sign_codes_file)
#     # print(traffic_sign_codes)
#     preprocessor = Neo4jPreProcessor(uri, username, password)
#     traffic_sign_infos = preprocessor.find("traffic_sign_info", [])
#     for traffic_sign_info in traffic_sign_infos:
#         # Find the traffic sign code in the traffic_sign_codes.json file
#         traffic_sign_code = traffic_sign_info[1]._properties['value']
#         traffic_sign_subtype = traffic_sign_info[2]._properties['value']
#         traffic_sign_value = traffic_sign_info[3]._properties['value']
        
#         # use a combination of traffic_sign_code and traffic_sign_subtype to find the traffic sign information as the key in the traffic_sign_codes.json file with the format "traffic_sign_code-traffic_sign_subtype"
#         if traffic_sign_subtype != '-1':
#             if traffic_sign_code == '262' or traffic_sign_code == '263' or traffic_sign_code == '264' or traffic_sign_code == '265' or traffic_sign_code == '266':
#                 traffic_sign_info_key = f"{traffic_sign_code}-"
#             else:
#                 traffic_sign_info_key = f"{traffic_sign_code}-{traffic_sign_subtype}"
#         else:
#             traffic_sign_info_key = f"{traffic_sign_code}"
#         print(traffic_sign_info_key)
#         try:
#             if traffic_sign_code == '262' or traffic_sign_code == '263' or traffic_sign_code == '264' or traffic_sign_code == '265' or traffic_sign_code == '266':
#                 # print in blue if the traffic sign code is found in the traffic_sign_codes.json file
#                 print(f"\033[94m{traffic_sign_codes[traffic_sign_info_key]} = {traffic_sign_subtype}\033[0m")
#             elif traffic_sign_code == '274':
#                 # print in yellow if the traffic sign code is found in the traffic_sign_codes.json file
#                 print(f"\033[93m{traffic_sign_codes[traffic_sign_info_key]} = {traffic_sign_value}\033[0m")            
#             else:
#                 print(traffic_sign_codes[traffic_sign_info_key])
#         except KeyError:
#             # print in red if the traffic sign code is not found in the traffic_sign_codes.json file
#             print("\033[91m" + f"Traffic sign code {traffic_sign_info_key} not found in traffic sign codes" + "\033[0m")
#     preprocessor.close()
# test_traffic_sign_info()

