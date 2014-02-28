import requests
import json


class Nest(object):
    """
    Class that abstracts communication with the Nest Learning Thermostat
    unofficial API.  Initialize with username and password, and you will get
    an object with methods that allow you to check states and issue commands.
    """
    def __init__(self, username, passwd):
        self.username = username
        self.passwd = passwd
        self.access_endpoint = 'https://home.nest.com/user/login'
        self.session = False
        self.resource_path = '/v2/mobile/user.'
        self.command_path = '/v2/put/shared.'
        self.weather_endpoint = 'https://home.nest.com/api/0.1/weather/forecast/'

        # these items are set later
        self.transport_url = ''
        self.access_token = ''
        self.user_id = ''
        self.resource_endpoint = ''
        self.structures = []
        self.devices = None
        self.serial = ''
        self.temp = ''
        self.humidity = ''
        self.state = None
        self.schedule = None
        self.shared = None
        self.user = None
        self.target_device = None
        self.target_device_id = ''
        self.temperature_scale = ''
        self.temperature = 0
        self.humidity = 0
        self.headers = None
        self.target_temperature = 0

        # populate them
        self.login().get_state().set_target_device()

    def login(self):
        """
        Logs in to Nest remote server
        """
        payload = {'username': self.username, 'password': self.passwd}
        headers = {'user-agent': 'Nest/1.1.0.10 CFNetwork/548.0.4'}

        r = requests.post(self.access_endpoint, data=payload, headers=headers)

        try:
            res = json.loads(r.text)
            self.transport_url = res['urls']['transport_url']
            self.access_token = res['access_token']
            self.user_id = res['userid']
            self.resource_endpoint = self.transport_url + self.resource_path + self.user_id
            self.session = True
        except ValueError:
            raise Exception('Nest login failed')

        return self

    def get_state(self):
        """
        Fetches Nest thermometer state data from remote server
        """
        self.headers = {
            'user-agent': 'Nest/1.1.0.10 CFNetwork/548.0.4',
             'Authorization': 'Basic ' + self.access_token,
             'X-nl-user-id': self.user_id,
             'X-nl-protocol-version': '1'
        }

        r = requests.get(self.resource_endpoint, headers=self.headers)

        try:
            self.state = json.loads(r.text)
            self.devices = self.state['device']
            self.schedule = self.state['schedule']
            self.shared = self.state['shared']
            self.structures = self.state['structure']
            self.user = self.state['user'][self.user_id]
            for structure in self.user['structures']:
                structure_id = structure.split('.')[1]
                self.structures[structure_id]['weather'] = self.get_weather(self.structures[structure_id]['postal_code'])
        except ValueError:
            raise Exception('Nest remote service not available')

        return self

    def get_weather(self, zip_code):
        """
        Get weather forecast from the Nest api
        """
        r = requests.get(self.weather_endpoint + zip_code)
        return json.loads(r.text)

    def set_target_device(self, device_id=None):
        """
        Figure out which of the many devices is the target device.
        We can specify the device_id (serial number) if we have it.
        If there is a single device, we assume that's the target (most use cases).
        Otherwise, we grow confused.
        """
        if device_id:
            self.target_device_id = device_id
            self.target_device = self.devices[self.target_device_id]
            return True
        elif len(self.devices) == 1:
            self.target_device_id = self.devices.keys()[0]
            self.target_device = self.devices[self.target_device_id]
        else:
            raise Exception("Can't figure out which Nest to target.")

        self.temperature_scale = self.target_device['temperature_scale']

        if self.temperature_scale == 'F':
            self.temperature = float(celsius_to_fahrenheit(self.state['shared'][self.target_device_id]['current_temperature']))
            self.target_temperature = float(celsius_to_fahrenheit(self.state['shared'][self.target_device_id]['target_temperature']))
        elif self.temperature_scale == 'C':
            self.temperature = float(self.state['shared'][self.target_device_id]['current_temperature'])
            self.target_temperature = float(self.state['shared'][self.target_device_id]['target_temperature'])
        else:
            raise Exception('Invalid temperature scale')

        self.humidity = float(self.target_device['current_humidity'])

        return self

    def set_target_temperature(self, target_temp):
        if not self.target_device:
            self.set_target_device()

        if self.temperature_scale == 'F':
            target_temp_C = fahrenheit_to_celsius(target_temp)
        elif self.temperature_scale == 'C':
            target_temp_C = target_temp
        else:
            raise Exception('Invalid temperature scale')

        payload = json.dumps(
            {'target_change_pending': True,
             'target_temperature': target_temp_C}
        )

        r = requests.post(self.transport_url + self.command_path + self.target_device_id,
                          data=payload,
                          headers=self.headers)

        if r.status_code == '200':
            return r
        else:
            return r


def celsius_to_fahrenheit(celsius):
    fahrenheit = 9.0 / 5.0 * celsius + 32
    return fahrenheit


def fahrenheit_to_celsius(fahrenheit):
    celsius = (fahrenheit - 32) * 5.0 / 9.0
    return celsius
