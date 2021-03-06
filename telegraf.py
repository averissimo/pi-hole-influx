#! /usr/bin/env python3
import json
import requests
from time import sleep, localtime, strftime
import sys
import logging

from dynaconf import LazySettings, Validator
from dynaconf.utils.boxing import DynaBox

settings = LazySettings(
    SETTINGS_FILE_FOR_DYNACONF="etc/default.toml,etc/user.toml",
    ENVVAR_PREFIX_FOR_DYNACONF="PIHOLE",
)
settings.validators.register(Validator("INSTANCES", must_exist=True))
settings.validators.validate()

logger = logging.getLogger(__name__)


class Pihole:
    """Container object for a single Pi-hole instance."""

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.timeout = settings.as_int("REQUEST_TIMEOUT")
        self.logger = logging.getLogger("pihole." + name)
        # self.logger.info("Initialized for %s (%s)", name, url)

    def get_data(self):
        """Retrieve API data from Pi-hole, and return as dict on success."""
        response = requests.get(self.url, timeout=self.timeout)
        if response.status_code == 200:
            self.logger.debug("Got %d bytes", len(response.content))
            return response.json()
        else:
            self.logger.error(
                "Got unexpected response %d, %s", response.status_code, response.content
            )


class Daemon(object):
    def __init__(self):

        if isinstance(settings.INSTANCES, DynaBox):
            self.piholes = [
                Pihole(name, url) for name, url in settings.INSTANCES.items()
            ]
        elif isinstance(settings.INSTANCES, list):
            self.piholes = [
                Pihole("pihole" + str(n + 1), url)
                for n, url in enumerate(settings.INSTANCES)
            ]
        elif "=" in settings.INSTANCES:
            name, url = settings.INSTANCES.split("=", maxsplit=1)
            self.piholes = [Pihole(name, url)]
        elif isinstance(settings.INSTANCES, str):
            self.piholes = [Pihole("pihole", settings.INSTANCES)]
        else:
            raise ValueError("Unable to parse instances definition(s).")

    def run(self):
        for pi in self.piholes:
            data = pi.get_data()
            self.send_msg(data, pi.name)

    def send_msg(self, resp, name):
        if "gravity_last_updated" in resp:
            del resp["gravity_last_updated"]

        # Monkey-patch ads-% to be always float (type not enforced at API level)
        resp["ads_percentage_today"] = float(resp.get("ads_percentage_today", 0.0))

        json_body = {"measurement": "pihole", "tags": {"host": name}}
        json_body.update(resp)

        print(json.dumps(json_body))



def main(single_run=True):
    log_level = (settings.LOG_LEVEL).upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(levelname)s: [%(name)s] %(message)s",
    )

    daemon = Daemon()

    try:
        daemon.run()
    except KeyboardInterrupt:
        sys.exit(0)  # pragma: no cover
    except Exception:
        logger.exception("Unexpected exception", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main(True)
