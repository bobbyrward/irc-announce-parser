from twisted.internet import reactor, protocol
from optparse import OptionParser
import logging
import logging.handlers
from twisted.python.log import PythonLoggingObserver
from twisted.web.client import downloadPage
import re
import os


from irc_announce_parser import common
from irc_announce_parser.config import config
from irc_announce_parser import irc_client
from irc_announce_parser import site_client


LOGGING_FORMAT = "%(asctime)s.%(msecs)03.0f [%(levelname)-8s][%(name)s:%(lineno)-4d] %(message)s"

log = logging.getLogger(__name__)


def announce_match_check(category, release, link):
    log.debug('Checking category %s for %s' % (category, release))

    if config.has_key('match', category):
        regexps = config.get('match', category)

        log.debug('Category in config, checking regexps')

        for regexp in regexps:
            if re.match(regexp, release):
                log.debug('%s matches %s' % (regexp, release))
                return True

    return False


def do_download(category, release, link):
    link_extract_id_re = re.compile(config.get('download', 'link_extract_id_regexp'), re.IGNORECASE)

    format_args = {
            "release": release,
            "category": category,
            "link": link,
        }

    result = link_extract_id_re.match(link)

    if not result:
        return

    log.debug('Extracted link id: %s' % result.group(1))

    format_args['link_id'] = result.group(1)

    download_link = config.get('download', 'download_link_format') % format_args
    download_file = os.path.join(config.get('download', 'watch_directory'), '%(release)s.torrent' % format_args)
    
    log.debug('Download Link: %s' % download_link)
    log.debug('Download File: %s' % download_file)

    log.debug('Starting Download')

    d = downloadPage(download_link, download_file)

    def on_finished_download(*args, **kwargs):
        log.debug('finished downloading for real')

    d.addCallback(on_finished_download)

    log.debug('Finished Download')


class Daemon(object):
    def __init__(self):
        self.site_client = None

    def _load_settings(self):
        log.info('Loading configuration')
        config.load()

        self.site_client = site_client.SiteClient()
        self.announce_message_re = re.compile(config.get('irc', 'announce_message_regexp'), re.IGNORECASE)

    def _irc_announce_observer(self, event, event_args):
        if event == 'joined':
            log.info('Joined channel %s' % event_args)
            return

        if event == 'message':
            channel, user, message = event_args

            result = self.announce_message_re.match(message)

            if result:
                self._handle_announce_message(result.group('category'), result.group('release'), result.group('link'))

            return

        log.debug('Unhandled event %s for %s' % (event, event_args))

    def _handle_announce_message(self, category, release, link):
        if announce_match_check(category, release, link):
            do_download(category, release, link)

    def _irc_control_observer(self, event, event_args):
        if event == 'signedOn':
            self.site_client.do_invite()
        else:
            log.debug('Unhandled event %s for %s' % (event, event_args))

    def _connect(self):
        self.site_client.do_login()

        f = irc_client.IRCClientFactory({
            config.get('irc', 'announce_channel'): self._irc_announce_observer,
            '': self._irc_control_observer,
        })

        irc_hostname = config.get('irc', 'hostname')
        irc_port = config.get('irc', 'port')

        log.info('Connecting to %s on port %d' % (irc_hostname, irc_port))

        reactor.connectTCP(irc_hostname, irc_port, f)

    def run(self):
        log.info('Daemon starting')

        self._load_settings()

        log.info('Logging into site')

        self._connect()

        reactor.run()


def main():
    parser = OptionParser(usage="%prog [options] [actions]",
                  version= "%prog: " + common.get_version())

    parser.add_option("-l", "--logfile", dest="logfile",
        help="Set the logfile location", action="store", type="str")
    parser.add_option("-L", "--loglevel", dest="loglevel",
        help="Set the log level: none, info, warning, error, critical, debug", action="store", type="str")


    (options, args) = parser.parse_args()

    if options.logfile:
        handler = logging.handlers.RotatingFileHandler(options.logfile, 'a', maxBytes=50*1024*1024, backupCount=5, encoding='utf-8', delay=0)
    else:
        handler = logging.StreamHandler()

    level = {
        "none": logging.NOTSET,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "none": logging.CRITICAL,
        "debug": logging.DEBUG,
    }[options.loglevel if options.loglevel else 'warning']

    handler.setLevel(level)

    rootLogger = logging.getLogger()
    formatter = logging.Formatter(LOGGING_FORMAT, datefmt="%H:%M:%S")

    handler.setFormatter(formatter)
    rootLogger.addHandler(handler)
    rootLogger.setLevel(level)

    twisted_logging = PythonLoggingObserver('twisted')
    twisted_logging.start()
    logging.getLogger("twisted").setLevel(level)

    daemon = Daemon()
    daemon.run()
