"""Link a few documents and paragraphs. """
import os
from utils import setup_logging
from database.db import GraphCon

setup_logging()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
gc = GraphCon('bolt://localhost:7687', 'neo4j', NEO4J_PASSWORD)

for n, d in enumerate(gc.get_documents(100, 1)):
    if n < 10 or len(d.title) < 3:
        continue
    for m, f in enumerate(gc.get_documents(1000, 100)):
        if d.title == f.title or len(f.title) < 3:
            continue
        for p in f.paragraphs():
            if d.title in p.text:
                gc.link_documents(f.title, d.title)
                break
gc.close()
