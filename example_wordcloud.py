"""Create word cloud based on most viewed wiki page title. """
from utils import setup_logging, wordcloud
from data.download import wiki_page_counts

setup_logging()
wordcloud({w.decode('utf-8'): float(f) for w, f in wiki_page_counts(50)[4:]})
