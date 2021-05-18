# NLP
---
This library contains tools to create natural language processing models and 
other funky linguistic things. Some of the features require neo4j to be
installed and running.

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
