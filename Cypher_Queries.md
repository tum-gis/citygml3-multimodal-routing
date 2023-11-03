# Cypher queries for the preprocessing of the Neo4j database
## Create shortcuts for navigation relationships
### Create shortcut PREDECESSOR_OF relationships

OLD QUERY
```cypher
//Create Shortcut 4 TrafficSpace Predecessors
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) CREATE (a)-[:PREDECESSOR_OF]->(b);
```

New queries with proper direction handling:

```cypher
//Create Shortcut 4 TrafficSpace Predecessors
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`)
WITH a, b
MATCH (a)-[:trafficDirection]-(n WHERE n.value="forwards") CREATE (a)-[:PREDECESSOR_OF]->(b);
```
AND
```cypher
//Create Shortcut 4 TrafficSpace Predecessors
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) 
WITH a, b
MATCH (a)-[:trafficDirection]-(n WHERE n.value="backwards") CREATE (a)-[:PREDECESSOR_OF]->(b);
```


### Create shortcut SUCCESSOR_OF relationships

OLD QUERY
```cypher
//Create Shortcut 4 TrafficSpace SUCCESSORS
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) CREATE (a)-[:SUCCESSOR_OF]-(b);
```

New queries with proper direction handling:

```cypher
//Create Shortcut 4 TrafficSpace SUCCESSORS
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:predecessors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`)
WITH a, b
MATCH (a)-[:trafficDirection]-(n WHERE n.value="backwards") CREATE (a)-[:SUCCESSOR_OF]->(b);
```
AND
```cypher
//Create Shortcut 4 TrafficSpace SUCCESSORS
MATCH (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:successors]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b:`org.citygml4j.core.model.transportation.TrafficSpace`) 
WITH a, b
MATCH (a)-[:trafficDirection]-(n WHERE n.value="forwards") CREATE (a)-[:SUCCESSOR_OF]->(b);
```

### Add lane change relationships
<!-- Implemented in introduce_lane_changes.py -->

Implemented in [introduce_lane_changes.py](_TEST_introduce_lane_changes.py)

```cypher
```	

## Switch Transportation Modes
### get all parking spaces
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_lane_type" and m.value="PARKING") RETURN  m
```
### get neighbouring TrafficAreas to parking AuxiliaryTrafficAreas
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_lane_type" and m.value="PARKING") 
WITH n, m
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(l WHERE l.name="identifier_roadId")
WITH n, m, l 
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(k WHERE k.name="identifier_laneSectionId")
WITH n,m, l,k
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(j WHERE j.name="identifier_laneId")
WITH n,m, l,k,j
MATCH (a:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="identifier_roadId" and b.value=l.value)
MATCH(a:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="identifier_laneSectionId" and c.value=k.value)
RETURN n, a, b.value, l.value, c.value, k.value
```
Use the following query to find the next neighbouring TrafficArea in positive and negative lane id direction. There might be multiple. Choose the two closest ones. One in positive and one in negative direction.
```cypher	
MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_lane_type" and m.value="PARKING") 
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
RETURN n, a, b.value, l.value, c.value, k.value, j.value, d.value
```
### generate the SWITCH_TO_PARKING and SWITCH_TO relationships
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.AuxiliaryTrafficArea` WHERE n.id="UUID_2165a80f-384b-3975-abad-5da54363c55e")-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(a)
WITH a
MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea` WHERE m.id="")-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:boundaries]-(b)
WITH a, b
CREATE (a)-[:SWITCH_TO]->(b);
CREATE (b)-[:SWITCH_TO_PARKING]->(a);

```

### Switch road side as pedestrian using crossWalk
The code below would work if a TrafficArea which represents a crossWalk would contain information about their roadId, laneSectionId and laneId. This is currently not the case. Therefore, this code does not work.
Right now, it is only possible to find such connections utilizing the coordinate level.

```cypher 
MATCH (n:`org.citygml4j.core.model.transportation.TrafficArea`)-[:names]-()-[:elementData]-()-[:ARRAY_MEMBER]-(b WHERE b.value="crossWalk")
WITH n
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(l WHERE l.name="identifier_roadId")
WITH n, l 
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(k WHERE k.name="identifier_laneSectionId")
WITH n, l,k
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(j WHERE j.name="identifier_laneId")
WITH n, l,k,j
MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="opendrive_lane_type" and a.value="SIDEWALK")
MATCH (m:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="identifier_roadId" and b.value=l.value)
MATCH(m:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="identifier_laneSectionId" and c.value=k.value)
MATCH(m:`org.citygml4j.core.model.transportation.TrafficArea`)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="identifier_laneId")
RETURN m, n;
```

### Find SIDEWALK nodes that end 
Only a successor relationship
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(p)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="opendrive_lane_type" and a.value="SIDEWALK")
MATCH (n)-[:successors]-() 
MATCH (n) WHERE not (n)-[:predecessors]-()
RETURN n;
```
Only a predecessor relationship
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(p)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="opendrive_lane_type" and a.value="SIDEWALK")
MATCH (n)-[:predecessors]-()
MATCH (n) WHERE not (n)-[:successors]-()
RETURN n;
```

## Add the Type of Transportation Mode 
### Add the type of transportation mode to the TrafficSpace nodes
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="opendrive_lane_type")
WITH n, m, a
SET n.transportation_type=a.value;
```
Then you can run the cypher query below to set the transportation type for the relationships.
### Add the type of transportation mode to the successor and predecessor relationships
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)-[r:SUCCESSOR_OF]-()
WITH n, r
SET r.transportation_type=n.transportation_type;
```


## Add weighting attributes to the relationships

### Get the attributes for SUCCESSOR_OF relationships from the database

```cypher 
MATCH path = (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[r:SUCCESSOR_OF]->(:`org.citygml4j.core.model.transportation.TrafficSpace`)
WITH path
MATCH (a)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n)
WITH path, n
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_road_length") RETURN m.name, m.value, n, m, path LIMIT 1;
```	
### Set the length attribute for SUCCESSOR_OF relationships

```cypher
MATCH path = (a:`org.citygml4j.core.model.transportation.TrafficSpace`)-[r:SUCCESSOR_OF]->(b:`org.citygml4j.core.model.transportation.TrafficSpace`)
WITH path, a, b
MATCH (a)-[:boundaries]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(n)
WITH path, n, a, b
MATCH (n)-[:genericAttributes]-()-[:elementData]-()-[:ARRAY_MEMBER]-()-[:object]-(m WHERE m.name="opendrive_road_length") 
WITH path, n, m, a, b
MERGE (a)-[r:SUCCESSOR_OF]->(b)
SET r.opendrive_road_length = m.value
RETURN a, b, m.value;
```

## Routing

### Using A* algorithm

```cypher
//APOC Dijkstra: Find shortest path between start and end node using SUCCESSOR_OF and NEIGHBOURS_LANE shortcut and segment_length weight
MATCH (from:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_666b845a-0860-3849-b81c-0b47c663b6aa'}), (to:`org.citygml4j.core.model.transportation.TrafficSpace`{id:'UUID_f66d4bd1-d97e-39a8-a712-1459ae9ca30b'})
CALL apoc.algo.aStarConfig(from, to, 'SUCCESSOR_OF>|NEIGHBOURS_LANE>', {weight:'segment_length',y: 'lat', x:'lon'}) yield path as path, weight as weight
RETURN path, weight;
```

# Useful queries

## Delete all relationships with unset property
Change the relationship type and property name accordingly.
```cypher 
MATCH ()-[r:SUCCESSOR_OF]-() WHERE r.transportation_type IS NULL DELETE r
```

<!-- TODO: The code must be corrected to only generate one new relationship -->
## Create new relationships between TrafficSpaces for bidirectional lanes
This code generates a new relationship called SUCCESSOR_OF_2 between two TrafficSpaces. The new relationship has the same properties as the original relationship. The inclination is multiplied by -1 to reflect the opposite direction of the lane.
```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace`)
WHERE n.transportation_type = "BIDIRECTIONAL"
MATCH (m:`org.citygml4j.core.model.transportation.TrafficSpace`)
WHERE m.transportation_type = "BIDIRECTIONAL"
MATCH (n)-[r:SUCCESSOR_OF]->(m)
CREATE (n)<-[r2:SUCCESSOR_OF_2]-(m)
SET r2 = properties(r)
SET r2.inclination = r.inclination * (-1)
RETURN n, m, r2;
```
To delete the relationships again, run the following query:
```cypher
MATCH ()-[r:SUCCESSOR_OF_2]-()  DELETE r
```

# Traffic Sign Information

Cypher code to get traffic sign information for RegulatorySigns corresponding to a TrafficSpace node:

```cypher	
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id="")-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="RegulatorySigns") 
WITH n,f,o, a 
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
WITH n,f,o, a,b
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
WITH n,f,o, a,b,c
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
RETURN n,f,o, a,b,c,d limit 1;
```

Code for getting the traffic sign information for trafficSign corresponding to a TrafficSpace node:

```cypher
MATCH (n:`org.citygml4j.core.model.transportation.TrafficSpace` WHERE n.id="")-[:object]-()-[:relatedTo]-()-[:object]-()-[:ARRAY_MEMBER]-()-[:elementData]-()-[:relatedTo]-(f)-[:genericAttributes]-()-[:elementData]-(o)-[:ARRAY_MEMBER]-()-[:object]-(a WHERE a.name="identifier_roadObjectName" and a.value="trafficSign") 
WITH n,f,o, a 
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(b WHERE b.name="opendrive_roadSignal_type")
WITH n,f,o, a,b
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(c WHERE c.name="opendrive_roadSignal_subtype")
WITH n,f,o, a,b,c
MATCH (o)-[:ARRAY_MEMBER]-()-[:object]-(d WHERE d.name="opendrive_roadSignal_value")
RETURN n,f,o, a,b,c,d limit 1;
```



# Metadata
Get the bounding box of the city model:
```cypher
MATCH (n:`org.citygml4j.core.model.core.CityModel`)-[:boundedBy]-()-[:envelope]-(e)
WITH e
MATCH (e)-[:upperCorner]-()-[:value]-()-[:elementData]-(a)
WITH e, a
MATCH (e)-[:lowerCorner]-()-[:value]-()-[:elementData]-(b)
RETURN a as upperCorner, b as lowerCorner;
```


# Insert Speed Limit TrafficSign connections

```cypher
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
```


# Final routing weights

## Concepts

### Weight overview

- Distance: The distance of the segment in meters (simple Euclidean or advanced calculation)
- Inclination Weight: The inclination of the segment in % moved to positive values by adding 100 to the value
- Width: 1/min_width of the segment to prioritize wider segments
- Speed: 1/speed_limit of the segment to prioritize higher speed limits
- time = distance / speed = accurate distance * speed weight as the speed weight is 1/speed_limit

### Specialities for different connections in the graph

- SUCCESSOR_OF: Default connection between two TrafficSpaces
- SUCCESSOR_OF_2: Connection between two TrafficSpaces for bidirectional usage of SIDEWALKS, thus the speed limit is set to 5.0 [km/h]
- NEIGHBOURS_LANE: Connection between two TrafficSpaces that are neighbours in the same lane section
  - Distance and width get the same value and are calculated by the Euclidean distance between the first point of the geometry of the two TrafficSpaces
  - The inclination is calculated in the same manner using the first point of the geometry of the two TrafficSpaces
  - The speed limit is set to the lower value of the two TrafficSpaces SUCCESSOR_OF relationship
  - The speed weight is calculated by 1/speed_limit
  - The time is calculated by distance * speed weight
- SWITCH_TO_PARKING: All weights are set to 0, as those are just used to block a transportation mode switch to a parking space
- SWITCH_TO: This contains all weights of the SUCCESSOR_OF relationship.
  - The distance is calculated between the first point of the geometry of the two TrafficSpaces that are connected by the SWITCH_TO_PARKING and SWITCH_TO relationship (trafficSpace)-[:SWITCH_TO_PARKING]-()-[:SWITCH_TO]->(trafficSpace)
  - The inclination is calculated in the same manner using the first point of the geometry of the two TrafficSpaces
  - The speed limit is set to 5.0 [km/h] as an assumption in parking spaces there is a lower movement speed around walking speed
  - The speed weight is calculated by 1/speed_limit
  - The time is calculated by distance * speed weight (additionally, a time delay for switching the transportation mode could be added)
  - The width is set to 0 as the width of the parking space is not relevant for the routing, however this could be used in more advanced applications to find suitable parking spaces for a vehicle with a certain width

## SUCCESSOR_OF relationships

Retrieve the relationship information for calculation of the final weights in Python:
```cypher
MATCH p=()-[r:SUCCESSOR_OF]->() RETURN r.speed_limit as speed_limit, r.advanced_segment_length as distance, r.transportation_type as type, r.inclination as inclination, r.min_width as width
```

Python code to calculate the final weights for the SUCCESSOR_OF relationships:
```python
# Calculate the final weights for the SUCCESSOR_OF relationships
# speed weight:
speed_weight = 1 / speed_limit
# time weight:
time_weight = distance * speed_weight
# inclination weight:
inclination_weight = inclination + 100
# width weight:
width_weight = 1 / width
```

Cypher code to update the SUCCESSOR_OF relationships with the final weights:
```cypher
MATCH p=()-[r:SUCCESSOR_OF]->() SET r.speed_weight = speed_weight, r.time_weight = time_weight, r.inclination_weight = inclination_weight, r.width_weight = width_weight
```

## SUCCESSOR_OF_2 relationships

Retrieve the relationship information for calculation of the final weights in Python:
```cypher
MATCH p=()-[r:SUCCESSOR_OF_2]->() RETURN r.speed_limit as speed_limit, r.advanced_segment_length as distance, r.transportation_type as type, r.inclination as inclination, r.min_width as width
```

Python code to calculate the final weights for the SUCCESSOR_OF_2 relationships:
```python
# Calculate the final weights for the SUCCESSOR_OF relationships
# speed weight:
speed_weight = 1 / speed_limit
# time weight:
time_weight = distance * speed_weight
# inclination weight:
inclination_weight = inclination + 100
# width weight:
width_weight = 1 / width
```

Cypher code to update the SUCCESSOR_OF_2 relationships with the final weights:
```cypher
MATCH p=()-[r:SUCCESSOR_OF_2]->() SET r.speed_weight = speed_weight, r.time_weight = time_weight, r.inclination_weight = inclination_weight, r.width_weight = width_weight
```

## NEIGHBOURS_LANE relationships

Retrieve the relationship information for calculation of the final weights in Python:
```cypher
MATCH p=(n)-[r:NEIGHBOURS_LANE]->(m) 
WITH n, m, r, p
MATCH (n)-[r2:SUCCESSOR_OF]->()
WITH n, m, r, p, r2
MATCH (m)-[r3:SUCCESSOR_OF]->()
RETURN n, m, r, r2.speed_limit, r3.speed_limit
```
- 
Python code to calculate the final weights for the NEIGHBOURS_LANE relationships:
```python
# Calculate the final weights for the NEIGHBOURS_LANE relationships
# distance and width:
# distance = distance between the first point of the geometry of the two TrafficSpaces
# Get the first point of the geometry of the two TrafficSpaces
# TODO Query DATABASE

# Calculate the distance between the two points
distance = distance_between_points(point1, point2)
width_weight = 1 / distance
# inclination weight:
inclination = inclination_between_points(point1, point2)
inclination_weight = inclination + 100
# speed_limit:
speed_limit = min(r2.speed_limit, r3.speed_limit)
# speed weight:
speed_weight = 1 / min(r2.speed_limit, r3.speed_limit)
# time weight:
time_weight = distance * speed_weight
```

Cypher code to update the NEIGHBOURS_LANE relationships with the final weights:
```cypher
MATCH p=(n)-[r:NEIGHBOURS_LANE]->(m)
SET r.distance = distance, r.width_weight = width_weight, r.inclination_weight = inclination_weight, r.speed_limit = speed_limit, r.speed_weight = speed_weight, r.time_weight = time_weight
```

## SWITCH_TO relationships

Retrieve the relationship information for calculation of the final weights in Python:
```cypher
MATCH (n)-[:SWITCH_TO_PARKING]->()-[r:SWITCH_TO]->(m)
RETURN n, m, r
```

Python code to calculate the final weights for the SWITCH_TO relationships:
```python
# Calculate the final weights for the SWITCH_TO relationships
# distance:
# distance = distance between the first point of the geometry of the two TrafficSpaces
# Get the first point of the geometry of the two TrafficSpaces
# TODO Query DATABASE

# Calculate the distance between the two points
distance = distance_between_points(point1, point2)
# inclination weight:
inclination = inclination_between_points(point1, point2)
inclination_weight = inclination + 100
# speed_limit:
speed_limit = 5.0
# speed weight:
speed_weight = 1 / speed_limit
# time weight:
time_weight = distance * speed_weight
# width weight:
width_weight = 0
```

Cypher code to update the SWITCH_TO relationships with the final weights:
```cypher
MATCH (n)-[:SWITCH_TO_PARKING]->()-[r:SWITCH_TO]->(m)
SET r.distance = distance, r.width_weight = width_weight, r.inclination_weight = inclination_weight, r.speed_limit = speed_limit, r.speed_weight = speed_weight, r.time_weight = time_weight
```


# Metadata for nodes and relationships

Using the APOC library to get the metadata for nodes and relationships:
```cypher
CALL apoc.meta.graph()
```



