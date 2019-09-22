import re
import bz2
import gzip
import xml.etree.ElementTree as EleTree
from urllib.request import urlopen
from utils import maybe_download, TMP_DIR
from data.WikiExtractor import Extractor
import logging


logger = logging.getLogger(__name__)


def wiki_page_counts(min_count=50):
    url = "https://dumps.wikimedia.org/other/pageviews/"
    with urlopen(url) as f:
        years = [m[1] for m in re.finditer(
                r'<a href="(\d+/)', f.read().decode('utf-8')
        )]
    url = url + years[-1]
    with urlopen(url) as f:
        yr_mons = [m[1] for m in re.finditer(
                r'<a href="(\d+-\d+/)', f.read().decode('utf-8')
        )]
    url = url + yr_mons[-1]
    with urlopen(url) as f:
        files = [url+m[1] for m in re.finditer(
                r'<a.*(pageviews-\d+-\d+.gz)', f.read().decode('utf-8')
        )]

    en_counts = {}
    logger.info('Downloading wikipedia page counts.')
    for page_view_file in files[-12:]:
        with gzip.GzipFile(fileobj=maybe_download(page_view_file)) as f:
            for line in f:
                if line[:3] == b'en ':
                    if len(line.split()) != 4:
                        continue
                    if line.split()[-3] not in en_counts:
                        en_counts[line.split()[-3]] = int(line.split()[-2])
                    else:
                        en_counts[line.split()[-3]] += int(line.split()[-2])
    en_counts = [(w, count) for w, count in en_counts.items() if count >= min_count]
    en_counts.sort(key=lambda x: x[1], reverse=True)
    logger.info('%d wiki pages found with at least %d views.',
                len(en_counts), min_count)
    return en_counts


def wiki_xml_dump():
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-" \
          "articles-multistream.xml.bz2"
    popular = [v[0].decode('utf-8') for v in wiki_page_counts(50)]
    count = 0
    for n, (event, elem) in enumerate(EleTree.iterparse(bz2.open(maybe_download(url)))):
        if elem.tag[43:] == 'page':
            page = {
                child.tag[43:]: child.text if child.tag[43:] != 'revision'
                else {gc.tag[43:]: gc.text for gc in child.getchildren()}
                for child in elem.getchildren()
            }
            if 'redirect' in page:
                continue
            if page['title'] in popular:
                ext = Extractor(page['id'], page['revision']['id'], page['title'], page['revision']['text'])
                ext.extract(open(TMP_DIR+'wiki/'+re.sub(r'[/ ]', '_', page['title']), 'w'))
                count += 1
    logger.info("%d pages with content extracted from %d." % (count, len(popular)))
