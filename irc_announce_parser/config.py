import json
import os

from irc_announce_parser import common


class ConfigManager(object):
    def __init__(self):
        self.config_filename = common.get_config_dir('config.json')
        self.config = {}

    #TODO: This should take an arbritrary list of values to access nested dicts
    def get(self, section, key, default_value=None):
        if section not in self.config:
            self.config[section] = {}

        if key not in self.config[section]:
            if default_value is None:
                raise Exception('Config key %s not set in section %s' % (key, section))

            self.config[section][key] = default_value

        value = self.config[section][key]

        if isinstance(value, unicode):
            value = value.encode('utf-8')

        return value

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def has_section(self, section):
        return section in self.config

    def has_key(self, section, key):
        if not section in self.config:
            return False

        return key in self.config[section]

    def load(self):
        with open(self.config_filename, 'r') as fd:
            self.config = json.load(fd)

    def write(self):
        with open(self.config_filename, 'r') as fd:
            self.config = json.dump(fd)

config = ConfigManager()
