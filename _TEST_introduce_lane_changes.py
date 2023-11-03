# 1. Get all Sections in the graph database: MATCH (n:`org.citygml4j.core.model.transportation.Section` ) RETURN n;
# 2. For each Section, get all trafficSpaces (Connection from n: -[r:trafficSpaces]-()-[r:elementData]-()-[r:ARRAY_MEMBER]-()-[object])
# This returns a list of all trafficSpaces in the section
# 3. For each trafficSpace, get the corresponding trafficArea
# The connection starting from the trafficSpace is: -[r:boundaries]-()-[r:elementData]-()-[r:ARRAY_MEMBER]-()-[object]
# The TrafficArea object has the needed lane information in its attributes. Needed are the attributes: 
# - identifier_laneId
# - identifier_laneSectionId
# - and potentially the attribute: identifier_roadId

# ATTENTION:
# - identifier_lane_Id <--> identifier_from_laneId & identifier_to_laneId
# - identifier_laneSectionId <--> identifier_from_laneSectionId & identifier_to_laneSectionId
# - identifier_roadId <--> identifier_from_roadId & identifier_to_roadId

# ATTENTION: The MISSING identifier_laneId values are used for the "positioning" of the AuxiliaryTrafficArea objects (markings, etc.).

# 4. For each laneSectionId search neighboring lanes via the laneID and the type of the lane (DRIVING, SIDEWALK, BIKING)
# 4.1 If two lanes are found that have the same type and are just one laneID apart, then they are neighbors
# 4.2 Introduce a relationship between the two lanes called 'NEIGHBOURING_LANE' if it does not exist yet (to avoid duplicates) this relationship is undirected and can also have attributes.
# (5. Idea of connecting lanes of different types: If the total number of lanes changes, the lane type which is added or removed could be connected to the neighboring lane of another type. This would introduce a capabitity to change transportation modes for multi-modal routing. Here, the relationship 'NEIGHBOURING_LANE' could receive an attribute indicating the transportation mode change or a new relationship could be introduced, e.g. 'TRANSPORTATION_MODE_CHANGE'.)
# (5.1 First step would be to find out where the new lane was added or removed by checking the lineIds and the order of their types. )

# ========================================================================================================
# Implementation
# ========================================================================================================
# Imports
from neo4j import GraphDatabase
from constants import username, password

from tqdm import tqdm

# Class for interacting with Neo4j DB
class Neo4jInteractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

# 1. Get all Sections in the graph database: MATCH (n:`org.citygml4j.core.model.transportation.Section` ) RETURN n;
    @staticmethod
    def _find_sections(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.Section` ) RETURN n;")
        return [record["n"] for record in result]
# 2. For each Section, get all trafficSpaces (Connection from n: -[r:trafficSpaces]-()-[r:elementData]-()-[r:ARRAY_MEMBER]-()-[object])
    @staticmethod
    def _find_traffic_spaces(tx, vars):
        result = tx.run("MATCH (n)-[r:trafficSpaces]-()-[r2:elementData]-()-[r3:ARRAY_MEMBER]-()-[r4:object]-(ts) WHERE ID(n)=$sectionID RETURN ts;", sectionID=vars[0])
        return [record["ts"] for record in result]
# 3. For each trafficSpace, get the corresponding trafficArea (Connection starting from the trafficSpace is: -[r:boundaries]-()-[r:elementData]-()-[r:ARRAY_MEMBER]-()-[object])
    @staticmethod
    def _find_traffic_area(tx, vars):
        result = tx.run("MATCH (n WHERE n.id=$trafficSpaceID)-[r:boundaries]-()-[r2:elementData]-()-[r3:ARRAY_MEMBER]-()-[r4:object]-(ta) RETURN ta;", trafficSpaceID=vars[0])
        return [record["ta"] for record in result]
# 3.1 get the lane information from the trafficArea: identifier_laneId, identifier_laneSectionId, identifier_roadId attributes
# via:
# -[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n:`org.citygml4j.core.model.generics.IntAttribute` WHERE n.name ="identifier_laneSectionId")
# -[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n4:`org.citygml4j.core.model.generics.IntAttribute` WHERE n4.name ="identifier_laneId")
# -[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n2:`org.citygml4j.core.model.generics.StringAttribute` WHERE n2.name ="identifier_roadId"
    @staticmethod
    def _find_lane_information(tx, vars):
        # Cyper query to get the lane information by the trafficArea UUID
        # MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` WHERE n.id=$trafficAreaID)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(lsID:`org.citygml4j.core.model.generics.IntAttribute` WHERE lsID.name ="identifier_laneSectionId") WITH n, lsID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(roadID:`org.citygml4j.core.model.generics.StringAttribute` WHERE roadID.name ="identifier_roadId") WITH n, roadID, lsID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(laneID:`org.citygml4j.core.model.generics.IntAttribute` WHERE laneID.name ="identifier_laneId") RETURN roadID.value as roadID, lsID.value as laneSectionID, laneID.value as laneID;
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` WHERE n.id=$trafficAreaID)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(roadID:`org.citygml4j.core.model.generics.StringAttribute` WHERE roadID.name ="identifier_roadId") WITH n, roadID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(lsID:`org.citygml4j.core.model.generics.IntAttribute` WHERE lsID.name ="identifier_laneSectionId") WITH n, roadID, lsID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(laneID:`org.citygml4j.core.model.generics.IntAttribute` WHERE laneID.name ="identifier_laneId") WITH n, roadID, lsID, laneID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(laneType:`org.citygml4j.core.model.generics.StringAttribute` WHERE laneType.name="opendrive_lane_type") RETURN roadID.value as roadID, lsID.value as laneSectionID, laneID.value as laneID, laneType.value as laneType;', trafficAreaID=vars[0])
        for record in result:
            if len([record['roadID'], record['laneSectionID'], record['laneID'], record['laneType']]) == 4:
                return [record['roadID'], int(record['laneSectionID']), int(record['laneID']), record['laneType']]
            else:
                return []
         

    def find(self, query, vars=[]):
        with self.driver.session() as session:
            if query == "sections":
                result = session.execute_read(self._find_sections, vars)
                return [int(record.element_id.split(":")[-1]) for record in result]
            if query == "trafficSpaces":
                result = session.execute_read(self._find_traffic_spaces, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                return [record["id"] for record in result]
            if query == "trafficArea":
                result = session.execute_read(self._find_traffic_area, vars)
                return [record["id"] for record in result]
            if query == "laneInformation":
                result = session.execute_read(self._find_lane_information, vars)
                return result
            
            for record in result:
                # print found in green to make it easier to spot in the console
                print("\n\033[92mFound:\033[0m {record}".format(record=record))
    
    @staticmethod
    def _find_lane_nodes(tx, vars):

        first_id = vars[0][0]
        second_id = vars[1][0]
        # print(f"\n-------------------------------------\nFirst ID: {first_id}, Second ID: {second_id}\n-------------------------------------")
        result = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) RETURN n2,m2;', id1=first_id, id2=second_id)
        for record in result:
            if len([record['n2'], record['m2']]) == 2:
                return [record['n2'], record['m2']]
            else:
                print("\n\033[91m[ERROR]: Could not find the lane nodes pair\033[0m")

    @staticmethod
    def _insert_lane_changes(tx, vars):
        # print(vars)
        # result = tx.run('')

        # Using the !!! trafficAreaID !!! and set the lane changes relationship for the trafficSpaces nodes in one query
        first_id = vars[0][0]
        second_id = vars[1][0]
        result = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) WITH n2,m2 CREATE(n2)-[r:NEIGHBOURS_LANE]->(m2) RETURN r;', id1=first_id, id2=second_id)

        result2 = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) WITH n2,m2 CREATE(n2)-[r:NEIGHBOURS_LANE]->(m2) RETURN r;', id1=second_id, id2=first_id)

    def insert(self, query, vars):
        with self.driver.session() as session:
            if query == "laneChanges":
                # first read the DB to see if the node selection functions properly
                # print("Testing the query")
                # result = session.execute_read(self._find_lane_nodes, vars)
                # traffic_spaces_ids = [record["id"] for record in result]
                # for record in result:
                #     print("\n\033[92mFound:\033[0m {record}".format(record=record))
                # print("\n=====================================\nInserting the lane changes relationship\n=====================================\n")
                # result = session.execute_write(self._insert_lane_changes, traffic_spaces_ids)
                
                print("\n\033[96m[INFO]: Inserting the lane changes relationship: 'NEIGHBOURS_LANE'\033[0m")
                result = session.execute_write(self._insert_lane_changes, vars)

                



if __name__ == '__main__':
    uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
    # create instance of Neo4jInteractor
    print("Connecting to Neo4j...")
    neo4j_interactor = Neo4jInteractor(uri, username, password)
    print("Interaction with Neo4j DB...")
    # find all sections
    sections = neo4j_interactor.find("sections")
    # find all trafficSpaces for each section
    for section_id in tqdm(sections):
        print(f"\nSection ID: {section_id}")
        section_traffic_spaces = neo4j_interactor.find("trafficSpaces", [section_id])
        # print("=====================================\nTraffic Spaces:\n=====================================")
        # print(section_traffic_spaces)
        # print("=====================================")
        # find all trafficAreas for each trafficSpace
        traffic_areas = []
        traffic_areas += [neo4j_interactor.find("trafficArea", [traffic_space_id]) for traffic_space_id in section_traffic_spaces]
        tmp = []
        for traffic_areas_id in traffic_areas:
            tmp += traffic_areas_id
        traffic_areas = tmp
        # print("Traffic Areas:\n=====================================\033[93m")
        # print(traffic_areas)
        # print("\033[0m")
        # print("=====================================")
        section_lane_information = []
        # find lane information for each trafficArea
        # print("Lane Information:")
        for traffic_area_id in traffic_areas:
            lane_information = neo4j_interactor.find("laneInformation", [traffic_area_id])
            if type(lane_information) == list:
                lane_information.insert(0, traffic_area_id)
                section_lane_information.append(lane_information)
                
                
            # print(lane_information)
        # print("=====================================")

        # print in blue to make it easier to spot in the console
        # print(f"\033[94m {section_lane_information}\033[0m")

        # print("\n=====================================\nSorted lane information with potential neighbours:\n=====================================\n")

        s = sorted(section_lane_information, key = lambda x: (x[1], x[2], x[3]))
        neighbouring_lanes_same_type = []
        for i, el in enumerate(s):
            
            if i < len(s)-1 and el[1] == s[i+1][1] and el[2] == s[i+1][2] and el[4] == s[i+1][4] and ((el[3] < 0 and s[i+1][3] <0) or (el[3] > 0 and s[i+1][3] > 0)):
                # print("\033[92m" + str(el) + "\033[0m")
                neighbouring_lanes_same_type.append(el)
            elif  i > 0 and el[1] == s[i-1][1] and el[2] == s[i-1][2] and el[4] == s[i-1][4] and ((el[3] < 0 and s[i-1][3] <0) or (el[3] > 0 and s[i-1][3] > 0)):
                # print("\033[92m" + str(el) + "\033[0m")
                neighbouring_lanes_same_type.append(el)
            else:
                # print(el)
                pass
            
        print("\n=====================================\nNeighbouring lanes:\n=====================================\n")
        lanes_to_connect = []
        neighbouring_lanes = []
        neighbouring_lanes_pos = []
        neighbouring_lanes_neg = []
        for i, el in enumerate(neighbouring_lanes_same_type):
            if el[3] < 0:
                print("\033[94m" + str(el) + "\033[0m")
                if i < len(neighbouring_lanes_same_type)-1 and el[1] == neighbouring_lanes_same_type[i+1][1] and el[2] == neighbouring_lanes_same_type[i+1][2] and el[4] == neighbouring_lanes_same_type[i+1][4]:
                    neighbouring_lanes.append(el)
                    # neighbouring_lanes_neg.append(el)
                elif  i > 0 and el[1] == neighbouring_lanes_same_type[i-1][1] and el[2] == neighbouring_lanes_same_type[i-1][2] and el[4] == neighbouring_lanes_same_type[i-1][4]:
                    neighbouring_lanes.append(el)
                    # neighbouring_lanes_neg.append(el)
                    # neighbouring_lanes.append(neighbouring_lanes_neg)
                    lanes_to_connect.append(neighbouring_lanes)
                    # lanes_to_connect.append(neighbouring_lanes_neg)
                    neighbouring_lanes = []
                    # neighbouring_lanes_neg = []
            if el[3] > 0:
                print("\033[92m" + str(el) + "\033[0m")
                
                if i < len(neighbouring_lanes_same_type)-1 and el[1] == neighbouring_lanes_same_type[i+1][1] and el[2] == neighbouring_lanes_same_type[i+1][2] and el[4] == neighbouring_lanes_same_type[i+1][4]:
                    neighbouring_lanes.append(el)
                    # neighbouring_lanes_pos.append(el)
                elif  i > 0 and el[1] == neighbouring_lanes_same_type[i-1][1] and el[2] == neighbouring_lanes_same_type[i-1][2] and el[4] == neighbouring_lanes_same_type[i-1][4]:
                    neighbouring_lanes.append(el)
                    # neighbouring_lanes_pos.append(el)
                    lanes_to_connect.append(neighbouring_lanes)
                    # lanes_to_connect.append(neighbouring_lanes_pos)
                    # neighbouring_lanes.append(neighbouring_lanes_pos)
                    neighbouring_lanes = []
                    # neighbouring_lanes_pos = []
        # lanes_to_connect.append(neighbouring_lanes_neg)
        # lanes_to_connect.append(neighbouring_lanes_pos)
            
        # print("\n=====================================\nLanes to connect:\n=====================================\n")
        # print(lanes_to_connect)

        lanes_to_connect_by_direction = []
        for block in lanes_to_connect:
            positive_lanes = []
            negative_lanes = []
            for el in block:
                if el[3] < 0:
                    # copy to new negative list
                    negative_lanes.append(el)
                if el[3] > 0:
                    # copy to new positive list
                    positive_lanes.append(el)
            # to have a better overview of the lanes that should be connected (negative and positive lanes)
            # lanes_to_connect_by_direction.append([negative_lanes, positive_lanes])

            # to have all pairs of lanes that should be connected in one list
            lanes_to_connect_by_direction.append(negative_lanes)
            lanes_to_connect_by_direction.append(positive_lanes)
        
        # print("\n=====================================\nLanes to connect by direction:\n=====================================\n")
        # print(lanes_to_connect_by_direction)
        print("\n=====================================\nCreating relationships between lanes:\n=====================================\n")   
        for block in lanes_to_connect_by_direction:
            if len(block) == 2:
                neo4j_interactor.insert("laneChanges", block)
            elif len(block) > 2:
                for i in range(len(block)-1):
                    neo4j_interactor.insert("laneChanges", [block[i], block[i+1]])
            
                
            
       

    neo4j_interactor.close()
    print("Done")