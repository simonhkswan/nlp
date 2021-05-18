"""Fetch and extract wikipedia texts.

This takes a while on the first call. The extacted data is cached so subsequent
calls are much faster.

"""
from utils import setup_logging, TMP_DIR
from data.download import wiki_xml_dump

setup_logging()
wiki_xml_dump(
    txt_file_path=TMP_DIR + 'texts.txt',
    min_count=50,
    num_hours=12
)
