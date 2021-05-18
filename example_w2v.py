"""Create w2v training data, build and train a w2v model. """
import numpy as np
from utils import setup_logging, TMP_DIR
from data.download import wiki_xml_dump
from data.structures import get_documents
from models.neural.word2vec import Word2Vec, W2V_DIR
from models.feature_extractors import SkipGramExtractor

setup_logging()
# Fetch and extract wikipedia texts (this takes a while on first call)
wiki_xml_dump(TMP_DIR + 'texts.txt')

# Create w2v training data
sge = SkipGramExtractor(window=2)
x, y = sge.docs_to_training_data(docs=get_documents(), size=50000,
                                 tsv_path=W2V_DIR + '1/vocab.tsv')
np.save(TMP_DIR + 'nlp/x.npy', x)
np.save(TMP_DIR + 'nlp/y.npy', y)

# Create and train a w2v model
x = np.expand_dims(np.load(TMP_DIR + 'nlp/x.npy'), axis=-1)
y = np.load(TMP_DIR + 'nlp/y.npy')
z = np.concatenate([x, y], axis=-1)
np.random.shuffle(z)
x, y = z[..., 0], z[..., 1:]
del z
w2v = Word2Vec(dim=128, vocab=50000)
w2v.construct()
w2v.train(x=x, y=y, mbs=5000, steps=1000000)
w2v.save()
