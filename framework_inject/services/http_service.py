"""Framework: https://github.com/eshut/Framework-Python"""

import requests
from urllib.parse import urlencode, parse_qs
from framework_inject.logger.logger import Logger


class API(Logger):
    def __init__(self, site, logger=__file__):
        super().__init__(logger)
        self.site = site

    def status(self, uri):
        '''
        :return: request > request.status_code
        '''
        self.logger.debug("Trying to get status code")
        req = requests.get(self.site + uri)
        result = req
        return result

    def get(self, uri, params=None, headers=None):
        self.logger.debug("Trying to get Json")
        response = requests.get(self.site + uri, params=params, headers=headers)
        response.raise_for_status()
        return response

    def post(self, uri, data, headers=None):
        self.logger.debug("Trying to send POST data to: " + str(self.site + uri) + " With data: " + str(data))
        result = requests.post(self.site + uri, data=data, headers=headers)
        self.logger.debug("Got response: " + str(result) + "With data: " + str(result.text))
        return result

    def build_payload(self, **params):
        """
        Constructs a payload string from key-value pairs.

        Args:
            **params: Arbitrary keyword arguments representing payload parameters.

        Returns:
            str: URL-encoded payload string.
        """
        return urlencode(params, doseq=True)

    @staticmethod
    def parse_response(response: str) -> dict:
        """
        Converts a URL-encoded response string into a dictionary.

        Args:
            response (str): URL-encoded response string.

        Returns:
            dict: Parsed response as a dictionary.
        """
        parsed = parse_qs(response, keep_blank_values=True)
        # Flatten single-item lists for convenience
        return {key: value[0] if len(value) == 1 else value for key, value in parsed.items()}

