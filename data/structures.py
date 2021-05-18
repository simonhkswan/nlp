# -*- coding: utf-8 -*-
"""This module contains natural language data structures to work with.

By order of size, with each one containing the next, the data structures are:
    - Corpus
    - Document
    - Paragraph
    - Sentence
    - Span
    - Grapheme

These structures are stored as nodes in the graph database.

"""
import re
import logging
from abc import ABC, abstractmethod
from collections import Counter
from utils import TMP_DIR

logger = logging.getLogger(__name__)


class Structure(ABC):
    """The abstract base structure class"""

    def __init__(self, class_name):
        self.class_name = class_name

    @property
    @abstractmethod
    def text(self):
        pass


class Corpus(Structure):
    """"""
    class_name = "Corpora"

    def __init__(self, name):
        self.name = name
        super(Corpus, self).__init__(self.class_name)

    @abstractmethod
    def text(self):
        return "Corpora:"+self.name


class Document(Structure):
    """"""
    class_name = "Document"

    def __init__(self, text=None, paragraphs=None, node_id=None, title=None,
                 **kwargs):
        self.id = node_id
        if node_id is None:
            lines = text.split('\n')
            self.title = re.search(r'title="(.*)"', lines[0])[1]
            self._text = lines[3:-1]
        else:
            self.paras = paragraphs
            self.title = title
            self._text = None
            self.bowv = kwargs.get("bowv")
        super(Document, self).__init__(self.class_name)

    def paragraphs(self):
        if self.id is None:
            txt = ''
            for line in self._text:
                if len(line) > 0:
                    txt += (line+' ')
                elif len(txt) > 0:
                    yield Paragraph(txt)
                    txt = ''
        else:
            for p in self.paras:
                yield Paragraph(
                    text=p.get('text'),
                    id=p.id
                )

    @property
    def text(self):
        return '\n'.join([p.text for p in self.paragraphs()])

    def words(self, lower=False):
        for para in self.paragraphs():
            for w in para.words(lower):
                yield w


class Paragraph(Structure):
    """"""
    class_name = "Paragraph"

    def __init__(self, text, id=None):
        self._text = text
        self.id = id
        super(Paragraph, self).__init__(self.class_name)

    @property
    def text(self):
        return self._text

    def sentences(self):
        for s in re.split(r'(?<=[\)\]\w])\. ', self.text):
            if len(s) > 0:
                yield Sentence(s)

    def words(self, lower=False):
        for sent in self.sentences():
            for w in sent.words(lower):
                yield w


class Sentence(Structure):
    """"""
    class_name = "Sentence"

    def __init__(self, text):
        self._text = text
        super(Sentence, self).__init__(self.class_name)

    @property
    def text(self):
        return self._text

    def words(self, lower=False):
        if lower:
            for w in re.split(r'\W+', self.text):
                yield w.lower()
        else:
            for w in re.split(r'\W+', self.text):
                yield w


def get_documents():
    doc_count = 0
    with open(TMP_DIR+'texts.txt', 'r') as f:
        txt = ''
        for l in f:
            txt += l
            if '</doc>' in l:
                yield Document(txt)
                doc_count += 1
                if doc_count % 10000 == 0:
                    logger.debug('Processed %d documents' % doc_count)
                txt = ''


def get_vocab(size=50000):
    logger.info("Getting vocab counts.")
    counts = Counter(w for d in get_documents()
                     for p in d.paragraphs()
                     for s in p.sentences() for w in s.words()).most_common()
    logger.info("%d words in vocab (%d with more than 100 occurences). "
                "Returning top %d" % (len(counts),
                                      len([c for c in counts if c[1] > 100]),
                                      size))
    logger.debug('Most common words: %s' % counts[:50])
    logger.debug('Least common words: %s' % counts[-50:])
    return counts[:size]
