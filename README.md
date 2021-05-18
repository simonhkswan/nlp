[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-3710/) [![Flake8](https://github.com/simonhkswan/nlp/actions/workflows/flake8-action.yml/badge.svg)](https://github.com/simonhkswan/nlp/actions/workflows/flake8-action.yml)

# NLP
This library contains tools to create natural language processing models and 
other funky linguistic things. Some of the features require neo4j to be
installed and running.

Currently there are three modules (plus a few more things in `nlp.utils.py`):

`nlp.data`
- downloading and extracting text data
- data structures: corpora -> docs -> paragraphs -> spans

`nlp.database`
- storing the data structures and models in `neo4j`
- accessing the data structures + any annotations/predictions from the models

`nlp.models`
- neural models - word2vec, LSTM classifiers
- statistical models - tfidf
- feature extractors - SkipGram (feature extractors take data from the data
    structures and prepare it for the models).


## Some Snippets

### Word Clouds
The snippet below provides an example of how a word cloud can be created based
upon recently read wikipedia pages. It's interesting to sum up what the world
is reading about at any given moment.

```python
# example_wordcloud.py
from utils import setup_logging, wordcloud
from data.download import wiki_page_counts

setup_logging()
wordcloud({
    w.decode('utf-8'): float(f) 
    for w, f in wiki_page_counts(min_count=500, num_hours=12)[4:]
})
```

Example output:

![wordcloud](https://user-images.githubusercontent.com/13236749/118616146-54888d00-b7b9-11eb-9444-f36dc6d01a5f.png)

### Downloading and extracting Wikipedia pages
We need lots of text for NLP. A good source is wikipedia, but a lot of the
pages are automatically generated and filled with junk.

The snippet below downloads and extracts wiki pages, but only ones that have
been accessed by people enough times to likely be edited by real people. In 
this example, pages with at least 50 views in the past 12 hours are extracted.

```python
# example_wiki_fetch.py
from utils import setup_logging, TMP_DIR
from data.download import wiki_xml_dump

setup_logging()
wiki_xml_dump(
    txt_file_path=TMP_DIR + 'texts.txt',
    min_count=50,
    num_hours=12
)
```

### Word2Vec
This snippet shows how a word2vec model can be trained.

```python
# example_w2v.py
import os
import numpy as np
from utils import setup_logging, TMP_DIR
from data.structures import get_documents
from models.neural.word2vec import Word2Vec, W2V_DIR
from models.feature_extractors import SkipGramExtractor

setup_logging()
MODEL_DIR = W2V_DIR + '1/'
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# Create w2v training data
sge = SkipGramExtractor(window=2)
x, y = sge.docs_to_training_data(docs=get_documents(), size=50000,
                                 tsv_path=MODEL_DIR + 'vocab.tsv')
np.save(TMP_DIR + 'x.npy', x)
np.save(TMP_DIR + 'y.npy', y)

# Create and train a w2v model
x = np.expand_dims(np.load(TMP_DIR + 'x.npy'), axis=-1)
y = np.load(TMP_DIR + 'y.npy')
z = np.concatenate([x, y], axis=-1)
np.random.shuffle(z)
x, y = z[..., 0], z[..., 1:]
del z
w2v = Word2Vec(dim=128, vocab=50000, path=MODEL_DIR, feature_extractor=sge)
w2v.construct()
w2v.train(x=x, y=y, mbs=5000, steps=1000000)
w2v.save()
```
<img width="1152" alt="Screenshot 2021-05-18 at 09 12 22" src="https://user-images.githubusercontent.com/13236749/118616026-3b7fdc00-b7b9-11eb-8ace-7d8ed432c2ac.png">

