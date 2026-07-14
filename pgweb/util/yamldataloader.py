import os
import yaml

import logging
log = logging.getLogger(__name__)


# Load the feature matrix data at startup and cache it in memory
class YamlDataLoader:
    DATAFILE = None

    def __init__(self):
        self.fn = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data/', self.DATAFILE))
        self.load()

    def load(self):
        self.lastload = os.stat(self.fn).st_mtime
        with open(self.fn) as f:
            self.data = yaml.load(f, Loader=yaml.SafeLoader)

    def _conditional_load(self):
        if os.stat(self.fn).st_mtime != self.lastload:
            log.info("{} data has changed, reloading".format(self.DATAFILE))
            self.load()

    def get(self):
        self._conditional_load()
        return self.data
