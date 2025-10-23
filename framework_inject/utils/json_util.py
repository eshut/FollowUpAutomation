import json


class JsonUtil:
    '''
    Use .get("element") to get element from .json
    '''

    @staticmethod
    def load_file(file_path):
        '''
        :return: element from config
        '''

        with open(file_path, "rb") as config_file:
            data = json.load(config_file)
            return data

    @staticmethod
    def load_json(text):
        return json.loads(text)