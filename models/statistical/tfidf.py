import os
import math
import logging
from collections import Counter
from models.feature_extractors import WordSetExtractor

logger = logging.getLogger(__name__)

TFIDF_DIR = os.getcwd() + "/generated/tfidf/"
if not os.path.exists(TFIDF_DIR):
    os.makedirs(TFIDF_DIR)


class TfIdfVectorizer(object):
    def __init__(self, node_type):
        self.node_type = node_type
        self.global_counts = Counter()
        self.node_count = 0
        self.fe = WordSetExtractor()

    def calculate_global_counts(self, nodes):
        for n in nodes:
            self.global_counts.update(self.fe.extract(n))
            self.node_count += 1
        logger.info("Counts extracted from %d nodes." % self.node_count)
        logger.info("Top 10 counts: %s" % self.global_counts.most_common(10))

    def extract(self, node):
        words = list(node.words(lower=True))
        counts = Counter(words).most_common()
        n = len(words)
        return [(c[0], self.tfidf(c, n)) for c in counts]

    def tfidf(self, c, total):
        word, count = c
        # print(word, count, total, self.idf(word))
        return count/total * self.idf(word)

    def idf(self, word):
        # print(word, self.node_count, self.global_counts[word])
        return math.log10(self.node_count/(1+self.global_counts[word]))
