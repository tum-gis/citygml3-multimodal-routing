from constants import password, username
from OLD_neo4j_interactor import Neo4jInteractor

# Test
# main method
if __name__ == '__main__':
    uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
    # create instance of Neo4jInteractor
    print("Connecting to Neo4j...")
    neo4j_interactor = Neo4jInteractor(uri, username, password)
    # test read
    print("Interaction with Neo4j DB...")
    # neo4j_interactor.find("apoc_djikstra")
    # query = "MATCH (n:%)-[r:successors|predecessors]->() RETURN n as test_nodes limit 2;"
    # vars = ""
    # results = neo4j_interactor.read(query, vars)
    # for result in results:
    #     print(result)
    
    # test write
    # query = "CREATE (n:Test {name: $name, title: $title}) RETURN n.name, n.title"
    # vars = {"name": "Test", "title": "Test"}
    # results = neo4j_interactor.write(query, vars)
    # for result in results:
    #     print(result)
    # close connection


    print("[INFO] Adding distance weights to 'SUCCESSOR_OF' relationships")
    # add distance weights to the relationships
    neo4j_interactor.insert("distance_weight")
    print("[INFO] Adding advanced distance weights to 'SUCCESSOR_OF' relationships")
    # add distance weights to the relationships
    neo4j_interactor.insert("advanced_distance_weight")

    print("[INFO] Adding coordinates to 'TrafficSpace' nodes")
    # add coordinates to the TrafficSpace nodes
    neo4j_interactor.insert("coords")

    print("\n\033[96m[INFO] Adding width to 'TrafficSpace' nodes \033[0m")
    # add width to the TrafficSpace nodes
    neo4j_interactor.insert("width")

    print("[INFO] Adding inclination to 'TrafficSpace' nodes")
    # add inclination to the TrafficSpace nodes
    neo4j_interactor.insert("inclination")


    neo4j_interactor.close()
    print("Done")

# TODO: Check if the inclination is calculated correctly with the right sign for the travel direction! 
