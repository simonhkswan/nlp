import gzip
import bz2
import re
from urllib.request import urlopen
from utils import maybe_download
from .wikiextractor.WikiExtractor import Extractor
import logging


logger = logging.getLogger(__name__)


def wiki_page_counts(min_count=50, num_hours=12):
    url = "https://dumps.wikimedia.org/other/pageviews/"
    logger.debug(f"Querying {url} for page_counts.")
    with urlopen(url) as f:
        years = [m[1] for m in re.finditer(
                r'<a href="(\d+/)', f.read().decode('utf-8')
        )]

    url = url + years[-1]
    logger.debug(f"Querying {url} for page_counts.")
    with urlopen(url) as f:
        yr_mons = [m[1] for m in re.finditer(
                r'<a href="(\d+-\d+/)', f.read().decode('utf-8')
        )]

    url = url + yr_mons[-1]
    logger.debug(f"Querying {url} for page_counts.")
    with urlopen(url) as f:
        files = [url+m[1] for m in re.finditer(
                r'<a.*(pageviews-\d+-\d+.gz)', f.read().decode('utf-8')
        )]

    en_counts = {}
    logger.info(f'Downloading {num_hours} hours of pageview counts.')
    for page_view_file in files[-num_hours:]:
        with gzip.GzipFile(fileobj=maybe_download(page_view_file)) as f:
            for line in f:
                if line[:3] == b'en ':
                    if len(line.split()) != 4:
                        continue
                    if line.split()[-3] not in en_counts:
                        en_counts[line.split()[-3]] = int(line.split()[-2])
                    else:
                        en_counts[line.split()[-3]] += int(line.split()[-2])

    en_counts = [
        (w, count) for w, count in en_counts.items() if count >= min_count
    ]
    en_counts.sort(key=lambda x: x[1], reverse=True)
    logger.info('%d wiki pages found with at least %d views.',
                len(en_counts), min_count)
    return en_counts


def wiki_xml_dump(txt_file_path: str, min_count=50, num_hours=12):
    url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-" \
          "articles-multistream.xml.bz2"
    with bz2.open(maybe_download(url)) as f:
        num_texts = 0
        popular = [
            v[0].decode('utf-8').replace('_', ' ')
            for v in wiki_page_counts(min_count=min_count, num_hours=num_hours)
        ]
        with open(txt_file_path, 'w') as outfile:
            for n, page in enumerate(pages(f)):
                if n % 10000 == 0:
                    logger.debug(
                        '%d pages processed (found: %d).' % (n, num_texts)
                    )

                if page['title'] not in popular:
                    continue

                popular.remove(page['title'])
                Extractor(
                    page['id'], 1, page['title'], page['text']
                ).extract(outfile)
                num_texts += 1

            logger.info("%d pages with content extracted from %d." %
                        (num_texts, n))


def pages(f):
    page = {'text': ''}
    pos = 'o'
    for line in f:
        if pos == 'o':
            if b'<page>' in line:
                pos = 'i'
            else:
                continue

        elif 'i' in pos:
            if 'ii' in pos:
                if b'</text>' in line:
                    pos = 'i'
                    page['text'] += line.decode('utf-8')
                else:
                    page['text'] += line.decode('utf-8')

            else:
                if b'<title>' in line:
                    page['title'] = re.search(
                        '<title>(.*)</title>', line.decode('utf-8')
                    )[1]

                if b'<ns>' in line:
                    page['ns'] = re.search(
                        '<ns>(.*)</ns>', line.decode('utf-8')
                    )[1]
                    if page['ns'] != '0':
                        pos = 'o'
                        page = {'text': ''}
                        continue

                if b'<id>' in line:
                    page['id'] = re.search(
                        '<id>(.*)</id>', line.decode('utf-8')
                    )[1]
                elif b'</page>' in line:
                    pos = 'o'
                    yield(page)
                    page = {'text': ''}
                elif b'<text' in line:
                    page['text'] += line.decode('utf-8')
                    pos = 'ii'


def text_from_page(page):
    page['text'] = re.sub(r'\{\{[^{]+?\}\}', r'', page['text'])
    page['text'] = re.sub(r"\[\[File:.*\]\]", r'', page['text'])
    page['text'] = re.sub(
        r"\[\[[^\[]+\|(?P<word>[^\[]+)\]\]", r'\g<word>', page['text']
    )
    page['text'] = re.sub(
        r"\[\[(?P<word>[^\[]+)\]\]", r'\g<word>', page['text']
    )
    page['text'] = re.sub(r"&quot;|\'{2,3}", r'"', page['text'])
    page['text'] = re.sub(r" ?={2,4} ?", r'', page['text'])
    page['text'] = re.sub(r"&lt;!--.*--&gt;", r'', page['text'])
    page['text'] = re.sub(r'\n+', r'\n', page['text'])

    if 'See also\n' in page['text']:
        return page['text'][:page['text'].index('See also\n')]
    if 'References\n' in page['text']:
        return page['text'][:page['text'].index('References\n')]
    else:
        return None
