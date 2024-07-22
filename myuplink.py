#!/usr/bin/env python3
import os
import sys
import json
import logging
import time
import datetime
import requests
from caseconverter import snakecase
from prometheus_client import start_http_server, Gauge

class MyUplink:
    def __init__(self):
        try:
            # Variables
            self.registered_metrics = {}
            self.token_timestamp = datetime.datetime(1677, 9, 21)
            self.token = ""
            self.refresh_in = 0

            # Set up logging
            self.log_format = "%(asctime)-15s %(levelname)s %(message)s"
            if os.environ.get("debug", "false").lower() == "false":
                self.debug = False
                logging.basicConfig(level=logging.INFO, format=self.log_format)
            else:
                self.debug = True
                logging.basicConfig(level=logging.DEBUG, format=self.log_format)
            self.logger = logging.getLogger("myuplink")

            # Configure listen port and start Promethus http server
            try:
                self.listen_port = int(os.environ.get("port", "5000"))
            except ValueError:
                self.logger.critical("port must be a valid integer")
                sys.exit(1)
            start_http_server(self.listen_port)
            self.logger.info(f"Listen on port {self.listen_port}")

            self.base_url = os.environ.get("base_url", "https://api.myuplink.com")
            try:
                self.client_id = os.environ.get("client_id")
                self.client_secret = os.environ.get("client_secret")
            except ValueError:
                self.logger.critical(
                        "client_id and client_secret is mandatory environment variables")
                sys.exit(1)

            self.refresh_token()
        except Exception as exception:
            self.logger.critical(exception)

    def request_get_data(self, endpoint: str):
        payload = {}

        if (datetime.datetime.utcnow() - self.token_timestamp).total_seconds() < self.refresh_in:
            self.logger.debug(f"Seconds since last refresh of token: {(datetime.datetime.utcnow() - self.token_timestamp).total_seconds()}")
            self.refresh_token()
        else:
            self.logger.debug(f"Seconds since last refresh of token: {(datetime.datetime.utcnow() - self.token_timestamp).total_seconds()}")

        if self.token:
            headers = {'Authorization': 'Bearer ' + self.token}
            response = requests.get(f"{self.base_url}{endpoint}",
                                    headers=headers,
                                    verify=True,
                                    timeout=30)

            # Try to authenticate again if not authenticated
            if response.status_code == 401:
                self.refresh_token()
                response = requests.get(f"{self.base_url}{endpoint}",
                                        headers=headers,
                                        verify=True,
                                        timeout=30)

            # Abort if still not authenticated
            if response.status_code == 401:
                self.logger.critical("Not authorized")
                return payload

            if response.status_code == 200:
                # Did we get json response body?
                try:
                    # Load dict from json and remove soft hyphens that are often used in the response
                    payload = json.loads(response.text.replace('\xad', ''))
                except Exception as exception:
                    self.logger.error(f"Coult not parse JSON response: {exception}, body: {response.text}")
                    return payload
            else:
                self.logger.error(f"Unexpected status code: {response.status_code}, body: {response.text}")
        else:
            self.logger.critical("Not authenticated, cannot request data from API")
        self.logger.debug(f"Body: {payload}")
        return payload

    def refresh_token(self):
        token_req_payload = {'grant_type': 'client_credentials'}
        token_response = requests.post(f"{self.base_url}/oauth/token",
            data=token_req_payload, verify=True, allow_redirects=False,
            auth=(self.client_id, self.client_secret),
            timeout=30)
        if token_response.status_code !=200:
            self.logger.critical("Failed to obtain token from server")
        response = json.loads(token_response.text)
        self.logger.debug(f"Token: {response}")
        if 'access_token' in response:
            self.token = response['access_token']
            self.token_timestamp = datetime.datetime.utcnow()
        if 'expires_in' in response:
            self.expires_in = response['expires_in']

    def get_systems(self) -> dict:
        result = self.request_get_data("/v2/systems/me")
        if isinstance(result, dict):
            return result
        self.logger.warning(f"Unexpected response from API: {result}")
        return {}

    def get_device_info(self, device_id) -> dict:
        return self.request_get_data(f"/v2/devices/{device_id}")

    def get_device_points(self, device_id: str) -> dict:
        result = self.request_get_data(f"/v2/devices/{device_id}/points")
        if isinstance(result, list):
            return result
        self.logger.warning(f"Unexpected response from API: {result}")
        return []

    def fix_name(self, string: str) -> str:
        output = string.rstrip()
        output = snakecase(output)
        output = output.replace('å', 'a')
        output = output.replace('ä', 'a')
        output = output.replace('ö', 'o')
        return output

    def handle_metrics(self, device_id: str, metrics: list) -> None:
        for metric in metrics:
            if 'parameterName' in metric and 'value' in metric:
                name = f"myuplink_{self.fix_name(metric['parameterName'])}"
                if name not in self.registered_metrics:
                    try:
                        if 'category' in metric:
                            self.logger.info(
                                    f"Registering metric {name}, category: {metric['category']}")
                            self.registered_metrics[name] = Gauge(
                                    name,
                                    metric['parameterName'],
                                    ['device_id', 'category'])
                        else:
                            self.logger.info(f"Registering metric {name}")
                            self.registered_metrics[name] = Gauge(name,
                                    metric['parameterName'],
                                    ['device_id'])
                    except ValueError:
                        self.logger.warning(
                            f"Could not register {name}")
                if 'category' in metric:
                    self.registered_metrics[name].labels(
                            device_id,
                            metric['category']).set(metric['value'])
                else:
                    self.registered_metrics[name].labels(
                            device_id).set(metric['value'])

    def poll_metrics(self, devices: list) -> None:
        for device in devices:
            if 'id' in device:
                self.handle_metrics(device['id'], self.get_device_points(device['id']))

    def run(self):
        systems = self.get_systems()
        if 'systems' in systems:
            while True:
                for system in systems['systems']:
                    if 'devices' in system:
                        self.poll_metrics(system['devices'])
                time.sleep(60)
        else:
            self.logger.critical("Could not fetch systems from API, exiting")
            sys.exit(1)

def main():
    runner = MyUplink()
    runner.run()

if __name__ == '__main__':
    main()
