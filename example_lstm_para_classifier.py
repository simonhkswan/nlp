"""Example LSTM based paragraph classifier. """
import os
import random
import numpy as np
from utils import setup_logging
from models.neural.word2vec import Word2Vec, W2V_DIR
from models.neural.classifiers import LSTMParaClassifier, LSTM_DIR
from database.db import GraphCon

setup_logging()
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
gc = GraphCon('bolt://localhost:7687', 'neo4j', NEO4J_PASSWORD)

w2v = Word2Vec.load(W2V_DIR + '1')
m = LSTMParaClassifier(input_dim=128, dims=[64, 32], max_len=100)
docs = gc.get_documents(limit=1)

x1 = [np.array(w2v.extract(p)) for doc in docs for p in doc.paragraphs()]
x1 = [np.array([x[:100]]) for x in x1 if x.shape[0] >= 100]
x2 = [
    np.array(
        [[w2v.word_vectors[random.randrange(0, 40000)] for _ in range(100)]]
    )
    for __ in range(len(x1))
]
y1 = [np.array([[1.0]]) for _ in x1]
y2 = [np.array([[0.0]]) for _ in x2]

data = list(zip(x1+x2, y1+y2))

m.construct()
m.train_model(data, epochs=20, log_dir=LSTM_DIR + '1')
gc.close()
