"""
This is the main file for the project test.
@Author: Felix Olbrich
@Date: 2022-12-16
@Version: 1.0.0
"""
#( -*- coding: utf-8 -*-)

""" This test requires a running Neo4j instance and a constants.py file with the following content:
- username 
- password
Also, the database needs to be accessible via bolt://localhost:7687. If the port is different, change the uri variable accordingly.
It follows the official Neo4j Python driver documentation: https://neo4j.com/docs/api/python-driver/current/ """

# Imports
from neo4j import GraphDatabase

from constants import password, username

print("Testing the connection to the database ...")

uri = "bolt://localhost:7687"  # "neo4j://localhost:7687"
driver = GraphDatabase.driver(uri, auth=(username, password))

def get_number_of_nodes(tx, var):
    results = []
    result = tx.run("MATCH (n) RETURN count(n) as number_of_nodes;")
    for record in result:
        results.append(record["number_of_nodes"])
    return results

with driver.session() as session:
    # friends = session.execute_read(get_friends_of, "Alice")
    # for friend in friends:
    #     print(friend)
    try:
        nodes = session.execute_read(get_number_of_nodes, "")
        for node in nodes:
            print(f"\033[92mSUCCESS! Found {node} nodes.\033[0m")
    except Exception as e:
        print("\033[91m[ERROR] An error occurred when accessing the \
            database!\033[0m")
        print(e)
driver.close()