from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.error import ConnectionLost
import logging
import re

from irc_announce_parser.config import config


log = logging.getLogger(__name__)


strip_control_chars_re = re.compile("\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)


class IRCClient(irc.IRCClient):
    def __init__(self, channel_observers):
        self.channel_observers = channel_observers
        self.nickname = config.get('irc', 'nickname')

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        log.info('connectionMade')

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self)
        log.info('connectionMade')

    def signedOn(self):
        if '' in self.channel_observers:
            self.channel_observers['']('signedOn', None)

    def joined(self, channel):
        if channel in self.channel_observers:
            self.channel_observers[channel]('joined', channel)
        elif '' in self.channel_observers:
            self.channel_observers['']('joined', channel)


    def privmsg(self, user, channel, message):
        user = user.split('!')[0]

        message = strip_control_chars_re.sub('', message)

        if channel in self.channel_observers:
            self.channel_observers[channel]('message', (channel, user, message))
        elif '' in self.channel_observers:
            self.channel_observers['']('message', (channel, user, message))
        


class IRCClientFactory(protocol.ClientFactory):
    def __init__(self, channel_observers):
        self.channel_observers = channel_observers

    def buildProtocol(self, addr):
        p = IRCClient(self.channel_observers)
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        if not reason.check(ConnectionLost):
            log.info('Failure reason: %s' % reason.type)
            dest = connector.getDestination()
            log.info('Reconnecting to %s:%d' % (dest.host, dest.port))
            connector.connect()

    def clientConnectionFailed(self, connector, reason):
        dest = connector.getDestination()
        log.info('Connection failed to %s:%d' % (dest.host, dest.port))
        log.info('Bailing')
        reactor.stop()
