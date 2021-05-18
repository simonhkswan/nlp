# -*- coding: utf-8 -*-
"""Feature extractors used by models.

Feature extractors provide the link between the data stored in the database
and the models used for prediction.

Every feature extractor implements the method `extract` on a selection of the
structure types defined in data.structures.py. The allowed structures are
specified by the FeatureExtractors `in_types`.

Currently implemented:
    - SkipGramExtractor
    - WordSetExtractor

"""
import logging
from typing import Dict
import numpy as np
import random
from abc import ABC, abstractmethod
from data.structures import get_vocab

logger = logging.getLogger(__name__)


def fe_from_dict(json_dict):
    """Returns a feature extractor from json content.

    Args:
        json_dict (dict):

    Returns:
        FeatureExtractor: The feature extractor described by the json content.
    """
    return str2feature_extractor[json_dict['class_name']].from_json(json_dict)


class FeatureExtractor(ABC):
    """Abstract base feature extractor class.

    Args:
        class_name (str): String representation of the class.
        in_types (list[str]): List of allowed input structure types.
    """
    def __init__(self, class_name, in_types):
        self.class_name = class_name
        self.in_types = in_types

    @abstractmethod
    def extract(self, node):
        return node

    @abstractmethod
    def to_json(self):
        fe = {
            "class_name": self.class_name
        }
        return fe

    @staticmethod
    @abstractmethod
    def from_json(json_dict):
        pass


class SkipGramExtractor(FeatureExtractor):
    """

    Args:
        window (int): Number of words either side to use as context.
    """
    class_name = "SkipGramExtractor"
    in_types = ["Corpus", "Document", "Paragraph", "Sentence"]

    def __init__(self, window):
        self.win = window
        self.word2int = None
        self.counts = None
        self.probs = None
        super(SkipGramExtractor, self).__init__(self.class_name, self.in_types)

    def create_word2int(self, size, tsv_path=None):
        self.counts = get_vocab(size=size - 1)
        self.word2int = {w[0]: n + 1 for n, w in enumerate(self.counts)}
        if tsv_path is not None:
            self.save_vocab_tsv(tsv_path)
        total = sum([w[1] for w in self.counts])
        self.probs = {
            self.word2int[w[0]]: (
                1. + np.sqrt(1000. * w[1] / total)
            ) * total / (1000. * w[1])
            for w in self.counts
        }

    def save_vocab_tsv(self, path):
        logger.info("Saving vocab TSV file to: %s." % path)
        with open(path, 'w') as tsv_file:
            tsv_file.write('Word\tCount\n')
            tsv_file.write('<UNK>\t0\n')
            for w, c in self.counts:
                tsv_file.write('%s\t%d\n' % (w, c))

    def extract(self, node):
        x, y = [], []
        text = [self.word2int.get(w, 0) for w in node.words()]
        for i in range(len(text) - 4):
            x.append(text[i + self.win])
            y.append(text[i:i + self.win] +
                     text[i + 1 + self.win:i + 1 + 2 * self.win])

        x = np.array(x, dtype=np.int32)
        y = np.array(y, dtype=np.int32)
        return x, y

    def docs_to_training_data(self, docs, size, tsv_path=None):
        x = []
        y = []
        self.create_word2int(size=size, tsv_path=tsv_path)
        for doc in docs:
            for para in doc.paragraphs():
                for s in para.sentences():
                    text = [self.word2int.get(w, 0) for w in s.words()]
                    for i in range(len(text) - 4):
                        if random.random() > self.probs.get(text[i+self.win], self.probs[1]):
                            continue
                        x.append(text[i + self.win])
                        y.append(text[i:i + self.win] +
                                 text[i + 1 + self.win:i + 1 + 2 * self.win])
        x = np.array(x, dtype=np.int32)
        y = np.array(y, dtype=np.int32)
        return x, y

    def to_json(self):
        fe = super().to_json()
        fe["win"] = str(self.win)
        return fe

    @staticmethod
    def from_json(json_dict):
        return SkipGramExtractor(json_dict["window"])


class WordSetExtractor(FeatureExtractor):
    """Feature Extractor that returns unique sets of words from nodes."""
    class_name = "WordSetExtractor"
    in_types = ["Document", "Paragraph", "Sentence"]

    def __init__(self):
        super(WordSetExtractor, self).__init__(self.class_name, self.in_types)

    def extract(self, node):
        return list(set(node.words(lower=True)))

    def to_json(self):
        fe = super().to_json()
        return fe

    @staticmethod
    def from_json(json_dict):
        return WordSetExtractor()


str2feature_extractor: Dict[str, FeatureExtractor] = {
    feature_extractor.class_name: feature_extractor
    for feature_extractor in FeatureExtractor.__subclasses__()
}
