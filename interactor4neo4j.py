"""This Tool is used to interact with Neo4j Database using the Neo4j Python Driver.
It consists of a Pre-Processing and a Navigation Part."""

import datetime
import json
import re
# Imports
from calendar import c
from math import isnan
from pprint import pprint
from turtle import speed
from typing import final
from unittest import result

import folium
import numpy as np
import open3d as o3d
import utm
from bs4 import BeautifulSoup
from folium import plugins
# import matplotlib
from matplotlib import pyplot as plt
from neo4j import GraphDatabase
from pyparsing import col
from tqdm import tqdm

from constants import password, username

# Constants
uri = "bolt://localhost:7687"

# Helper Functions

# Helper Classes
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

def get_first_point_geometry_node(geometry_node):
    for record in geometry_node:
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
        sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])
        # get the lat, lon and height values of the first point 
        lat = float(sorted_coords[0][1])
        lon = float(sorted_coords[1][1])
        height = float(sorted_coords[2][1])
        return [lat, lon, height]

def add_results_to_map(start, dest, latlngs, distance, weight, transport_type):
    # create list of lists with the coordinates from list of tuples and reverse the order
    # after https://datagy.io/python-reverse-list/
    reverser = slice(None, None, -1)
    # reversed_latlngs = latlngs[reverser]
    # this needs to be done in a loop because the latlngs list contains multiple lists
    final_latlngs = []
    for coord_list in latlngs:
        reversed_latlngs = coord_list[reverser]
        final_latlngs.append([[lat, lon] for lat, lon in reversed_latlngs])
        
    # latlngs = [[lat, lon] for lat, lon in reversed_latlngs]

    # create list of colors for the different transportation types
    colors = []
    for t_type in transport_type:
        if len(t_type) > 0:
            if t_type[0] == "DRIVING":
                colors.append("#0065bd")
            elif t_type[0] == "SIDEWALK":
                colors.append("#f44336")
            elif t_type[0] == "BIKING":
                colors.append("#4caf50")
            elif t_type[0] == "BIDIRECTIONAL":
                colors.append("#9c27b0")
            elif t_type[0] =="SHOULDER":
                colors.append("#ff9800")
            elif t_type[0] == "PARKING":
                colors.append("#ffeb3b")
            else:
                colors.append("#000000")
        else:
            colors.append("#000000")


    with open("web/js/map-script.js", "r", encoding='utf-8') as input_file:
        with open ("web/js/map-script-final.js", "w", encoding="utf-8") as output_file:
            output_file.write(input_file.read())
            output_file.write("\n\n")
            output_file.write(f'''
                var startMarker = L.marker({start}, {{icon:greenIcon}}).addTo(startLayerGroup);\n
                var destinationMarker = L.marker({dest}, {{icon:redIcon}}).addTo(destinationLayerGroup);\n
                var latlngsList = {final_latlngs};\n
                var colors = {colors};\n
                for (var i = 0; i < latlngsList.length; i++) {{
                    var line = L.polyline(latlngsList[i], 
                    {{//dashArray: "20 10", 
                    //dashSpeed: 15, 
                    color: colors[i],
                    weight: 5}}
                    );\n
                    line.addTo(map);\n
                }}
                map.fitBounds([{start}, {dest}]);\n
                var resultsDiv = document.getElementById("results");\n
                resultsDiv.innerHTML = `Distance: <span id="result-weight">${{{round(distance,2)}}}</span>m<br>Total weight: <span id="weight-span">${{{weight}}}</span>`;}}''')
            # TODO uncomment dashArray and dashSpeed to get animated dashed lines
            '''
                var startMarker = L.marker({start}, {{icon:greenIcon}}).addTo(startLayerGroup);\n
                var destinationMarker = L.marker({dest}, {{icon:redIcon}}).addTo(destinationLayerGroup);\n
                var latlngs = {latlngs};\n
                var line = L.polyline(latlngs, {{dashArray: "20 10", dashSpeed: 15, color: "#0065bd"}});\n
                line.addTo(map);\n
                map.fitBounds(line.getBounds());\n
                var resultsDiv = document.getElementById("results");\n
                resultsDiv.innerHTML = `Distance: <span id="result-weight">${{{round(distance,2)}}}</span>m<br>Total weight: <span id="weight-span">${{{weight}}}</span>`;'''
    

def add_additional_routes_to_map(name_id, start, dest, latlngs, distance, weight):
    # latlngs = [[lat, lon] for lat, lon in reversed(latlngs)]
    reverser = slice(None, None, -1)
    reversed_latlngs = latlngs[reverser]
    latlngs = [[lat, lon] for lat, lon in reversed_latlngs]

    # with open("web/js/map-script.js", "r", encoding='utf-8') as input_file:
    with open ("web/js/map-script-final.js", "a", encoding="utf-8") as output_file:
        # output_file.write(input_file.read())
        output_file.write("\n\n")
        output_file.write(f'''
            var startMarker{name_id} = L.marker({start}, {{icon:greenIcon}}).addTo(startLayerGroup);\n
            var destinationMarker{name_id} = L.marker({dest}, {{icon:redIcon}}).addTo(destinationLayerGroup);\n
            var latlngs{name_id} = {latlngs};\n
            var line{name_id} = L.polyline(latlngs{name_id}, {{dashArray: "20 10", dashSpeed: 15, color: "#0065bd"}});\n
            line{name_id}.addTo(map);\n
            map.fitBounds(line{name_id}.getBounds());\n
            //var resultsDiv = document.getElementById("results");\n
            //resultsDiv.innerHTML = `Distance: <span id="result-weight">${{{distance}.toFixed(2)}}</span>m<br>Total weight: <span id="weight-span">${{{weight}}}</span>`;''')


# Pre-Processing class
class Neo4jPreProcessor:

    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    # Static Methods    
    # functions needed for creating routing shortcut relationships
    @staticmethod
    def _insert_predecessor_shortcut(tx, vars):
        # The connection direction has been fixed in the r:tron converter, therefore this code is not needed anymore and infact results in opposite relationships
        # tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="forwards") CREATE (a)-[:PREDECESSOR_OF]->(b);')

        # tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="backwards") CREATE (a)-[:PREDECESSOR_OF]->(b);')

        tx.run("MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) CREATE (a)-[:PREDECESSOR_OF]->(b);")


    @staticmethod
    def _insert_successor_shortcut(tx, vars):
        # The connection direction has been fixed in the r:tron converter, therefore this code is not needed anymore and in fact results in opposite relationships
        # tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="backwards") CREATE (a)-[:SUCCESSOR_OF]->(b);')

        # tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="forwards") CREATE (a)-[:SUCCESSOR_OF]->(b);')

        # default SUCCESSOR_OF relationship
        tx.run("MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) CREATE (a)-[:SUCCESSOR_OF]->(b);")

        # Add SUCCESSOR_OF relationships for trafficDirection="both"
        query="""MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:PREDECESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MATCH (a)-[:trafficDirection]-(n WHERE n.value="both") CREATE (a)-[:SUCCESSOR_OF]->(b);"""
        tx.run(query)
    
    @staticmethod
    def _insert_parking_garage_entrance_connection(tx, vars):
        query="""MATCH (n WHERE n.id="UUID_8e583928-2103-3512-a1be-44d8631f19ad")
    WITH n MATCH (m WHERE m.id="TS_section12")
    CREATE (n)-[:SUCCESSOR_OF]->(m)
    RETURN n,m""" 
        tx.run(query)
    
    # Functions needed for creating lane change relationships
    @staticmethod
    def _insert_lane_changes(tx, vars):
        # Using the !!! trafficAreaID !!! and set the lane changes relationship for the trafficSpaces nodes in one query
        first_id = vars[0][0]
        second_id = vars[1][0]
        result = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) WITH n2,m2 CREATE(n2)-[r:NEIGHBOURS_LANE]->(m2) RETURN r;', id1=first_id, id2=second_id)

        result2 = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) WITH n2,m2 CREATE(n2)-[r:NEIGHBOURS_LANE]->(m2) RETURN r;', id1=second_id, id2=first_id)
    
    @staticmethod
    def _find_lane_nodes(tx, vars):
        first_id = vars[0][0]
        second_id = vars[1][0]

        result = tx.run('MATCH (n WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(n2) WITH n2 MATCH (m WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(m2) RETURN n2,m2;', id1=first_id, id2=second_id)
        for record in result:
            if len([record['n2'], record['m2']]) == 2:
                return [record['n2'], record['m2']]
            else:
                print("\n\033[91m[ERROR]: Could not find the lane nodes pair\033[0m")
    
    @staticmethod
    def _find_lane_information(tx, vars):
        query="""
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` WHERE n.id=$trafficAreaID)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(roadID:`org.citygml4j.core.model.generics.StringAttribute` WHERE roadID.name ="identifier_roadId") 
        WITH n, roadID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(lsID:`org.citygml4j.core.model.generics.IntAttribute` WHERE lsID.name ="identifier_laneSectionId") 
        WITH n, roadID, lsID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(laneID:`org.citygml4j.core.model.generics.IntAttribute` WHERE laneID.name ="identifier_laneId") 
        WITH n, roadID, lsID, laneID MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(laneType:`org.citygml4j.core.model.generics.StringAttribute` WHERE laneType.name="opendrive_lane_type") 
        RETURN roadID.value as roadID, lsID.value as laneSectionID, laneID.value as laneID, laneType.value as laneType;
        """
        result = tx.run(query, trafficAreaID=vars[0])
        for record in result:
            if len([record['roadID'], record['laneSectionID'], record['laneID'], record['laneType']]) == 4:
                return [record['roadID'], int(record['laneSectionID']), int(record['laneID']), record['laneType']]
            else:
                return []
    
    @staticmethod
    def _find_traffic_area(tx, vars):
        result = tx.run("MATCH (n WHERE n.id=$trafficSpaceID)-[r:boundaries]-()-[r2:elementData]-()-[r3:ARRAY_MEMBER]-()-[r4:object]-(ta) RETURN ta;", trafficSpaceID=vars[0])
        return [record["ta"] for record in result]
    
    @staticmethod
    def _find_traffic_spaces(tx, vars):
        result = tx.run("MATCH (n)-[r:trafficSpaces]-()-[r2:elementData]-()-[r3:ARRAY_MEMBER]-()-[r4:object]-(ts) WHERE ID(n)=$sectionID RETURN ts;", sectionID=vars[0])
        return [record["ts"] for record in result]
    
    @staticmethod
    def _find_sections(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.Section` ) RETURN n;")
        return [record["n"] for record in result]

    # Functions for adding weights to the relationships
    @staticmethod
    def _insert_weight(tx, vars):
        raise NotImplementedError
        tx.run('<QUERY>', var1=vars[0])

    @staticmethod
    def _find_trafficSpace_ids(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` ) RETURN n.id as gmlid;")
        return [record["gmlid"] for record in result]
    
    @staticmethod
    def _find_trafficSpace_geometry(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:lod2MultiCurve]-()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;', id=vars[0])
        return [record["m"] for record in result]
    
    @staticmethod
    def _find_trafficSpace_geometry_and_type(tx, vars):
        result = []
        result_node = tx.run('''
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:lod2MultiCurve]-()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;
        ''', id=vars[0])
        result.append([record["m"] for record in result_node])
        result_type = tx.run('''
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m) RETURN n.transportation_type as transportation_type;
        ''', id=vars[0])
        result.append([record["transportation_type"] for record in result_type])
        return result
    
    @staticmethod
    def _insert_distance(tx, vars):
        tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.euclidean_segment_length=$weight RETURN a, b;', id=vars[0], weight=vars[1])
    
    @staticmethod
    def _insert_advanced_distance(tx, vars):
        tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.advanced_segment_length=$weight RETURN a, b;', id=vars[0], weight=vars[1])

    @staticmethod
    def _insert_TrafficSpace_coordinate_attributes(tx, vars):
        tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id) SET n.x= $x, n.y= $y, n.height= $height RETURN n;', id=vars[0], x=vars[1], y=vars[2], height=vars[3])

    @staticmethod
    def _insert_inclination(tx, vars):
        tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.inclination=$weight RETURN a, b;', id=vars[0], weight=vars[1])
    
    @staticmethod
    def _find_trafficArea_geometry(tx, vars):
        # TODO: CHANGE WHEN USED WITH PREVIOUS DATASET
        query = """MATCH (s) WHERE ID(s) = $id 
        WITH s MATCH (s)-[:object]-()-[:patches]-()-[:objects]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:exterior]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;""" # updated query for new database connection path in dataset with garage
        # result = tx.run(query, id=vars[0])
        result = tx.run('MATCH (s) WHERE ID(s) = $id WITH s MATCH (s)-[:object]-()-[:exterior]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;', id=vars[0])
        return [record["m"] for record in result]
    
    @staticmethod
    def _find_trafficArea_SurfaceMembers(tx, vars):
        """Finds all TrafficArea SurfaceMember nodes to a TrafficSpace node"""
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(t)-[:lod2MultiSurface]-()-[:object]-()-[:surfaceMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-(m) RETURN ID(m) as id;', id=vars[0])
        return [record["id"] for record in result]
    
    @staticmethod
    def _insert_min_lane_width(tx, vars):
        tx.run('MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE a.id=$id)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`) WITH a, b MERGE (a)-[r:SUCCESSOR_OF]-(b) SET r.min_width=$weight RETURN a, b;', id=vars[0], weight=vars[1])

    @staticmethod
    def _insert_lane_changes_attributes(tx, vars):
        # Adds all weights including routing weights to the NEIGHBOURS_LANE relationship specified by the internal id of Neo4j
        query="""
        MATCH ()-[r:NEIGHBOURS_LANE]-() WHERE ID(r)=$id SET r.euclidean_segment_length=$euclidean_segment_length, r.advanced_segment_length=$advanced_segment_length, r.inclination=$inclination, r.min_width=$min_width, r.speed_limit=$speed_limit, r.speed_weight=$speed_weight, r.inclination_weight=$inclination_weight, r.width_weight=$width_weight, r.time_weight=$time_weight;
        """
        tx.run(query, id=vars[0], euclidean_segment_length=vars[1], advanced_segment_length=vars[1], min_width=vars[1], inclination=vars[2], inclination_weight=vars[3], speed_limit=vars[4], speed_weight=vars[5],  time_weight=vars[6], width_weight=vars[7])
        
    # @staticmethod
    # def _find_laneChanges_without_SUCCESSOR(tx, vars):
    #     result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[r:NEIGHBOURS_LANE]-(m:`org.citygml4j.core.model.transportation.TrafficSpace`) WHERE NOT (n)-[:SUCCESSOR_OF]-() RETURN n, m;')
    #     return [record["n"] for record in result]

    # @staticmethod
    # def _set_default_speed_limit_property_NEIGHBOURS_LANE(tx, vars):
    #     tx.run('MATCH ()-[r:NEIGHBOURS_LANE]-() WHERE ID(r)=$id SET r.speed_limit=$speed_limit RETURN r;', id=vars[0], speed_limit=vars[1])

    @staticmethod
    def _find_trafficAreas_to_PARKING_AuxiliaryAreas(tx, vars):
        # ! Note the Parking areas have been moved from AuxiliaryTrafficArea to TrafficArea elements with the dataset from 20230921!
        # Only the first MATCH in the query is affected
        query = '''MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_lane_type" and m.value="PARKING") 
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
        result = tx.run(query, vars)
        output = []
        for record in result:
            output.append([record["n"], record["a"], record["road_id"], record["lane_segment_id"], record["original_lane_id"], record["possible_lane_neighbour_id"]])
        return output
    
    @staticmethod
    def _insert_SWITCH_TO_relation(tx, vars):
        # ! Note the Parking areas have been moved from AuxiliaryTrafficArea to TrafficArea elements with the dataset from 20230921!
        # Only the first MATCH in the query is affected
        query1 = '''
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(a)
        WITH a
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea` WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(b)
        WITH a, b
        CREATE (a)-[:SWITCH_TO]->(b);
        '''
        # ! Note the Parking areas have been moved from AuxiliaryTrafficArea to TrafficArea elements with the dataset from 20230921!
        # Only the first MATCH in the query is affected
        query2 = '''
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea` WHERE n.id=$id1)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(a)
        WITH a
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea` WHERE m.id=$id2)-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(b)
        WITH a, b
        CREATE (b)-[:SWITCH_TO_PARKING]->(a);
        '''
        tx.run(query1, id1=vars[0], id2=vars[1])
        tx.run(query2, id1=vars[0], id2=vars[1])

    @staticmethod
    def _insert_transport_mode_switch(tx, vars):
        query = """
        MATCH ()-[r:SWITCH_TO]-() WHERE ID(r)=$id SET r.euclidean_segment_length=$euclidean_segment_length, r.advanced_segment_length=$advanced_segment_length, r.inclination=$inclination, r.min_width=$min_width, r.speed_limit=$speed_limit, r.speed_weight=$speed_weight, r.inclination_weight=$inclination_weight, r.width_weight=$width_weight, r.time_weight=$time_weight;
        """
        tx.run(query, id=vars[0], euclidean_segment_length=vars[1], advanced_segment_length=vars[1], inclination=vars[2], inclination_weight=vars[3], speed_limit=vars[4], speed_weight=vars[5],  time_weight=vars[6], min_width=vars[7], width_weight=vars[8])
        
        # tx.run('MATCH p=()-[r:SWITCH_TO]->() SET r.euclidean_segment_length=0 RETURN p;') # TODO: The euclidean_segment_length is not correct, it should be the distance between the two lane changes
        # tx.run('MATCH p=()-[r:SWITCH_TO]->() SET r.advanced_segment_length=0 RETURN p;') # TODO: The advanced_segment_length is not correct, it should be the distance between the two lane changes
        # tx.run('MATCH p=()-[r:SWITCH_TO]->() SET r.inclination=0 RETURN p;') # TODO: Calculate the inclination between the two lane changes nodes
        # tx.run('MATCH p=()-[r:SWITCH_TO]->() SET r.min_width=0 RETURN p;') # TODO: The min_width is not correct, it should be the width of the lane change

    @staticmethod
    def _insert_transport_mode_switch_parking(tx, vars):
        # The SWITCH_TO_PARKING relationships are used in the routing algorithm to block transportation mode changes, therefore the default weights are set to 0 to allow the routing algorithm to find the shortest path, the weights for changing the transportation mode are set in the _insert_transportation_mode_switch function
        query="""
        MATCH p=()-[r:SWITCH_TO_PARKING]->() SET r.euclidean_segment_length=0, r.advanced_segment_length=0, r.inclination=0, r.min_width=0, r.speed_limit=0, r.speed_weight=0, r.inclination_weight=0, r.width_weight=0, r.time_weight=0 RETURN p;""" 
        tx.run(query)

    @staticmethod
    def _insert_transportation_type_to_nodes(tx, vars):
        """Adds the transportation type to the TrafficSpace nodes"""
        tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="opendrive_lane_type") WITH n, m, a SET n.transportation_type=a.value;')

    @staticmethod
    def _insert_transportation_type_to_successor_relationship(tx, vars):
        """Adds the transportation type to the successor relationships"""
        # Needs to be run after the transportation type has been added to the nodes
        tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[r:SUCCESSOR_OF]-() WITH n, r SET r.transportation_type=n.transportation_type;')
    
    @staticmethod
    def _insert_bidirectional_successor_relationship(tx, vars):
        """Adds the second successor relationship (SUCCESSOR_OF_2) for bidirectional lane type
        This function requires that the transportation type has been added to the nodes and relationships and that the SUCCESSOR_OF relationships have been created!
        """
        tx.run('''MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE n.transportation_type = "BIDIRECTIONAL"
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE m.transportation_type = "BIDIRECTIONAL"
        MATCH (n)-[r:SUCCESSOR_OF]->(m)
        CREATE (n)<-[r2:SUCCESSOR_OF_2]-(m)
        SET r2 = properties(r)
        SET r2.inclination = r.inclination * (-1)
        RETURN n, m, r2;''')

    @staticmethod
    def _insert_bidirectional_successor_relationship_sidewalk(tx, vars):
        """Adds the second successor relationship (SUCCESSOR_OF_2) allowing traversal in both directions on the sidewalk. This allows modelling pedestrians walking in both directions on the sidewalk regardless of the driving direction of the road."""
        query = """MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE n.transportation_type = "SIDEWALK"
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE m.transportation_type = "SIDEWALK"
        MATCH (n)-[r:SUCCESSOR_OF]->(m)
        CREATE (n)<-[r2:SUCCESSOR_OF_2]-(m)
        SET r2 = properties(r)
        SET r2.inclination = r.inclination * (-1)
        RETURN n, m, r2;"""
        tx.run(query)

    @staticmethod
    def _insert_bidirectional_successor_relationship_sidewalk_no_properties(tx, vars):
        query = """MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE n.transportation_type = "SIDEWALK"
        MATCH (m:`org.citygml4j.core.model.transportation.TrafficSpace`)
        WHERE m.transportation_type = "SIDEWALK"
        MATCH (n)-[r:SUCCESSOR_OF]->(m)
        CREATE (n)<-[r2:SUCCESSOR_OF_2]-(m)
        RETURN n, m, r2;"""
        tx.run(query)

    @staticmethod
    def _insert_trafficSign_UUIDs(tx, vars):
        """Adds the UUIDs of the cityFurniture traffic sign nodes to the TrafficSpace navigation relationships, like SUCCESSOR_OF"""
        query = """MATCH (n)-[r:SUCCESSOR_OF]->() WHERE ID(n)=$id 
                    SET r.trafficSignIds = coalesce(r.trafficSignIds, []) + $trafficSignUUID
                    RETURN n, r;"""
        tx.run(query, id=vars[0], trafficSignUUID=vars[1])

    @staticmethod
    def _insert_speed_limit_streetSign_shortcut(tx, vars):
        query = """
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:relatedTo]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:relatedTo]-()-[:object]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
        WITH n,f,o, a 
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type" and b.value="274")
        WITH n,f,o, a,b
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
        WITH n,f,o, a,b,c
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
        WITH n,f,o, a,b,c,d
        CREATE (n)-[r:SPEED_LIMIT_SIGN {value: c.value}]->(f)
        RETURN n,f,o, a,b,c,d;
        """
        tx.run(query)

    @staticmethod
    def _insert_speed_limit_property(tx,vars):
        query = """MATCH p=(n WHERE n.transportation_type in["BIDIRECTIONAL","DRIVING"])-[r:SPEED_LIMIT_SIGN]->(m) 
                WITH n, r
                MATCH (n)-[r2:SUCCESSOR_OF]->()
                SET r2.speed_limit = r.value
                RETURN n, r2.speed_limit;"""
        result = tx.run(query)
        return [record for record in result] # return [record["n"] for record in result]        
    
    @staticmethod
    def _set_speed_limit_property(tx, vars):
        query = """MATCH (n WHERE n.id=$id)-[r:SUCCESSOR_OF]->()
                SET r.speed_limit = $speed_limit"""
        tx.run(query, id=vars[0], speed_limit=vars[1])

    @staticmethod
    def _set_default_speed_limit_property(tx, vars):
        """Sets the default speed limit for the given transportation type (must be a list of transportation types)"""
        query = """MATCH p=(n WHERE n.transportation_type in $transportationType)-[r:SUCCESSOR_OF]->() WHERE(r.speed_limit IS NULL) SET r.speed_limit=$speed_limit RETURN n"""
        tx.run(query, transportationType=vars[0], speed_limit=vars[1])
    
    @staticmethod
    def _remove_trafficSign_UUIDs(tx, vars):
        """Resets the trafficSignIds property of the navigation relationships, like SUCCESSOR_OF"""
        query = """MATCH (n)-[r:SUCCESSOR_OF]->() WHERE ID(n)=$id 
                    REMOVE r.trafficSignIds
                    RETURN n, r;"""
        tx.run(query, id=vars[0])


    @staticmethod
    def _get_traffic_sign_info(tx, vars):
        """Returns the traffic sign information for the given TrafficSpace"""
        
        '''MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
        WITH n,f,o, a 
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type") RETURN n,f,o, a,b limit 1;
        '''
        query = '''MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
        WITH n,f,o, a 
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
        WITH n,f,o, a,b
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
        WITH n,f,o, a,b,c
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
        RETURN n,f,o, a,b,c,d;'''

        result = tx.run(query,)
        output = []
        for record in result:
            output.append([record["n"], record["b"], record["c"], record["d"]])
        return output
    
    @staticmethod
    def _get_metadata_information(tx, vars):
        result = tx.run("CALL apoc.meta.stats()")
        return [record for record in result]
    
    @staticmethod
    def _get_bounding_box(tx, vars):
        result = tx.run("""
        MATCH (n:`org.citygml4j.core.model.core.CityModel`)-[:boundedBy]-()-[:envelope]-(e)
        WITH e
        MATCH (e)-[:upperCorner]-()-[:value]-()-[:elementData]-(a)
        WITH e, a
        MATCH (e)-[:lowerCorner]-()-[:value]-()-[:elementData]-(b)
        RETURN a as upperCorner, b as lowerCorner, e.srsName;
        """)
        return [record for record in result]
    
    @staticmethod
    def _get_speed_street_sign_code(tx, vars):
        query="""
        MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
        WITH n,f,o, a 
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type" and b.value="274")
        WITH n,f,o, a,b
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
        WITH n,f,o, a,b,c
        MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
        RETURN n,f,o, a,b,c,d;
        """
        result = tx.run(query)
        output = []
        for record in result:
            output.append([record["n"], record["f"], record["b"], record["c"], record["d"]])
        return output

    @staticmethod
    def _get_traffic_sign_codes(tx, vars):
        alternative_query = """
                MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:relatedTo]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:relatedTo]-()-[:object]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
                WITH n,f,o, a 
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
                WITH n,f,o, a,b
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
                WITH n,f,o, a,b,c
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
                RETURN n,f,o, a,b,c,d;
                """
        # The alternative query currently is not supported as the origin dataset has missing connections! (2023-09-16)
        query="""
                MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
                WITH n,f,o, a 
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
                WITH n,f,o, a,b
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
                WITH n,f,o, a,b,c
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
                RETURN n,f,o, a,b,c,d;
            """
        
        result = tx.run(query)
        output = []
        for record in result:
            output.append([record["n"], record["f"], record["b"], record["c"], record["d"]])
        return output
    
    @staticmethod
    def _test_speed_limit_set(tx, vars):
        query = """MATCH (n WHERE n.id=$id)-[:SUCCESSOR_OF]->(m)-[r:SUCCESSOR_OF]->(l) RETURN m.id, r.speed_limit"""
        result = tx.run(query, id=vars[0])
        return [record for record in result]
    
    @staticmethod
    def _find_laneChanges_with_SUCCESSOR(tx, vars):
        query="""MATCH p=(n)-[r:NEIGHBOURS_LANE]->(m) 
        WITH n, m, r, p
        MATCH (n)-[r2:SUCCESSOR_OF]->()
        WITH n, m, r, p, r2
        MATCH (m)-[r3:SUCCESSOR_OF]->()
        RETURN n, m, r, r2.speed_limit, r3.speed_limit"""
        result = tx.run(query)
        return [record for record in result]
    
    @staticmethod
    def _find_laneChanges(tx, vars):
        query="""MATCH p=(n)-[r:NEIGHBOURS_LANE]->(m) 
        RETURN n, m, r, p"""
        result = tx.run(query)
        return [record for record in result]
    
    @staticmethod
    def _test_speed_limit_set_NEIGHBOURS_LANE(tx, vars):
        # check whether a SUCCESSOR_OF relationship exists at the NEIGHBOURS_LANE relationship by id
        query = """
        MATCH (n)-[r:NEIGHBOURS_LANE]-(m) WHERE ID(r)=$id
        WITH n, m, r
        MATCH (n)-[r2:SUCCESSOR_OF]->()
        RETURN r2.speed_limit
        """
        result = tx.run(query, id=vars[0])
        return [record for record in result]
        
    @staticmethod
    def _find_transport_mode_switch(tx, vars):
        query = """
        MATCH (n)-[r:SWITCH_TO]->(m)
        RETURN n, m, r
        """
        result = tx.run(query)
        return [record for record in result]
    
    @staticmethod
    def _get_successor_of_relationships(tx, vars):
        query = """
        MATCH (n)-[r:SUCCESSOR_OF]->(m)
        RETURN n, m, r
        """
        result = tx.run(query)
        return [record for record in result]
    
    @staticmethod
    def _insert_successor_of_properties(tx, vars):
        # Add the SUCCESSOR_OF properties which are used as routing weights, the relationship is found via the internal Neo4j id
        query = """
        MATCH (n)-[r:SUCCESSOR_OF]->(m) WHERE ID(r)=$id
        SET r.speed_weight=$speed_weight, r.inclination_weight=$inclination_weight, r.width_weight=$width_weight, r.time_weight=$time_weight
        RETURN n, m, r
        """
        tx.run(query, id=vars[0], speed_weight=vars[1], inclination_weight=vars[2], width_weight=vars[3], time_weight=vars[4])

    @staticmethod
    def _get_successor_of_2_relationships(tx, vars):
        query = """
        MATCH (n)-[r:SUCCESSOR_OF_2]->(m)
        RETURN n, m, r
        """
        result = tx.run(query)
        return [record for record in result]
    
    @staticmethod
    def _insert_successor_of_2_properties(tx, vars):
        # Add the SUCCESSOR_OF properties which are used as routing weights, the relationship is found via the internal Neo4j id
        query = """
        MATCH (n)-[r:SUCCESSOR_OF_2]->(m) WHERE ID(r)=$id
        SET r.speed_weight=$speed_weight, r.inclination_weight=$inclination_weight, r.width_weight=$width_weight, r.time_weight=$time_weight
        RETURN n, m, r
        """
        tx.run(query, id=vars[0], speed_weight=vars[1], inclination_weight=vars[2], width_weight=vars[3], time_weight=vars[4])

    # Insert Functions
    def insert(self, query, vars):
        with self.driver.session() as session:
            
            if query == "lane_changes":
                print("\n\033[96m[INFO]: Inserting the lane changes relationship: 'NEIGHBOURS_LANE'\033[0m")
                session.execute_write(self._insert_lane_changes, vars)
            if query == "predecessor_shortcut":
                print("\n\033[96m[INFO]: Inserting the predecessor shortcut relationship: 'PREDECESSOR_OF'\033[0m")
                session.execute_write(self._insert_predecessor_shortcut, vars)
            if query == "successor_shortcut":
                print("\n\033[96m[INFO]: Inserting the successor shortcut relationship: 'SUCCESSOR_OF'\033[0m")
                session.execute_write(self._insert_successor_shortcut, vars)
            
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
                    # not all TrafficSpace objects have a gml UUID, therefore check if there is a string containing the UUID
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
                        result = session.execute_write(self._insert_distance, [id, dist])
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
                            sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])

                            # create 3D points from the sorted coordinates
                            points=[]
                            for x, y, z in zip(sorted_coords[0::3], sorted_coords[1::3], sorted_coords[2::3]):
                                # print(float(x[1]), float(y[1]), float(z[1]))
                                points.append([float(x[1]), float(y[1]), float(z[1])])
                            
                            # calculate the distance between two following points and add it to the total distance
                            for i in range(len(points)-1):
                                dist += euclidean_distance(points[i], points[i+1])
                            # print(f"\033[96m[INFO] Length of TrafficSpace object: {dist} meters \033[0m")

                            total_dist += dist
                            trafficSpace_dists.append(dist)
                        result = session.execute_write(self._insert_advanced_distance, [id, dist])
                print(f"\033[96m[INFO] Total length of all TrafficSpace objects: {total_dist} meters \033[0m")
                print(f"\033[96m[INFO] Minimum length of a TrafficSpace object: {min(trafficSpace_dists)} meters \033[0m")
                print(f"\033[96m[INFO] Maximum length of a TrafficSpace object: {max(trafficSpace_dists)} meters \033[0m")

                # 
            if query == "coords":
                """Add coordinates of first point to TrafficSpace elements"""
                # find all trafficSpace elements
                lat = None
                lon = None
                height = None
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
                        y = float(sorted_coords[0][1])
                        x = float(sorted_coords[1][1])
                        height = float(sorted_coords[2][1])
                    result = session.execute_write(self._insert_TrafficSpace_coordinate_attributes, [id, x, y, height])
            if query == "inclination":
                # TODO: Check if the inclination is calculated correctly with the right sign for the travel direction!
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
                    inclination = 0
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
                    result = session.execute_write(self._insert_inclination, [id, inclination*100])
                print(f"\033[96m[INFO] Minimum inclination of the TrafficSpace: {min(inclinations)*100} % \033[0m")
                print(f"\033[96m[INFO] Maximum inclination of the TrafficSpace: {max(inclinations)*100} % \033[0m")
            if query == "min_width":
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
                    result = session.execute_write(self._insert_min_lane_width, [id, minimum_width])
                print(list_of_widths)
                # print minimum and maximum width of the list_of_widths
                # remove all -1 values from the list and count the number of -1 values
                print(f"\033[96m[INFO] Number of TrafficSpace elements without a width: {list_of_widths.count(-1)} \033[0m") # Those should be the TrafficSpace elements used for storing data but do not have a own citygml id
                list_of_widths = [x for x in list_of_widths if x != -1]
                print(f"\033[96m[INFO] Minimum width of the TrafficSpace: {min(list_of_widths)} meters \033[0m")
                print(f"\033[96m[INFO] Maximum width of the TrafficSpace: {max(list_of_widths)} meters \033[0m")
            if query == "lane_change_attributes":
                # ! [INFO] NEIGHBOURS_LANE relationships with nodes that have just one or no successor need a special treatment!
                # Besides the speed_limit property and the derived time, the weights can be calculated/generated in the same manner. The speed limit could be derived by the incoming SUCCESSOR_OF relationships. However, here again only one or none could exist!

                # retrieve lane change relationships NEIGHBOURS_LANE
                result = session.execute_read(self._find_laneChanges, vars)
                
                print(f"\n\033[96m[INFO]: Adding lane change attributes to {len(result)} 'NEIGHBOURS_LANE' relationships\033[0m")
                for record in result:
                    # Calculate the weights for the lane change relationships
                    # distance
                    # get the id of the two TrafficSpace elements
                    id1 = record[0]._properties["id"]
                    id2 = record[1]._properties["id"]
                    
                    # get the first and last point of the TrafficSpace geometries
                    coord_node1 = session.execute_read(self._find_trafficSpace_geometry, [id1])
                    point1 = get_first_point_geometry_node(coord_node1)
                    coord_node2 = session.execute_read(self._find_trafficSpace_geometry, [id2])
                    point2 = get_first_point_geometry_node(coord_node2)

                    euclidean_dist = euclidean_distance(point1, point2)
                    # ==> euclidean distance and advanced distance as well as width all get this value
                    width_weight = 1 / euclidean_dist

                    # inclination
                    inclination = (point2[2] - point1[2]) / euclidean_dist
                    inclination_weight = inclination + 100

                    # Check whether a speed limit can be derived from SUCCESSOR_OF relationships
                    # If not, use a default value of 0.1 
                    relationship_id = record[2].id
                    result = session.execute_read(self._test_speed_limit_set_NEIGHBOURS_LANE, [relationship_id])
                    if len(result) == 2:
                        speed_limit = min(result[0][0], result[1][0])
                    elif len(result) == 1:
                        speed_limit = result[0][0]
                    else:
                        speed_limit = 0.1 # Set default value for the speed_limit property to 0.1 as we have to divide by it later on and we do not want to divide by 0

                    # speed
                    speed_weight = 1 / speed_limit
                    # time
                    time_weight = euclidean_dist / (speed_limit/3.6) # [m/s]

                    # add weights as properties to the relationship
                    result = session.execute_write(self._insert_lane_changes_attributes, [record[2].id, euclidean_dist, inclination, inclination_weight, speed_limit, speed_weight, time_weight, width_weight])

                # result = session.execute_write(self._insert_lane_changes_attributes, [])
            if query == "transport_mode_switch":
                # Set the default value 0 for the SWITCH_TO_PARKING relationship
                result = session.execute_write(self._insert_transport_mode_switch_parking, [])

                # calculate the weights for switching transportation modes and add them as properties to the SWITCH_TO relationship

                # retrieve all transportation mode switching relationships
                result = session.execute_read(self._find_transport_mode_switch, vars)

                print(f"\n\033[96m[INFO]: Adding transportation mode switch attributes to {len(result)} 'SWITCH_TO' relationships\033[0m")

                for record in result:
                    id1 = record[0]._properties["id"]
                    id2 = record[1]._properties["id"]
                    # get the first and last point of the TrafficSpace geometries
                    coord_node1 = session.execute_read(self._find_trafficSpace_geometry, [id1])
                    point1 = get_first_point_geometry_node(coord_node1)
                    coord_node2 = session.execute_read(self._find_trafficSpace_geometry, [id2])
                    point2 = get_first_point_geometry_node(coord_node2)

                    # TODO: Not perfect as the outgoing and incoming distances could be of different length. However, the case exists that a parking space has only one connection to go in and out but is connected to other parking spaces via successor relationships. Thus, the traversal is possible but not using the envisioned element.
                    euclidean_dist = euclidean_distance(point1, point2) 
                    # ==> euclidean distance and advanced distance get this value

                    # inclination
                    if euclidean_dist == 0:
                        inclination = 0
                    else:
                        inclination = (point2[2] - point1[2]) / euclidean_dist
                    inclination_weight = inclination + 100

                    speed_limit = 5 # [km/h] Set default value for the speed_limit property to 5 [km/h] as we deal with parking lots or other switches involving walking and this is roughly the speed of walking
                    # speed
                    speed_weight = 1 / speed_limit
                    # time
                    changing_time = 0 # [s] # TODO this default value can be changed later on for more advanced applications
                    time_weight = euclidean_dist / (speed_limit/3.6) + changing_time

                    # width is not relevant for transportation mode switches
                    # In more advanced applications the width of a parking space could be used to determine whether a vehicle can park there or not
                    width = 0
                    width_weight = 0

                    # add weights as properties to the relationship
                    result = session.execute_write(self._insert_transport_mode_switch, [record[2].id, euclidean_dist, inclination, inclination_weight, speed_limit, speed_weight, time_weight, width, width_weight])
            if query == "add_transportation_type":
                result = session.execute_write(self._insert_transportation_type_to_nodes, [])
                result = session.execute_write(self._insert_transportation_type_to_successor_relationship, [])
            if query == "add_bidirectional_successor_relationship":
                result = session.execute_write(self._insert_bidirectional_successor_relationship, [])
            if query == "add_bidirectional_successor_of_2_weights":
                # add the remaining routing weight properties to the relationship
                # get all SUCCESSOR_OF_2 relationships
                result = session.execute_read(self._get_successor_of_2_relationships, [])

                print(f"\n\033[96m[INFO]: Adding routing weights to {len(result)} 'SUCCESSOR_OF_2' relationships\033[0m")

                for record in result:
                    # speed
                    speed_weight = 1 / record[2]._properties["speed_limit"]
                    # inclination
                    inclination_weight = record[2]._properties["inclination"] + 100
                    # width
                    width_weight = 1 / record[2]._properties["min_width"]
                    # time
                    time_weight = record[2]._properties["advanced_segment_length"] / (record[2]._properties["speed_limit"]/3.6)

                    # add weights as properties to the relationship
                    result = session.execute_write(self._insert_successor_of_2_properties, [record[2].id, speed_weight, inclination_weight, width_weight, time_weight])
            
            if query == "add_bidirectional_successor_sidewalk_relationship":

                # Check if the SUCCESSOR_OF relationship has properties
                result = session.execute_read(self._get_successor_of_relationships, [])

                properties_availiable = True
                print(f"Checking for available properties")
                for record in result:
                    # check if the relationship has properties
                    if len(record[2]._properties) <= 1 : # TODO: Could be a more advanced check
                        properties_availiable = False
                        print(f"\033[96m[INFO] Relationship {record[2].id} has no weight properties\033[0m")

                if properties_availiable:
                    result = session.execute_write(self._insert_bidirectional_successor_relationship_sidewalk, [])
                else:
                    print(f"\033[96m[INFO] Not all relationships have properties, therefore the bidirectional relationships cannot be created\033[0m")
                    # wait for user input to add relationships without properties
                    userinput = input("Do you want to add the relationships without properties? (y/n): ")
                    if userinput == "y":
                        print(f"\033[96m[INFO] Adding relationships without properties\033[0m")
                        result = session.execute_write(self._insert_bidirectional_successor_relationship_sidewalk_no_properties, [])
                    else:
                        print(f"\033[96m[INFO] No relationships added\033[0m")


            if query == "traffic_signs":
                # TODO: Add weights to the successor and lane change and transportation switch relationships
                # 1) find all trafficSpace elements
                # 2) for each trafficSpace element get the related cityFurniture elements
                # 3) for each cityFurniture element analyze the genericAttributes
                # 3.1) create weight for usability of the segment for certain transportation types
                # 3.2) create weight for speed limits
                # 3.3) create weight for waiting times and delays
                # 3.4) create final weight for traversal time of a segment used for routing which includes information about the transportation type, speed limits, waiting times and delays, inclination, and restrictions

                # 1) find all trafficSpace elements and
                # 2) for each trafficSpace element get the related cityFurniture elements
                """
                MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(cityFurniture) RETURN n, cityFurniture;
                """
                # 1) 2) and for 3) the genericAttributes to analyze are combined in one query
                """
                MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:relatedTo]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:relatedTo]-()-[:object]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
                WITH n,f,o, a 
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
                WITH n,f,o, a,b
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
                WITH n,f,o, a,b,c
                MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
                RETURN n,f,o, a,b,c,d;
                """

                # 3)
                # Retrieve the traffic sign information for each TrafficSpace element
                # Codes for "Verkehrsverbote" signs
                # Source: https://de.wikipedia.org/wiki/Bildtafel_der_Verkehrszeichen_in_der_Bundesrepublik_Deutschland_seit_2017 (18.08.2023)
                codes_restriction = {
                    "250": "Verbot für Fahrzeuge aller Art",
                    "251": "Verbot für Kraftwagen",
                    "253": "Verbot für Kraftfahrzeuge über 3,5 t",
                    "254": "Verbot für Radverkehr",
                    "255": "Verbot für Krafträder",
                    "257-50": "Verbot für Mofas",
                    "257-51": "Verbot für Reiter",
                    "257-52": "Verbot für Gespannfuhrwerke",
                    "257-53": "Verbot für Viehtrieb",
                    "257-54": "Verbot für Kraftomnibusse",
                    "257-55": "Verbot für Personenkraftwagen",
                    "257-56": "Verbot für Personenkraftwagen mit Anhänger",
                    "257-57": "Verbot für Lastkraftwagen mit Anhänger",
                    "257-58": "Verbot für Kraftfahrzeuge und Züge, die nicht schneller als 25 km/h fahren können oder dürfen",
                    "259": "Verbot für Fußgänger",
                    "260": "Verbot für Kraftfahrzeuge",
                    "261": "Verbot für kennzeichnungspflichtige Kraftfahrzeuge mit gefährlichen Gütern",
                    "262-": "Tatsächliche Masse: die Unternummer entspricht dem angegebenen Zahlwert",
                    "263-": "Tatsächliche Achslast: die Unternummer entspricht dem angegebenen Zahlwert",
                    "264-": "Tatsächliche Breite: die Unternummer entspricht dem angegebenen Zahlwert",
                    "264-2,3": "Tatsächliche Breite: die Unternummer entspricht dem angegebenen Zahlwert",
                    "265-": "Tatsächliche Höhe: die Unternummer entspricht dem angegebenen Zahlwert",
                    "266-": "Tatsächliche Länge: die Unternummer entspricht dem angegebenen Zahlwert",
                    "267": "Verbot der Einfahrt",
                    "269": "Verbot für Fahrzeuge mit wassergefährdender Ladung",
                    "272": "Verbot des Wendens",
                }

                code_speed_limit = {"274-5": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-10": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-20": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-30": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-40": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-50": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-60": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-70": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-80": "Zulässige Höchsteschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-90": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-100": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-110": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-120": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274-130": "Zulässige Höchstgeschwindigkeit: die Unternummer entspricht dem angegebenen Zahlwert",
                    "274.1": "Beginn einer Tempo 30-Zone",
                    "274.1-20": "Beginn einer Tempo 20-Zone in verkehrsberuhigten Geschäfts-bereichen",
                    "274.2": "Ende einer Tempo 30-Zone",
                    "274.2-20": "Ende einer Tempo 20-Zone in verkehrsberuhigten Geschäftsbereichen",
                    "275-": "Vorgeschriebene Mindestgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-5": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-10": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-20": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-30": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-40": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-50": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-60": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-70": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-80": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-90": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-100": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-110": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-120": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "278-130": "Ende der zulässigen Höchstgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "279-": "Ende der vorgeschriebenen Mindestgeschwindigkeit; Neu: die Unternummer ändert sich mit dem angegebenen Zahlenwert",
                    "282": "Ende sämtlicher streckenbezogener Geschwindigkeitsbeschränkungen und Überholverbote",
                }

                codes_delay = {
                    "101": "Gefahrenstelle",
                    "101-10": "Flugbetrieb – Aufstellung rechts;",
                    "101-20": "Flugbetrieb – Aufstellung links;",
                    "101-11": "Fußgängerüberweg – Aufstellung rechts;",
                    "101-21": "Fußgängerüberweg – Aufstellung links;",
                    "101-12": "Viehtrieb – Aufstellung rechts;",
                    "101-22": "Viehtrieb – Aufstellung links;",
                    "101-13": "Reiter – Aufstellung rechts;",
                    "101-23": "Reiter – Aufstellung links;",
                    "101-14": "Amphibienwanderung – Aufstellung rechts;",
                    "101-24": "Amphibienwanderung – Aufstellung links;",
                    "101-15": "Steinschlag – Aufstellung rechts;",
                    "101-25": "Steinschlag – Aufstellung links;",
                    "101-51": "Schnee- oder Eisglätte;",
                    "101-52": "Splitt, Schotter;",
                    "101-53": "Ufer;",
                    "101-54": "Unzureichendes Lichtraumprofil;",
                    "101-55": "Bewegliche Brücke;",
                    "102": "Kreuzung oder Einmündung",
                    "103-10": "Kurve – links",
                    "103-20": "Kurve – rechts",
                    "105-10": "Doppelkurve – zunächst links",
                    "105-20": "Doppelkurve – zunächst rechts",
                    "108-4": "Gefälle 4 %;",
                    "108-5": "Gefälle 5 %;",
                    "108-6": "Gefälle 6 %;",
                    "108-7": "Gefälle 7 %;",
                    "108-8": "Gefälle 8 %;",
                    "108-9": "Gefälle 9 %;",
                    "108-10": "Gefälle 10 %;",
                    "108-11": "Gefälle 11 %;",
                    "108-12": "Gefälle 12 %;",
                    "108-13": "Gefälle 13 %;",
                    "108-14": "Gefälle 14 %;",
                    "108-15": "Gefälle 15 %;",
                    "108-16": "Gefälle 16 %;",
                    "108-17": "Gefälle 17 %;",
                    "108-18": "Gefälle 18 %;",
                    "108-19": "Gefälle 19 %;",
                    "108-20": "Gefälle 20 %;",
                    "108-21": "Gefälle 21 %;",
                    "108-22": "Gefälle 22 %;",
                    "108-23": "Gefälle 23 %;",
                    "108-24": "Gefälle 24 %;",
                    "108-25": "Gefälle 25 %;",
                    "110-4": "Steigung 4 %;",
                    "110-5": "Steigung 5 %;",
                    "110-6": "Steigung 6 %;",
                    "110-7": "Steigung 7 %;",
                    "110-8": "Steigung 8 %;",
                    "110-9": "Steigung 9 %;",
                    "110-10": "Steigung 10 %;",
                    "110-11": "Steigung 11 %;",
                    "110-12": "Steigung 12 %;",
                    "110-13": "Steigung 13 %;",
                    "110-14": "Steigung 14 %;",
                    "110-15": "Steigung 15 %;",
                    "110-16": "Steigung 16 %;",
                    "110-17": "Steigung 17 %;",
                    "110-18": "Steigung 18 %;",
                    "110-19": "Steigung 19 %;",
                    "110-20": "Steigung 20 %;",
                    "110-21": "Steigung 21 %;",
                    "110-22": "Steigung 22 %;",
                    "110-23": "Steigung 23 %;",
                    "110-24": "Steigung 24 %;",
                    "110-25": "Steigung 25 %;",
                    "112": "Unebene Fahrbahn",
                    "113": "Schleuder- oder Rutschgefahr",
                    "117-10": "Seitenwind von rechts",
                    "117-20": "Seitenwind von links",
                    "120": "Verengte Fahrbahn",
                    "121-10": "Einseitig verengte Fahrbahn – Verengung rechts",
                    "121-20": "Einseitig verengte Fahrbahn – Verengung links",
                    "123": "Arbeitsstelle",
                    "124": "Stau",
                    "125": "Gegenverkehr",
                    "131": "Lichtzeichenanlage",
                    "133-10": "Fußgänger – Aufstellung rechts",
                    "133-20": "Fußgänger – Aufstellung links",
                    "136-10": "Kinder – Aufstellung rechts",
                    "136-20": "Kinder – Aufstellung links",
                    "138-10": "Radverkehr – Aufstellung rechts",
                    "138-20": "Radverkehr – Aufstellung links",
                    "142-10": "Wildwechsel – Aufstellung rechts",
                    "142-20": "Wildwechsel – Aufstellung links",
                    "151": "Bahnübergang",
                    "156-10": "Bahnübergang mit dreistreifiger Bake – Aufstellung rechts",
                    "156-11": "Bahnübergang mit dreistreifiger Bake, mit Entfernungsangabe – Aufstellung rechts",
                    "156-20": "Bahnübergang mit dreistreifiger Bake – Aufstellung links",
                    "156-21": "Bahnübergang mit dreistreifiger Bake, mit Entfernungsangabe – Aufstellung links",
                    "157-10": "Dreistreifige Bake – Aufstellung rechts",
                    "157-11": "Dreistreifige Bake, mit Entfernungsangabe – Aufstellung rechts",
                    "157-20": "Dreistreifige Bake – Aufstellung links",
                    "157-21": "Dreistreifige Bake, mit Entfernungsangabe – Aufstellung links",
                    "159-10": "Zweistreifige Bake – Aufstellung rechts",
                    "159-11": "Zweistreifige Bake, mit Entfernungsangabe – Aufstellung rechts",
                    "159-20": "Zweistreifige Bake – Aufstellung links",
                    "159-21": "Zweistreifige Bake, mit Entfernungsangabe – Aufstellung links",
                    "162-10": "Einstreifige Bake – Aufstellung rechts",
                    "162-11": "Einstreifige Bake, mit Entfernungsangabe – Aufstellung rechts",
                    "162-20": "Einstreifige Bake – Aufstellung links",
                    "162-21": "Einstreifige Bake, mit Entfernungsangabe – Aufstellung links",

                    "201-50": "Andreaskreuz — stehend: Dem Schienenverkehr Vorrang gewähren!",
                    "201-51": "Andreaskreuz — stehend mit Blitzpfeil: Dem Schienenverkehr Vorrang gewähren!",
                    "201-52": "Andreaskreuz — liegend: Dem Schienenverkehr Vorrang gewähren!",
                    "201-53": "Andreaskreuz — liegend mit Blitzpfeil: Dem Schienenverkehr Vorrang gewähren!",
                    "205": "Vorfahrt gewähren",
                    "206": "Halt. Vorfahrt gewähren",
                    "208": "Vorrang des Gegenverkehrs",
                }

                # result = session.execute_read(self._get_traffic_sign_codes, [])
                # print(f"Number of TrafficSign elements: {len(result)}")
                # print("\n\033[96m[INFO]: Analyzing 'TrafficSign' nodes and inserting weights\033[0m")
                # for record in tqdm(result):
                    

                #     # 3.1) Used "Verkehrsverbote" signs to create a weight for the usability of the segment for certain transportation types
                #     # TO DO: This if-comparison is not sufficient, because there are more combinations possible
                #     if record[2]._properties['value'] in codes_restriction or record[2]._properties['value']+"-"+record[3]._properties['value'] in codes_restriction:
                #         #print in green to make it easier to spot in the console
                #         print(f"\033[92mFound TrafficSpace: {record[0]._properties['id']}, \033[0m TrafficSign Code: {record[2]._properties['value']}, TrafficSign Subtype Code: {record[3]._properties['value']}, TrafficSign Value: {record[4]._properties['value']}")
                #         # TO DO: include weight computation and insertion here
                    
                #     # 3.2) Used speed limit signs to create a weight for the usability of the segment for certain transportation types
                #     elif record[2]._properties['value'] in code_speed_limit or record[2]._properties['value']+"-" in code_speed_limit or record[2]._properties['value']+"-"+record[3]._properties['value'] in code_speed_limit:
                #         # print in blue to make it easier to spot in the console
                #         print(f"\033[94mFound TrafficSpace: {record[0]._properties['id']}, \033[0m TrafficSign Code: {record[2]._properties['value']}, TrafficSign Subtype Code: {record[3]._properties['value']}, TrafficSign Value: {record[4]._properties['value']}")
                #         # TO DO: include weight computation and insertion here

                #     # 3.3) Used delay signs to create a weight for the usability of the segment for certain transportation types
                #     elif record[2]._properties['value'] in codes_delay or record[2]._properties['value']+"-" in codes_delay or record[2]._properties['value']+"-"+record[3]._properties['value'] in codes_delay:
                #         # print in purple to make it easier to spot in the console
                #         print(f"\033[95mFound TrafficSpace: {record[0]._properties['id']}, \033[0m TrafficSign Code: {record[2]._properties['value']}, TrafficSign Subtype Code: {record[3]._properties['value']}, TrafficSign Value: {record[4]._properties['value']}")
                #         # TO DO: include weight computation and insertion here

                #     else:
                #         print(f"TrafficSpace: {record[0]._properties['id']}, TrafficSign Code: {record[2]._properties['value']}, TrafficSign Subtype Code: {record[3]._properties['value']}, TrafficSign Value: {record[4]._properties['value']}")

                #     # add all traffic sign UUIDs to the relationship SUCCESSOR_OF
                #     # get the TrafficSpace element id
                #     trafficSpace_id = record[0].id # ._properties['id']
                #     # get the traffic sign UUID
                #     trafficSign_UUID = record[1]._properties['id']
                #     print(f"TrafficSpace: {trafficSpace_id}, TrafficSign UUID: {trafficSign_UUID}")
                #     """
                #     MATCH (n)-[r:SUCCESSOR_OF]->() WHERE ID(n)=$id 
                #     SET r.trafficSignIds = coalesce(r.trafficSignIds, []) + $trafficSignUUID
                #     RETURN n, r;
                #     """
                #     print(type(trafficSpace_id), type(trafficSign_UUID))
                #     # ! To remove set trafficSignIds if the code is run multiple times for test purposes
                #     # remove = session.execute_write(self._remove_trafficSign_UUIDs, [trafficSpace_id])
                #     result = session.execute_write(self._insert_trafficSign_UUIDs, [trafficSpace_id, trafficSign_UUID])

                # ----------------------------------------
                #  Just for metadata analysis and testing
                # TODO: Comment out the following code after testing
                result = session.execute_read(self._get_speed_street_sign_code, [])
                print(f"Number of TrafficSign elements: {len(result)}")
                # [0]: TrafficSpace element
                # [1]: TrafficSign element
                # [2]: TrafficSign code
                # [3]: TrafficSign subtype code
                # [4]: TrafficSign value

                # Get the speed limit for each TrafficSpace element
                print("\n\033[96m[INFO]: Analyzing 'TrafficSign' nodes and inserting weights\033[0m")
                for record in tqdm(result):
                    speed_limit = float(record[4]._properties['value'])
                    print(f"Speed limit for {record[0]._properties['id']}: {speed_limit}")
                # ----------------------------------------
                    

                result = session.execute_write(self._insert_speed_limit_streetSign_shortcut, [])

                # TODO: Find all successors of the TrafficSpace nodes with no connection to the speed limit street sign and add the connection shortcut. If there is a connection to a different speed street sign, then use this one for the shortcut and continue.
                # 
                # TODO: After the connection shortcuts are added, add their maximum speed limit to the SUCCESSOR_OF relationship as a weight property. This is stored as a property in the relationship to the speed limit street sign node already for easier access. 



                print("\n\033[96m[INFO]: Adding weights to 'TrafficSpace' nodes\033[0m")
                # TODO: 3.4) Create final weight for traversal time of a segment used for routing which includes information about the transportation type, speed limits, waiting times and delays, inclination, and restrictions

            if query == "speed_limits":
                """Add speed limit information to the TrafficSpace nodes
                This uses the street sign information for the DRIVING or BIDIRECTIONAL transportation type and the assumption values from the config file for the other transportation types"""

                # Get all Driving or bidirectional TransportationType nodes with a connection to a speed limit street sign
                # MATCH p=(n WHERE WHERE n.transportation_type in["BIDIRECTIONAL","DRIVING"])-[r:SPEED_LIMIT_SIGN]->() RETURN n
                # Advance this query:
                # Add a speed limit property to the TrafficSpace SUCCESSOR_OF relationship of those nodes
                # query = """MATCH p=(n WHERE WHERE n.transportation_type in["BIDIRECTIONAL","DRIVING"])-[r:SPEED_LIMIT_SIGN]->(m) 
                # WITH n, r
                # MATCH (n)-[r2:SUCCESSOR_OF]->()
                # SET r2.speed_limit = r.value
                # RETURN n"""

                result = session.execute_write(self._insert_speed_limit_property, [])
                
                # Follow each SUCCESSOR_OF relationship and add the speed limit property to the next SUCCESSOR_OF relationship until the end of the path is reached or a speed limit is already set

                # Python code
                for record in result: # of previous query
                # test if the speed limit is already set
                    # query = MATCH (n WHERE n.id=$id)-[:SUCCESSOR_OF]->(m)-[r:SUCCESSOR_OF]->(l)  RETURN r.speed_limit
                    speed_limit_available = False
                    speed_limit_set = session.execute_read(self._test_speed_limit_set, [record[0]._properties['id']])
                    print(f"[INFO] Starting at {record[0]._properties['id']}")
                    speed_limit = int(record[1])
                    index = 0
                    while not speed_limit_available:
                        if len(speed_limit_set) == 0:
                            print("No more successors")
                            break
                        # print(speed_limit_set)
                        if speed_limit_set[0][1] == None:
                            index = index+1
                            print(f"[{index}] Speed limit not set")
                            #  TODO: Set the speed limit property on the SUCCESSOR_OF relationship of those nodes
                            session.execute_write(self._set_speed_limit_property, [speed_limit_set[0][0], speed_limit])
                            speed_limit_set = session.execute_read(self._test_speed_limit_set, [speed_limit_set[0][0]])
                        else:
                            print("Speed limit set")
                            speed_limit_available = True
                            break
                # Find remaining DRIVING and BIDIRECTIONAL TransportationType nodes without a set speed_limit property on their SUCCESSOR_OF relationship
                # query = """MATCH p=(n WHERE n.transportation_type in ["DRIVING", "BIDIRECTIONAL"])-[r:SUCCESSOR_OF]->() WHERE(r.speed_limit IS NULL)
                # SET r.speed_limit = $driving_speed_limit
                # RETURN n"""
                # Set a default speed limit property on the SUCCESSOR_OF relationship of those nodes, e.g. 50 km/h
                # load the default speed limit values from the json config file
                configurations = None
                with open('config.json') as f:
                    configurations = json.load(f)

                car_speed_limit = configurations["transportation_modes"]["car"]["speed"]
                bike_speed_limit = configurations["transportation_modes"]["bike"]["speed"]
                pedestrian_speed_limit = configurations["transportation_modes"]["walking"]["speed"]
                parking_speed_limit = configurations["transportation_modes"]["parking"]["speed"]
                print(f"[INFO] Adding default speed limit {car_speed_limit}km/h as a property to the remaining SUCCESSOR_OF relationships of type DRIVING and BIDIRECTIONAL")
                session.execute_write(self._set_default_speed_limit_property, [["DRIVING", "BIDIRECTIONAL"], car_speed_limit])
                # Set speed_limit property on the other TransportationType nodes
                # query = MATCH p=(n WHERE n.transportation_type="SIDEWALK")-[r:SUCCESSOR_OF]->() 
                # SET r.speed_limit = $sidewalk_speed_limit
                # query = MATCH p=(n WHERE n.transportation_type="BICYCLE")-[r:SUCCESSOR_OF]->()
                # SET r.speed_limit = $bicycle_speed_limit
                print(f"[INFO] Adding default speed limit properties to the SUCCESSOR_OF relationships of SIDEWALK ({pedestrian_speed_limit}km/h), BICYCLE ({bike_speed_limit}km/h), and PARKING ({parking_speed_limit}km/h)")
                session.execute_write(self._set_default_speed_limit_property, [["BIKING"], bike_speed_limit])
                session.execute_write(self._set_default_speed_limit_property, [["SIDEWALK"], pedestrian_speed_limit])
                session.execute_write(self._set_default_speed_limit_property, [["PARKING"], parking_speed_limit])

                others_speed_limit = 0.1
                print(f"[INFO] Adding default speed limit properties to the SUCCESSOR_OF relationships of SHOULDER and STOP ({others_speed_limit}km/h)")
                session.execute_write(self._set_default_speed_limit_property, [["SHOULDER", "STOP"], others_speed_limit])

            if query == "successor_of_properties":
                # add the properties to the SUCCESSOR_OF relationships
                # get the relationship and the available weighting info
                result = session.execute_read(self._get_successor_of_relationships, [])
                for record in result:
                    # speed
                    if record[2]._properties['speed_limit'] == 0:
                        speed_weight = 1/0.1
                    else:
                        speed_weight = 1 / record[2]._properties['speed_limit']
                    # inclination
                    inclination_weight = record[2]._properties['inclination'] +100
                    # width
                    width_weight = 1 / record[2]._properties['min_width']
                    # time 
                    time_weight = record[2]._properties['advanced_segment_length'] / (record[2]._properties['speed_limit']/3.6) # in seconds

                    # insert the properties
                    session.execute_write(self._insert_successor_of_properties, [record[2].id, speed_weight, inclination_weight, width_weight, time_weight])

        session.close() # TODO: Check if this is necessary

    def insert_SWITCH_TO_relation(self, node1_id, node2_id):
        with self.driver.session() as session:
            session.execute_write(self._insert_SWITCH_TO_relation, [node1_id, node2_id])

    def insert_parking_garage_entrance_connection(self):
        with self.driver.session() as session:
            session.execute_write(self._insert_parking_garage_entrance_connection, [])


    def find(self, query, vars=[]):
        with self.driver.session() as session:
            result = []
            if query == "sections":
                result = session.execute_read(self._find_sections, vars)
                return [int(record.element_id.split(":")[-1]) for record in result]
            if query == "traffic_spaces":
                result = session.execute_read(self._find_traffic_spaces, vars)
                print(f"Number of TrafficSpace elements: {len(result)}")
                return [record["id"] for record in result]
            if query == "traffic_area":
                result = session.execute_read(self._find_traffic_area, vars)
                return [record["id"] for record in result]
            if query == "lane_information":
                result = session.execute_read(self._find_lane_information, vars)
                return result
            if query == "parking_auxiliary_areas":
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
            
            if query == "traffic_sign_info":
                result = session.execute_read(self._get_traffic_sign_info, [])
                # for record in result:
                #     print(record)
                return result

            for record in result:
                # print found in green to make it easier to spot in the console
                print("\n\033[92mFound:\033[0m {record}".format(record=record))

    def create(self, query):
        if query == "lane_changes":
            sections = self.find("sections")
            # find all trafficSpaces for each section
            for section_id in tqdm(sections):
                print(f"\nSection ID: {section_id}")
                section_traffic_spaces = self.find("traffic_spaces", [section_id])
                # find all trafficAreas for each trafficSpace
                traffic_areas = []
                traffic_areas += [self.find("traffic_area", [traffic_space_id]) for traffic_space_id in section_traffic_spaces]
                tmp = []
                for traffic_areas_id in traffic_areas:
                    tmp += traffic_areas_id
                traffic_areas = tmp

                section_lane_information = []
                # find lane information for each trafficArea
                for traffic_area_id in traffic_areas:
                    lane_information = self.find("lane_information", [traffic_area_id])
                    if type(lane_information) == list:
                        lane_information.insert(0, traffic_area_id)
                        section_lane_information.append(lane_information)

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
                
                # print("\n=====================================\nNeighbouring lanes:\n=====================================\n")
                lanes_to_connect = []
                neighbouring_lanes = []
                neighbouring_lanes_pos = []
                neighbouring_lanes_neg = []
                for i, el in enumerate(neighbouring_lanes_same_type):
                    if el[3] < 0:
                        # print("\033[94m" + str(el) + "\033[0m")
                        if i < len(neighbouring_lanes_same_type)-1 and el[1] == neighbouring_lanes_same_type[i+1][1] and el[2] == neighbouring_lanes_same_type[i+1][2] and el[4] == neighbouring_lanes_same_type[i+1][4]:
                            neighbouring_lanes.append(el)
                        elif  i > 0 and el[1] == neighbouring_lanes_same_type[i-1][1] and el[2] == neighbouring_lanes_same_type[i-1][2] and el[4] == neighbouring_lanes_same_type[i-1][4]:
                            neighbouring_lanes.append(el)
                            lanes_to_connect.append(neighbouring_lanes)
                            neighbouring_lanes = []
                    if el[3] > 0:
                        # print("\033[92m" + str(el) + "\033[0m")
                        
                        if i < len(neighbouring_lanes_same_type)-1 and el[1] == neighbouring_lanes_same_type[i+1][1] and el[2] == neighbouring_lanes_same_type[i+1][2] and el[4] == neighbouring_lanes_same_type[i+1][4]:
                            neighbouring_lanes.append(el)
                        elif  i > 0 and el[1] == neighbouring_lanes_same_type[i-1][1] and el[2] == neighbouring_lanes_same_type[i-1][2] and el[4] == neighbouring_lanes_same_type[i-1][4]:
                            neighbouring_lanes.append(el)
                            lanes_to_connect.append(neighbouring_lanes)
                            neighbouring_lanes = []
                    
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
                # print("\n=====================================\nCreating relationships between lanes:\n=====================================\n")   
                print("[INFO] Creating relationships between lanes")   
                for block in lanes_to_connect_by_direction:
                    if len(block) == 2:
                        self.insert("lane_changes", block)
                    elif len(block) > 2:
                        for i in range(len(block)-1):
                            self.insert("lane_changes", [block[i], block[i+1]])
        if query == "predecessor_shortcut":
            # print("\n\033[96m[INFO]: Inserting the predecessor shortcut relationship: 'PREDECESSOR_OF'\033[0m")
            self.insert("predecessor_shortcut", [])
        if query == "successor_shortcut":
            # print("\n\033[96m[INFO]: Inserting the successor shortcut relationship: 'SUCCESSOR_OF'\033[0m")
            self.insert("successor_shortcut", [])

        if query == "transport_mode_switch":
            print("\n\033[96m[INFO]: Inserting the transport mode switch relationships: 'SWITCH_TO_PARKING' and 'SWITCH_TO' \033[0m")
            self.find("parking_auxiliary_areas", [])
        
        if query == "weight_attributes":
            # add advanced distance attribute to the relationships
            self.insert("advanced_distance_weight", [])
            # add distance attribute to the relationships
            self.insert("distance_weight", [])
            # add inclination attribute to the relationships
            self.insert("inclination", [])
            # add min width attribute to the relationships
            self.insert("min_width", [])
            # add properties for SUCCESSOR_OF relationships
            self.insert("successor_of_properties", [])
            self.insert("add_bidirectional_successor_of_2_weights", [])
            # add lane change attributes to the relationships
            self.insert("lane_change_attributes", [])
            # add weights to switch_to and switch_to_parking relationships
            self.insert("transport_mode_switch", [])

        # add transportation type to the nodes
        if query == "transportation_type":
            self.insert("add_transportation_type", [])
        # add bidirectional successor relationships
        if query == "bidirectional_successor_relationship":
            self.insert("add_bidirectional_successor_relationship", [])

    def get_metadata_information(self):
        """ Analyse the whole dataset and print the metadata information such as
            - Number of nodes
            - Number of relationships
            - Number of TrafficSpace Nodes
            - Number of TrafficArea Nodes 
            - Number of TrafficSign Nodes
            - Number of AuxiliaryTrafficSpace Nodes
            - Number of AuxiliaryTrafficArea Nodes 
            - Number of Predecessor relationships 
            - Number of Successor relationships
            - Number of Neighbours relationships
            - Number of SwitchTo relationships
            - Number of SwitchToParking relationships
            - Total length of the road network
            - Total length of the road network by type (DRIVING, SIDEWALK, BIKING, SHOULDER, OTHER)
            - Bounding Box of the city model
            - Area covered by the city model in km^2
            """
        
        with self.driver.session() as session:
            res_metadata = session.execute_read(self._get_metadata_information, [])
            metadata_labels = ["labelCount", "relTypeCount", "propertyKeyCount", "nodeCount", "relCount", "labels", "relTypes", "relTypesCount", "stats"]
            for label, res in zip(metadata_labels, res_metadata[0]):
                print(f"\n\033[92m{label}:\033[0m {res}")
            # print(res_metadata)
            added_relationship_types = ["SUCCESSOR_OF", "PREDECESSOR_OF", "NEIGHBOURS_LANE", "SWITCH_TO", "SWITCH_TO_PARKING"]
            for rel_type in added_relationship_types:
                print(f"\033[92mNumber of {rel_type} relationships:\033[0m {res_metadata[0][7][rel_type]}")

            # get the sum of all TrafficSpace lengths
            # find all sections
            result = session.execute_read(self._find_trafficSpace_ids, vars)
            print(f"Number of TrafficSpace elements: {len(result)}")
            # for record in result:
            #     print(record)

            total_dist = 0
            trafficSpace_dists = []
            types_dict = {}
            print("\n\033[96m[INFO]: Calculating length of 'SUCCESSOR_OF' relationships\033[0m")
            for id in tqdm(result):
                # not all TrafficSpace objects have a gml UUID, therfore check if there is a string containing the UUID
                # check if the id is a string and follows the UUID pattern
                # if type(id) == str and is_valid_uuid(id):
                dist = 0
                if type(id) == str:
                    coord_node, types = session.execute_read(self._find_trafficSpace_geometry_and_type, [id])
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
                        sorted_coords = sorted(record._properties.items(), key=lambda x: x[0])

                        # create 3D points from the sorted coordinates
                        points=[]
                        for x, y, z in zip(sorted_coords[0::3], sorted_coords[1::3], sorted_coords[2::3]):
                            points.append([float(x[1]), float(y[1]), float(z[1])])
                        
                        # calculate the distance between two following points and add it to the total distance
                        for i in range(len(points)-1):
                            dist += euclidean_distance(points[i], points[i+1])

                        trafficSpace_type = types[0]
                        # if the trafficSpace_type is not in the types_dict add it to the dict with the value of the distance otherwise add the distance to the existing value
                        if trafficSpace_type not in types_dict:
                            types_dict[trafficSpace_type] = dist
                        else:
                            types_dict[trafficSpace_type] += dist

                        total_dist += dist
                        trafficSpace_dists.append(dist)
                    # result = session.execute_write(self._insert_advanced_distance, [id, dist])
            print(f"\033[96m[INFO] Total length of all TrafficSpace objects: {round(total_dist, 2)} meters \033[0m")
            for key, value in types_dict.items():
                print(f"\033[96m[INFO] Total length of of {key} TrafficSpace: {round(value, 2)} meters \033[0m")
            
            # get the bounding box of the city model
            print("\n\033[96m[INFO]: Retrieving bounding box of the city model\033[0m")
            bounding_box = session.execute_read(self._get_bounding_box, [])
            upperCorner = [float(bounding_box[0][0]._properties['ARRAY_MEMBER[0]']), float(bounding_box[0][0]._properties['ARRAY_MEMBER[1]']), float(bounding_box[0][0]._properties['ARRAY_MEMBER[2]'])]
            lowerCorner = [float(bounding_box[0][1]._properties['ARRAY_MEMBER[0]']), float(bounding_box[0][1]._properties['ARRAY_MEMBER[1]']), float(bounding_box[0][1]._properties['ARRAY_MEMBER[2]'])]
            coordinate_system = int(bounding_box[0][2].split("::")[-1])
            print(f"\033[96m[INFO] Coordinate System: EPSG {coordinate_system} \033[0m")
            print(f"\033[96m[INFO] Upper Corner: {upperCorner} \033[0m")
            print(f"\033[96m[INFO] Lower Corner: {lowerCorner} \033[0m")

            # Calculate the covered area in square kilometers from the UTM coordinates
            area = (upperCorner[0] - lowerCorner[0]) * (upperCorner[1] - lowerCorner[1]) / 1000000
            print(f"\033[96m[INFO] Covered area: {round(area, 2)} square kilometers \033[0m")
            
            





# ========================================================================
# =========================== Neo4j Navigator ============================
# ========================================================================

# Navigation class
class Neo4jNavigator:

    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.config_file = 'config.json'
        self.config_data = self.load_config()
        # get the available transportation options
        self.transportation_options = self.config_data['transportation_modes'].keys()
        print(f"[INFO] Available transportation options: {self.transportation_options}")
        # retrieve the start and destination coordinates from the config file
        self.start_coords = [self.config_data['start']['lat_grafing'], self.config_data['start']['lon_grafing']]
        self.destination_coords = [self.config_data['destination']['lat_grafing'], self.config_data['destination']['lon_grafing']]
        self.start_location = list(utm.from_latlon(self.config_data['start']['lat_grafing'], self.config_data['start']['lon_grafing'])[:2])
        self.destination_location = list(utm.from_latlon(self.config_data['destination']['lat_grafing'], self.config_data['destination']['lon_grafing'])[:2])

        # Uncomment for May Ingolstadt Database
        # self.start_coords = [self.config_data['start']['lat'], self.config_data['start']['lon']]
        # self.destination_coords = [self.config_data['destination']['lat'], self.config_data['destination']['lon']]
        # self.start_location = list(utm.from_latlon(self.config_data['start']['lat'], self.config_data['start']['lon'])[:2])
        # self.destination_location = list(utm.from_latlon(self.config_data['destination']['lat'], self.config_data['destination']['lon'])[:2])

        # print(f"[INFO] Start location: {self.start_location}, Destination location: {self.destination_location}")
        # self.trafficSpace_ids = self.get_nearest_TrafficSpace_id([self.start_location, self.destination_location])
        # print(f"[INFO] TrafficSpace IDs: {self.trafficSpace_ids}")

        # self.generate_kd_tree()

    def load_config(self):
        with open(self.config_file, 'r') as config_file:
            config_data = json.load(config_file)
        # Print the config file
        pprint(config_data, sort_dicts=False)
        # print(config_data)
        print("[INFO] Config file loaded successfully!")
        return config_data

    def close(self):
        self.driver.close()

    @staticmethod
    def _find_shortest_path_apoc_djikstra(tx, vars):
        # //APOC Djikstra: Find shortest path between start and end node using SUCCESSOR_OF and NEIGHBOURS_LANE shortcut and segment_length weight MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_666b845a-0860-3849-b81c-0b47c663b6aa'}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_f66d4bd1-d97e-39a8-a712-1459ae9ca30b'}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF|NEIGHBOURS_LANE>', 'segment_length') yield path as path, weight as weight RETURN path, weight
        result = tx.run("MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id1}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id2}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF>|SUCCESSOR_OF_2>|NEIGHBOURS_LANE>', 'advanced_segment_length') yield path as path, weight as weight RETURN path, weight", id1=vars[0], id2=vars[1]) #advanced_segment_length, euclidean_segment_length, inclination, width  # TODO: Change the weight to the final routing weight

        for record in result:
            if len([record['path'], record['weight']]) == 2:
                return [record['path'], record['weight']]
    
    @staticmethod
    def _find_shortest_path_apoc_djikstra_multimodal(tx, vars):
        # //APOC Djikstra: Find shortest path between start and end node using SUCCESSOR_OF and NEIGHBOURS_LANE shortcut and segment_length weight MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_666b845a-0860-3849-b81c-0b47c663b6aa'}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_f66d4bd1-d97e-39a8-a712-1459ae9ca30b'}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF|NEIGHBOURS_LANE>', 'segment_length') yield path as path, weight as weight RETURN path, weight
        result = tx.run("MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id1}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id2}) CALL apoc.algo.dijkstra(from, to, 'SUCCESSOR_OF>|SUCCESSOR_OF_2>|NEIGHBOURS_LANE>|SWITCH_TO_PARKING>|SWITCH_TO>', $weight) yield path as path, weight as weight RETURN path, weight", id1=vars[0], id2=vars[1], weight=vars[2]) #advanced_segment_length, euclidean_segment_length, inclination, width  # TODO: Change the weight to the final routing weight
        for record in result:
            if len([record['path'], record['weight']]) == 2:
                return [record['path'], record['weight']]
                
    @staticmethod
    def _find_shortest_path_apoc_astar_multimodal(tx, vars):
        result = tx.run("MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id1}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:$id2}) CALL apoc.algo.aStar(from, to, 'SUCCESSOR_OF>|SUCCESSOR_OF_2>|NEIGHBOURS_LANE>|SWITCH_TO_PARKING>|SWITCH_TO>', $weight, 'x', 'y') yield path as path, weight as weight RETURN path, weight", id1=vars[0], id2=vars[1], weight=vars[2])
        
        for record in result:
            if len([record['path'], record['weight']]) == 2:
                return [record['path'], record['weight']]

    @staticmethod
    def _find_trafficSpace_ids(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` ) RETURN n.id as gmlid;")
        return [record["gmlid"] for record in result]
    
    @staticmethod
    def _find_trafficSpace_geometry(tx, vars):
        result = tx.run('MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[:lod2MultiCurve]-()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(m) RETURN m;', id=vars[0])
        return [record["m"] for record in result]

    @staticmethod
    def _get_coordinates_traffic_space(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id= $id)-[:lod2MultiCurve]->()-[:object]-()-[:curveMember]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-()-[:controlPoints]-()-[:posList]-()-[:value]-()-[:elementData]-(coords)  RETURN coords;", id = vars)
        return [record["coords"] for record in result]
    
    @staticmethod
    def _get_distance_between_traffic_spaces(tx, vars):
        result = tx.run("MATCH  (n WHERE n.id=$id1)-[r:SUCCESSOR_OF|NEIGHBOURS_LANE|SWITCH_TO|SWITCH_TO_PARKING]-(m WHERE m.id=$id2) RETURN r.euclidean_segment_length as distance;", id1=vars[0], id2=vars[1])
        return [record["distance"] for record in result]

    @staticmethod
    def _get_relationships_between_traffic_spaces(tx, vars):
        result = tx.run("MATCH  (n WHERE n.id=$id1)-[r:SUCCESSOR_OF|NEIGHBOURS_LANE|SWITCH_TO|SWITCH_TO_PARKING]-(m WHERE m.id=$id2) RETURN r as relationship;", id1=vars[0], id2=vars[1])
        return [record["relationship"] for record in result]

    @staticmethod
    def _get_traffic_space_reference_direction(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id)-[r:trafficDirection]-(m) RETURN m.value as direction;", id=vars[0])
        return [record["direction"] for record in result]
    
    @staticmethod
    def _get_transportation_type_node(tx, vars):
        result = tx.run("MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id=$id) RETURN n.transportation_type as type;", id=vars[0])
        return [record["type"] for record in result]
    
    @staticmethod
    def _get_bounding_box(tx, vars):
        result = tx.run("""
        MATCH (n:`org.citygml4j.core.model.core.CityModel`)-[:boundedBy]-()-[:envelope]-(e)
        WITH e
        MATCH (e)-[:upperCorner]-()-[:value]-()-[:elementData]-(a)
        WITH e, a
        MATCH (e)-[:lowerCorner]-()-[:value]-()-[:elementData]-(b)
        RETURN a as upperCorner, b as lowerCorner, e.srsName;
        """)
        return [record for record in result]
        

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

    def generate_kd_tree(self):
        # Print info message in blue to console
        print("\033[96m[INFO]: Generating kdTree from TrafficSpace coordinates\033[0m")
        coordinate_list, self.id_list=self.find_all_coordinates()
        print(f"Number of points: {len(coordinate_list)}")

        # add points to open3d point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(coordinate_list) 

        # create kdTree from point cloud
        self.kdTree = o3d.geometry.KDTreeFlann(pcd)

    def get_nearest_TrafficSpace_id(self, coordinates):

        # coordinate_list, self.id_list=self.find_all_coordinates()
        # print(f"Number of points: {len(coordinate_list)}")

        # # add points to open3d point cloud
        # pcd = o3d.geometry.PointCloud()
        # pcd.points = o3d.utility.Vector3dVector(coordinate_list) 

        # # create kdTree from point cloud
        # self.kdTree = o3d.geometry.KDTreeFlann(pcd)

        ids = []

        for point in coordinates:
            idx = self.get_nearest_points_kd_tree(point)
            ids.append(self.id_list[idx[0]])
        return ids
    
    def get_nearest_points_kd_tree(self, point):
        # create numpy ndarray from list
        if len(point) == 2:
        # if a point has 2 coordinates, add a 0.0 as the third coordinate
            print("\033[93m[WARN] The point has only 2 coordinates, (0.0) was added as the height!\033[0m")          
            # point.append(0.0)
            point.append(0)

        # if a point does not have 3 coordinates, raise an error
        elif len(point) != 3:
            raise ValueError("The point must have 2 or 3 values [x, y] or [x, y, z]!")
        print(point)
        new_point = np.array(point)
        print(f"Using point: {new_point}")

        # find the nearest neighbor of point1
        [k, idx, _] = self.kdTree.search_knn_vector_3d(new_point, 1)
        # print(f"K: {k}, Index: {idx}")
        # print the coordinates of the nearest neighbor
        # print(f"The nearest node is: {coordinate_list[idx[0]]}, the corresponding TrafficSpace object has the \nID: \033[92m {id_list[idx[0]]} \033[0m")
        print(f"Id: {idx}")
        return idx

    def get_TrafficSpace_geometry_coordinates(self, uuid, direction):
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
                if direction=='backwards': 
                    # sorted_points = sorted_points.reverse()
                    reverser = slice(None, None, -1)
                    reversed_list = sorted_points[reverser]
                    return reversed_list
                return sorted_points 
    
    def get_relationships_between_traffic_spaces(self, uuid1, uuid2):
        with self.driver.session() as session:
            result = session.execute_read(self._get_relationships_between_traffic_spaces, [uuid1, uuid2])
            # for record in result:
            #     print(record)
        return result
    

    # def get_traffic_space_reference_direction(self, uuid):
    #     with self.driver.session() as session:
    #         result = session.execute_read(self._get_traffic_space_reference_direction, uuid)
    #     return result

    def get_bounding_box(self):
        with self.driver.session() as session:
            bounding_box = session.execute_read(self._get_bounding_box, [])
            upperCorner = [float(bounding_box[0][0]._properties['ARRAY_MEMBER[0]']), float(bounding_box[0][0]._properties['ARRAY_MEMBER[1]']), float(bounding_box[0][0]._properties['ARRAY_MEMBER[2]'])]
            lowerCorner = [float(bounding_box[0][1]._properties['ARRAY_MEMBER[0]']), float(bounding_box[0][1]._properties['ARRAY_MEMBER[1]']), float(bounding_box[0][1]._properties['ARRAY_MEMBER[2]'])]
            return [upperCorner, lowerCorner]

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
            print(f"\033[94mRouting over {len(nodes)} nodes with a total weight of {result[1]}!\033[0m") # type: ignore
            return [path._nodes, result[1]]
    
    def shortest_path_APOC_dijkstra_multimodal(self, vars):
        print("Searching for the shortest_path using APOC Djikstra")
        with self.driver.session() as session:
            result = session.execute_read(self._find_shortest_path_apoc_djikstra_multimodal, vars)            
            # throw an error if the result is None
            if result is None:
                print("\033[91m[ERROR] No shortest path could be found!\033[0m")
                # raise ValueError("\033[91m[ERROR] No shortest path could be found!\033[0m")
                return [None, None]

            path = result[0] # type: ignore           
            for node in path._nodes:
                print(node['id'])
            nodes = path.nodes
            print(f"\033[94mRouting over {len(nodes)} nodes with a total weight of {result[1]}!\033[0m") # type: ignore
            return [path._nodes, result[1]]
        
    def shortest_path_APOC_astar(self, ids):
        print("Searching for the shortest_path using APOC A*")
        with self.driver.session() as session:
            result = session.execute_read(self._find_shortest_path_apoc_astar_multimodal, ids)            
            # throw an error if the result is None
            if result is None:
                # raise ValueError("\033[91m[ERROR] No shortest path could be found!\033[0m")
                print("\033[91m[ERROR] No shortest path could be found!\033[0m")
                return [None, None]

            path = result[0]
            for node in path._nodes:
                print(node['id'])
            nodes = path.nodes
            print(f"\033[94mRouting over {len(nodes)} nodes with a total weight of {result[1]}!\033[0m") # type: ignore
            return [path._nodes, result[1]]
    
    # def visualize_shortest_path_folium(self, path_nodes, weight):
    #     print("[INFO] Creating Visualization...")
    #     path_found = True
    #     if len(path_nodes) == 0:
    #         path_found = False
        
    #     geometry = []
    #     for node in path_nodes:
    #         uuid = node['id']
    #         geometry.extend(self.get_TrafficSpace_geometry_coordinates(uuid))
    #         # print(len(geometry))
    #         # geometry.extenjd(geometry)

    #     # convert the coordinates to lat, lon
    #     geometry_converted = [utm.to_latlon(point[0], point[1], 32, 'U') for point in geometry]

    #     # create map object
    #     m = folium.Map(location=self.start_coords, zoom_start=16, tiles='CartoDB positron', zoom_control=True, control_scale=True, )
    #     plugins.Geocoder(position='topright').add_to(m)
    #     # add zoom control
    #     # folium.zoom_control(position='topleft').add_to(m)
    #     # fit maker bounds
    #     m.fit_bounds([self.start_coords, self.destination_coords])

    #     if path_found:
    #         folium.PolyLine(geometry_converted,
    #                 color='#0065bd',
    #                 weight=3,
    #                 opacity=0.8).add_to(m)
    #         # fit bounds
    #         m.fit_bounds([[min([point[0] for point in geometry_converted]), min([point[1] for point in geometry_converted])], [max([point[0] for point in geometry_converted]), max([point[1] for point in geometry_converted])]])            

    #     start_popup = folium.Popup(f'<b>Start</b><br>TrafficSpace ID:<br> {self.trafficSpace_ids[0]}', max_width=300, show=True)
    #     folium.Marker(self.start_coords, popup=start_popup, icon=folium.Icon(color='green')).add_to(m)
    #     destination_popup = folium.Popup(f'<b>Destination</b><br>TrafficSpace ID:<br> {self.trafficSpace_ids[1]}', max_width=300, show=True)
    #     folium.Marker(self.destination_coords, popup=destination_popup, icon=folium.Icon(color='red')).add_to(m)
        
    #     # add fullscreen button
    #     plugins.Fullscreen(
    #         position='topleft',
    #         title='Fullscreen',
    #         title_cancel='Exit fullscreen',
    #         force_separate_button=True
    #     ).add_to(m)

    #     plugins.LocateControl(position='topleft', drawCircle=False, flyTo=True, strings={'title': 'Locate Me!'}).add_to(m)
    #     plugins.MousePosition(position='bottomright', empty_string='hover over map', separator=' | ').add_to(m)
    #     # add minimap
    #     minimap = plugins.MiniMap(toggle_display=True, width=100, height=100, minimized=True, zoom_level_offset=-5) # tile_layer='CartoDB positron',
    #     m.add_child(minimap)

    #     # save map
    #     m.save('web/map.html')

    #     # use BeautifulSoup to add the routing distance to the results div in the html file
    #     with open("web/index.html", encoding='utf-8') as fp:
    #         soup = BeautifulSoup(fp, "html.parser")
    #         # print(soup.prettify())
    #         # print(soup.find(id="results"))
    #         if path_found:
    #             original_div = soup.find("div", {"id": "results"})
    #             original_div.string = f'The shortest path has a length of '
    #             result_span = soup.new_tag("span", style="color:#e35e05;", id="result-weight")
    #             result_span.string = f'{round(weight,2)}'
    #             original_div.append(result_span)
    #             original_div.append(" meters.")
    #         else:
    #             original_div = soup.find("div", {"id": "results"})
    #             new_span = soup.new_tag("span", style="color:#e35e05;", id="result-weight")
    #             new_span.string = f'No path found!'
    #             original_div.string = ""
    #             original_div.append(new_span)
    #         # print(soup.prettify())
    #     with open("web/index_output.html", "w", encoding='utf-8') as fp:
    #         fp.write(soup.prettify())

    

    def visualize_shortest_path_leaflet(self, path_nodes, weight):
            print("[INFO] Creating Visualization...")
            path_found = True
            if len(path_nodes) == 0:
                path_found = False
            distance = 0
            relationship_types = []
            reference_direction = []
            transportation_type = []
            #  retrieve a list of the relationship types used for the routing as well as the distance associated with each relationship
            
            print("[INFO] Retrieving information about the route...")
            with self.driver.session() as session:
                for i in tqdm(range(len(path_nodes)-1)):
                    res = session.execute_read(self._get_distance_between_traffic_spaces, [path_nodes[i]['id'], path_nodes[i+1]['id']])
                    distance += res[0]
                    
                    res = session.execute_read(self._get_relationships_between_traffic_spaces, [path_nodes[i]['id'], path_nodes[i+1]['id']])
                    relationship_types.append(res[0].type) # ! this has an issue if multiple relationships are found between two nodes, however this should not happen in the current data model
                    # get the reference direction of the node
                    res = session.execute_read(self._get_traffic_space_reference_direction, [path_nodes[i]['id']])
                    if len(res) == 0:
                        # if the reference direction is empty, add the reference direction of "forwards"
                        reference_direction.append("forwards")
                    else:
                        reference_direction.append(res[0])
                    
                    # retrieve the transportation type of the node
                    res = session.execute_read(self._get_transportation_type_node, [path_nodes[i]['id']])
                    transportation_type.append(res)

                res = session.execute_read(self._get_traffic_space_reference_direction, [path_nodes[-1]['id']])
                # reference_direction.append(res[0])
                if len(res) == 0:
                    # if the reference direction is empty, add the reference direction of "forwards"
                    reference_direction.append("forwards")
                else:   
                    reference_direction.append(res[0])
                # retrieve the transportation type of the node
                res = session.execute_read(self._get_transportation_type_node, [path_nodes[-1]['id']])
                transportation_type.append(res)


            geometry = []
            geometry_path = []
            transportation = []
            
            
            for idx, node in enumerate(path_nodes):
                uuid = node['id']
                if idx == 0:
                    # just add the first geometries coordinates as they belong to the start node
                    # pass
                    geometry_values = self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])
                if idx == len(path_nodes)-1:
                    # just add the last geometries coordinates as they belong to the destination node
                    # pass
                    geometry_values = self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])

                else:
                    if relationship_types[idx] == "SUCCESSOR_OF":
                        # retrieve the geometry values of the current node
                        # pass
                        geometry_values = self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])
                    elif relationship_types[idx] == "SUCCESSOR_OF_2":
                        geometry_values = self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])
                        print("[INFO] Using the geometry of the SUCCESSOR_OF_2 relationship")
                    elif relationship_types[idx] == "NEIGHBOURS_LANE":
                        # just add the start point of the geometry to avoid showing the geometries of the two neighbouring lanes
                        geometry_values = [self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])[0]]
                        pass
                    elif relationship_types[idx] == "SWITCH_TO":
                        # TODO add the geometry of the switch_to relationship and the "SWITCH_TO_PARKING" relationship
                        pass
                    elif relationship_types[idx] == "SWITCH_TO_PARKING":
                        # TODO add the geometry of the switch_to relationship and the "SWITCH_TO_PARKING" relationship
                        pass
                    else:
                        raise NotImplementedError(f"\033[91m[ERROR] The relationship type {relationship_types[idx]} is not implemented yet!\033[0m")
                    
                
                # geometry_values = self.get_TrafficSpace_geometry_coordinates(uuid, reference_direction[idx])
                if geometry_values is not None:
                    # geometry.extend(geometry_values)
                    # collect all geometry values in a list if the transportation type is the same as the previous one
                    if idx < len(path_nodes)-1:
                        if len(transportation_type[idx]) == 0:
                            pass
                        elif transportation_type[idx] == transportation_type[idx+1]:
                            geometry_path.extend(geometry_values)
                        else:
                            # BUG: If the last geometry is added, some strange artefacts appear in the map visualization. However, if it is not added, the last geometry is missing after some bidirectional connections
                            # geometry_path.extend(geometry_values)

                            geometry.append(geometry_path)
                            geometry_path = []
                            transportation.append(transportation_type[idx])
                    else:
                        # geometry.append(geometry_values)
                        geometry_path.extend(geometry_values)
                        geometry.append(geometry_path)
                        transportation.append(transportation_type[-1])
                    
                else:
                    raise ValueError(f"\033[91m[ERROR] No geometry values found for the TrafficSpace with the ID: {uuid}!\033[0m")
            # geometry_path.extend(geometry_values)
            # geometry.append(geometry_path)
            # transportation.append(transportation_type[-1])

            # this needs to be done in a loop as the geometry is a list of lists
            # convert the coordinates to lat, lon
            # geometry_converted = [utm.to_latlon(point[0], point[1], 32, 'U') for point in geometry]
            geometry_converted = []
            for geometry_list in geometry:
                # geometry_converted.append([utm.to_latlon(point[0], point[1], 32, 'U') for point in geometry_list])
                geometry_converted.append([utm.to_latlon(point[0], point[1], 32, 'U') for point in geometry_list])
            

            print(f"Number of nodes: {len(path_nodes)} | Number of segments: {len(geometry)}")
            print("[INFO] Generating map html code...")
            # add_results_to_map(self.start_coords, self.destination_coords, geometry_converted, distance, weight, transportation_type)
            add_results_to_map(self.start_coords, self.destination_coords, geometry_converted, distance, weight, transportation)
            print("[INFO] Map html code generated successfully!")
            return [self.start_coords, self.destination_coords, geometry_converted, distance, weight, transportation]





# TODO: Further steps
# Add the transit connections to the interactor pre-processing
# Add the coordinate values to the AuxiliaryTrafficSpace objects in the same way as for the TrafficSpace objects
# Calculate the closest TrafficSpace object to the start and destination coordinates using the saved coordinates for each TrafficSpace object
# Test the new large Grafing dataset with the new data model and see if the routing works