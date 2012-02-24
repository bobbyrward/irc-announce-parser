from twisted.python import log
import mechanize
import logging


from irc_announce_parser.config import config


log = logging.getLogger(__name__)


class SiteClient(object):
    def __init__(self):
        self.browser = mechanize.Browser()
        self.browser.set_handle_robots(False)

    def do_login(self):
        url = 'http://%s/login' % config.get('site', 'hostname')
        log.info('Opening: %s' % url)

        response = self.browser.open(url)

        self.browser.select_form(nr=0)
        self.browser.form['username'] = config.get('site', 'username')
        self.browser.form['password'] = config.get('site', 'password')

        return self.browser.submit()

    def do_invite(self):
        url = 'http://%s/irc' % config.get('site', 'hostname')
        log.info('Opening: %s' % url)

        response = self.browser.open(url)

        self.browser.select_form(nr=0)

        for checkbox in config.get('site', 'invite_checkboxes_unset'):
            self.browser.form[checkbox] = []

        for checkbox in config.get('site', 'invite_checkboxes_set'):
            self.browser.form[checkbox] = ['yes']

        return self.browser.submit()

    def get_page(self, url):
        log.info('Opening: %s' % url)
        return self.browser.open(url)
