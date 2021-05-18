"""Add wiki documents to db. """
import os
from utils import setup_logging
from data.structures import get_documents
from database.db import GraphCon

setup_logging()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
gc = GraphCon('bolt://localhost:7687', 'neo4j', NEO4J_PASSWORD)

for dn, doc in enumerate(get_documents()):
    gc.add_document(dn, doc.title)
    for pn, para in enumerate(doc.paragraphs()):
        gc.add_paragraph(pn, dn, para.text)

gc.close()
