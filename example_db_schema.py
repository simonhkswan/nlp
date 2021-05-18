"""Construct db schema in neo4j. """
import os
from utils import setup_logging
from database.db import GraphCon

setup_logging()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
gc = GraphCon('bolt://localhost:7687', 'neo4j', NEO4J_PASSWORD)

query = """MATCH (n) WHERE EXISTS(n.abstract) DETACH DELETE n"""
gc.query(query)
structs = ["Document", "Paragraph", "Span"]
for n, s in enumerate(structs):
    query = """CREATE (:_%s
            {abstract:True, class_name:"%s", structure:True})""" % (s, s)
    gc.query(query)
    if n != 0:
        query = """MATCH (a:_%s), (b:_%s)
                CREATE (a)-[:_contains]->(b)""" % (structs[n-1], s)
        gc.query(query)

models = ["Classifier", "Detector"]
for c in models:
    query = """CREATE (:_%s {abstract:True, class_name:"%s"})""" % (c, c)
    gc.query(query)

query = """MATCH (n) WHERE EXISTS(n.structure)
        CREATE (n)<-[:_input]-(:_Concept {abstract:True, class_name:"Concept"})
        -[:_output]->(:_Prediction {abstract:True, class_name:"Prediction"})
        -[:_determines]->(n)"""
gc.query(query)

query = """MATCH (c:_Classifier), (n:_Concept) CREATE (c)-[:_predicts]->(n)"""
gc.query(query)

query = """MATCH (a)-[:_contains]->(b)
        CREATE (a)<-[:_input]-(:_Concept {abstract:True, class_name:"Concept"})
        -[:_output]->(:_Prediction {abstract:True, class_name:"Prediction"})
        -[:_determines]->(b)"""
gc.query(query)

query = """MATCH (c:_Detector),
        (a)<-[:_input]-(n:_Concept)-[:_output]->()-[:_determines]->(b)
        WHERE a.class_name <> b.class_name
        CREATE (c)-[:_predicts]->(n)"""
gc.query(query)

query = """MATCH
        (a)<-[:_determines]-(pa)<-[:_output]-(ca)<-[:_predicts]-(:_Classifier)
        -[:_predicts]->(cb)-[:_output]->(pb)-[:_determines]->(b)
        -[:_contains]->(a)
        CREATE (ca)<-[:_input]-(c:_Propagator
        {abstract:True, class_name:"Propagator"})-[:_modifies]->(pa),
        (cb)<-[:_input]-(c)-[:_modifies]->(pb)"""
gc.query(query)

query = """MATCH
        (c:_Concept)-[:_output]->(p:_Prediction)
        CREATE (c)<-[:_input]-(R:_Resolver
        {abstract:True, class_name:"Resolver"})-[:_modifies]->(p),
        (c)<-[:_input]-(R)-[:_modifies]->(p)"""
gc.query(query)

gc.close()
# ------------------------------------------------------------------------------
