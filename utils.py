import os
import sys
from urllib.request import urlopen
from wordcloud import WordCloud
import webbrowser
import coloredlogs
import logging

logger = logging.getLogger(__name__)

TMP_DIR = os.getcwd() + '/tmp/'
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)


def setup_logging():
    def trace(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'TRACE'."""
        if self.isEnabledFor(5):
            self._log(5, msg, args, **kwargs)
    logging.Logger.trace = trace

    root_logger = logging.getLogger()
    handler = logging.StreamHandler(stream=sys.stdout)
    root_logger.handlers = [handler]
    logging.addLevelName(5, 'TRACE')
    logging.TRACE = 5

    coloredlogs.DEFAULT_FIELD_STYLES = {
        'asctime': {'color': 229, 'bold': False},
        'msecs': {'color': 231, 'bold': False, 'faint': True},
        'levelname': {'color': 252, 'bold': True},
        'name': {'color': 67, 'bold': False},
        'lineno': {'color': 67, 'bold': False},
        'funcName': {'color': 132, 'bold': False}
    }
    coloredlogs.DEFAULT_LEVEL_STYLES = {
        'trace': {'color': 241, 'bold': False, 'faint': True},
        'debug': {'color': 68, 'bold': False, 'faint': False},
        'info': {'color': 253, 'bold': False, 'faint': False},
        'warning': {'color': 221, 'bold': True, 'faint': True},
        'success': {'color': 42, 'bold': True, 'faint': False},
        'error': {'color': 161, 'bold': True, 'faint': False},
        'critical': {'color': 130, 'bold': True, 'inverse': True}
    }

    coloredlogs.install(
        level=5,
        fmt='%(asctime)s.%(msecs)03d %(levelname)6s '
            '[%(process)s] %(name)s:%(funcName)s:%(lineno)d %(message)s',
        datefmt='%H:%M:%S'
    )


def maybe_download(url):
    local_path = os.path.join(TMP_DIR, os.path.split(url)[1])
    if os.path.exists(local_path):
        logger.debug("Using cached download at %s", local_path)
        return open(local_path, 'rb')
    else:
        logger.info("Downloading file from %s.", url)
        with urlopen(url) as df:
            file_size = int(df.headers.get('content-length')) / 1024
            logger.debug("File size: %skb", file_size)
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
    setup_logging()
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
