myquery = '''MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_lane_type" and m.value="PARKING") 
WITH n, m
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(l WHERE l.name="identifier_roadId")
WITH n, m, l 
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(k WHERE k.name="identifier_laneSectionId")
WITH n,m, l,k
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(j WHERE j.name="identifier_laneId")
WITH n,m, l,k,j
MATCH (a:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="identifier_roadId" and b.value=l.value)
MATCH(a:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="identifier_laneSectionId" and c.value=k.value)
MATCH(a:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="identifier_laneId")
RETURN n, a, b.value as road_id, c.value as lane_segment_id,  j.value as original_lane_id, d.value as possible_lane_neighbour_id'''

from datetime import datetime

from neo4j import GraphDatabase
from tqdm import tqdm

from constants import password, username


class Neo4jInteractor:
    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    @staticmethod
    def _find_trafficAreas_to_PARKING_AuxiliaryAreas(tx, vars):
        query = myquery
        result = tx.run(query, vars)
        output = []
        for record in result:
            output.append([record["n"], record["a"], record["road_id"], record["lane_segment_id"], record["original_lane_id"], record["possible_lane_neighbour_id"]])
        return output
    
    @staticmethod
    def _insert_SWITCH_TO_relation(tx, vars):
        query1 = '''
        MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea` WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(a)
        WITH a
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea` WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(b)
        WITH a, b
        CREATE (a)-[:SWITCH_TO]->(b);
        '''
        query2 = '''
        MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea` WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(a)
        WITH a
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea` WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(b)
        WITH a, b
        CREATE (b)-[:SWITCH_TO_PARKING]->(a);
        '''
        tx.run(query1, id1=vars[0], id2=vars[1])
        tx.run(query2, id1=vars[0], id2=vars[1])

    def insert_SWITCH_TO_relation(self, node1_id, node2_id):
        with self.driver.session() as session:
            session.execute_write(self._insert_SWITCH_TO_relation, [node1_id, node2_id])
        
    def find_trafficAreas_to_PARKING_AuxiliaryAreas(self):
        with self.driver.session() as session:
            result = session.execute_read(self._find_trafficAreas_to_PARKING_AuxiliaryAreas, {})
            for record in result:
                record[2:6] = [int(x) for x in record[2:6]]
                print(record)

            

            # sort the result by the second then third and then fourth column
            result = sorted(result, key=lambda x: (x[2], x[3], x[4]))

            segments = []
            temp_segments = []
            for idx, record in tqdm(enumerate(result)):
                
                if idx == len(result)-1:
                    break

                if record[2] == result[idx+1][2] and record[3] == result[idx+1][3] and record[4] == result[idx+1][4]:
                    temp_segments.append(record)
                if record[2] != result[idx+1][2] or record[3] != result[idx+1][3] or record[4] != result[idx+1][4]:
                    temp_segments.append(record)
                    segments.append(temp_segments)
                    temp_segments = []

            print(segments)
            for segment in segments:
                
                if len(segment) == 1:
                    print("Only one element in segment")
                    print(segment)
                    # Add a relationship between the corresponding TrafficSpaces to the two nodes
                    print("[INFO] Add relationship between the two nodes")
                    self.insert_SWITCH_TO_relation(segment[0][0]._properties['id'], segment[0][1]._properties['id'])
                    continue
                else:
                    # find the closest line using the original_lane_id [index 4] and the possible_lane_neighbour_id [index 5]
                    nearest_lower = None
                    nearest_higher = None
                    for temp_lines in segment:
                        if nearest_lower is None:
                            if temp_lines[5] < temp_lines[4]:
                                nearest_lower = temp_lines
                        else:
                            if temp_lines[5] > nearest_lower[5] and temp_lines[5] < temp_lines[4]:
                                nearest_lower = temp_lines
                        
                        if nearest_higher is None:
                            if temp_lines[5] > temp_lines[4]:
                                nearest_higher = temp_lines
                        else:
                            if temp_lines[5] < nearest_higher[5] and temp_lines[5] > temp_lines[4]:
                                nearest_higher = temp_lines
                    
                    # Add a relationship between the corresponding TrafficSpaces to the possible two nodes (nearest_lower and nearest_higher)
                    print(nearest_lower)
                    print(nearest_higher)
                    if nearest_lower is not None:
                        print("[INFO] Add relationship between nearest_lower and nearest_higher")
                        self.insert_SWITCH_TO_relation(nearest_lower[0]._properties['id'], nearest_lower[1]._properties['id'])
                    if nearest_higher is not None:
                        print("[INFO] Add relationship between nearest_higher and nearest_lower")
                        self.insert_SWITCH_TO_relation(nearest_higher[0]._properties['id'], nearest_higher[1]._properties['id'])
                        
                

            return result

if __name__ == "__main__":
    # print starting datetime
    print("Starting datetime: ", datetime.now())
    start = datetime.now()
    interactor = Neo4jInteractor("bolt://localhost:7687", username, password)
    res = interactor.find_trafficAreas_to_PARKING_AuxiliaryAreas()
    interactor.close()
    print(f"Execution time: {datetime.now() - start}")
    print("Number of results: ", len(res))

    print("Finished!")
