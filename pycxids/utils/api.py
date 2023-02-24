import requests
from requests.auth import HTTPBasicAuth

class GeneralApi():
    """
    A general helper to send multiple POST and GET requests to a server
    """
    def __init__(self, base_url: str, headers=None, username=None, password=None) -> None:
        self.base_url = base_url
        self.headers = headers
        self.basic_auth = None
        if username and password:
            self.basic_auth = HTTPBasicAuth(username=username, password=password)

    def get(self, path: str, params = None):
        """
        Generic API GET request
        """
        r = requests.get(f"{self.base_url}{path}", auth=self.basic_auth, params=params, headers=self.headers)

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None
        
        j = r.json()
        return j
    
    def post(self, path: str, data = None, json_content = True):
        """
        Generic API POST request
        """
        r = requests.post(f"{self.base_url}{path}",  auth=self.basic_auth, json=data, headers=self.headers)

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None
        
        if not json_content:
            return r.content
        j = r.json()
        return j

    def delete(self, path: str):
        """
        Generic API DELETE request
        """
        r = requests.delete(f"{self.base_url}{path}", auth=self.basic_auth, headers=self.headers)

        if not r.ok:
            print(f"{r.status_code} - {r.reason} - {r.content}")
            return None

        j = r.json()
        return j
