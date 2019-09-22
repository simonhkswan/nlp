import os
from urllib.request import urlopen
from wordcloud import WordCloud
import webbrowser
import logging

logger = logging.getLogger(__name__)

TMP_DIR = '/tmp/nlp/'


def maybe_download(url):
    local_path = os.path.join(TMP_DIR, os.path.split(url)[1])
    if os.path.exists(local_path):
        logger.debug("Using cached download at %s", local_path)
        return open(local_path, 'rb')
    else:
        logger.info("Downloading file from %s.", url)
        with urlopen(url) as df:
            logger.debug("File size: %skb", int(df.headers.get('content-length'))/1024)
            downloaded, dl = 0, 0
            with open(local_path, 'wb') as of:
                for _ in df:
                    of.write(_)
                    downloaded += len(_)
                    dl += len(_)
                    if dl > (1024*1000*10):
                        logger.trace('%d kb downloaded.' % (downloaded/1024))
                        dl = 0
        return open(local_path, 'rb')


def wordcloud(frequencies, path=None):
    wc = WordCloud(width=1920, height=1080, background_color='white')
    wc.generate_from_frequencies(frequencies)
    cloud_path = path or os.path.join(TMP_DIR, 'wordcloud.png')
    wc.to_file(cloud_path)
    webbrowser.open(cloud_path)


def test_logging():
    current_level = logger.getEffectiveLevel()
    logger.setLevel(0)
    logger.trace('This is the TRACE level')
    logger.debug('This is the DEBUG level')
    logger.info('This is the INFO level')
    logger.warning('This is the WARNING level')
    logger.success('This is the SUCCESS level')
    logger.error('This is the ERROR level.')
    logger.critical('This is the CRITICAL level.')
    logger.setLevel(current_level)
    logger.log(
        current_level,
        'Logger level currently set at %s' %
        logging.getLevelName(current_level)
    )
