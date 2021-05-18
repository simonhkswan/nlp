"""Add tfidf weighted bag-of-word vector to documents and paragraphs. """
import os
import numpy as np
from utils import setup_logging
from models.neural.word2vec import Word2Vec, W2V_DIR
from models.statistical.tfidf import TfIdfVectorizer, TFIDF_DIR
from database.db import GraphCon

setup_logging()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
gc = GraphCon('bolt://localhost:7687', 'neo4j', NEO4J_PASSWORD)
w2v = Word2Vec.load(W2V_DIR + '1')

tfidf = TfIdfVectorizer('paragraph')
tfidf.calculate_global_counts(
    (p for d in gc.get_documents(limit=50000, batch_size=1000)
     for p in d.paragraphs())
)

for n, d in enumerate(gc.get_documents(50000, 1000)):
    tvec = tfidf.extract(d)
    tvec.sort(key=lambda x: x[1], reverse=True)
    # wordcloud({w: f for w, f in tvec},
    #           path=TFIDF_DIR + 'wordcloud_alt_%d.png' % n)
    bowv = np.sum([w2v[w]*f for w, f in tvec[:200]], axis=0)
    gc.set_node_bowv(d.id, bowv.tolist())

# Fetch and save titles and bow vectors to tsv files.
titles, bowvs = [], []
for n, d in enumerate(gc.get_documents(50000, 1000)):
    titles.append(d.title)
    bowvs.append(d.bowv)

gc.close()

with open(TFIDF_DIR + 'doc_bowvs.tsv', 'w') as outfile:
    for bowv in bowvs:
        outfile.write('\t'.join(['%.5f' % j for j in bowv])+'\n')
with open(TFIDF_DIR + 'doc_titles.tsv', 'w') as outfile:
    for title in titles:
        outfile.write(title+'\n')
