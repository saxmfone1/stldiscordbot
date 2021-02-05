from requests import Request, Session, ConnectionError, get
import logging
from time import sleep
import re

log = logging.getLogger("bot.thingiverse")

THINGIVERSE_API = "https://api.thingiverse.com"
THINGIVERSE_HOST = "https://www.thingiverse.com"


class ThingAPIException(Exception):
    pass


class ThingInvalidIDException(Exception):
    pass


class ThingInvalidURLException(Exception):
    pass


class ThingInvalidThingException(Exception):
    pass


class ThingiverseRest(object):
    def __init__(self, token):
        self.thingiverse_host = THINGIVERSE_API
        self.thingiverse_token = token
        self.headers = {"Authorization": f"BEARER {self.thingiverse_token}"}
        self.valid_status = [200, 204]
        self.log = logging.getLogger("bot.thingiverse.ThingiverseRest")
        self.http_logging = False

    @property
    def endpoint(self):
        return THINGIVERSE_API

    def call(self, method, url, retries=3, **kwargs):
        if url[0] == "/":
            url = url[1:]

        full_url = f"{self.endpoint}/{url}"

        api_session = Session()
        api_request = Request(method, full_url, headers=self.headers, **kwargs).prepare()

        if self.http_logging:
            request_raw = self.dump_request_to_string(api_request)
            self.log.debug(f"API request: \n{request_raw}")

        api_response = None
        retry_count = 0
        while retry_count < retries:
            try:
                api_response = api_session.send(api_request, verify=True)
            except ConnectionError:
                self.log.warning("API request threw connection error, retrying in 5 seconds...")
                retry_count += 1
                sleep(5)
                continue

            if api_response.status_code in self.valid_status:
                break
            else:
                self.log.warning(f"API returned {str(api_response.status_code)}, retrying in 5 seconds...")
                retry_count += 1
                sleep(5)

        if api_response is not None:
            if self.http_logging:
                response_raw = self.dump_response_to_string(api_response)
                self.log.debug(f"API response: \n{response_raw}")

            if api_response.status_code not in self.valid_status:
                raise ThingAPIException(f"Could not execute API:\n{request_raw}\n{response_raw}")

        return api_response

    def get(self, url, **kwargs):
        return self.call('GET', url, **kwargs)

    def put(self, url, **kwargs):
        return self.call('PUT', url, **kwargs)

    def post(self, url, **kwargs):
        return self.call('POST', url, **kwargs)

    def delete(self, url, **kwargs):
        return self.call('DELETE', url, **kwargs)

    @staticmethod
    def dump_request_to_string(request):
        if request.method in ['PUT', 'POST']:
            body = f"\n\n{str(request.body)}"
        else:
            body = ""

        output = "-----------Request <{}>------------\n{}\n{}{}".format(
            hex(hash(request)),
            f"{request.method} {request.path_url} HTTP/1.0",
            '\n'.join('{}: {}'.format(k, v) for k, v in request.headers.items()),
            body
        )

        return output

    @staticmethod
    def dump_response_to_string(response):
        output = "-----------Response <{}>-----------\n{}\n{}\n\n{}".format(
            hex(hash(response.request)),
            f"{response.status_code} {response.reason}",
            '\n'.join('{}: {}'.format(k, v) for k, v in response.headers.items()),
            response.text
        )

        return output


class ThingiverseClient(ThingiverseRest):
    def __init__(self, token):
        super().__init__(token)
        self.log = logging.getLogger("bot.thingiverse.ThingiverseClient")

    def get_thing_by_id(self, thing_id):
        self.log.debug(f"getting thing info for {thing_id}")
        if self.validate_thing_id(thing_id):
            return self.get(f"things/{thing_id}").json()
        else:
            raise ThingInvalidIDException("Invalid format for a thing id")

    def get_stls_by_id(self, thing_id):
        self.log.debug(f"getting stl info for thing {thing_id}")
        if self.validate_thing_id(thing_id):
            return self.get(f"things/{thing_id}/files").json()
        else:
            raise ThingInvalidIDException("Invalid format for a thing id")

    def get_thing_by_url(self, thing_url):
        self.log.debug(f"getting thing info for {thing_url}")
        if self.validate_thing_url(thing_url):
            thing_id = self.get_thing_id_from_url(thing_url)
            self.log.debug(f"thingid is {thing_id}")
            return self.get(f"things/{thing_id}").json()
        else:
            raise ThingInvalidIDException("Invalid thing url")

    def get_stls_by_url(self, thing_url):
        if self.validate_thing_url(thing_url):
            self.log.debug(f"getting stl info for {thing_url}")
            thing_id = self.get_thing_id_from_url(thing_url)
            return self.get(f"things/{thing_id}/files").json()
        else:
            raise ThingInvalidIDException("Invalid thing url")

    def get_stls(self, thing):
        self.log.debug(f"getting stls for {thing}")
        if self.validate_thing_id(thing):
            files = self.get_stls_by_id(thing)
            self.log.debug("we got a thing id")
        elif self.validate_thing_url(thing):
            files = self.get_stls_by_url(thing)
            self.log.debug("we got a thing url")
        else:
            self.log.error("we got garbage")
            raise ThingInvalidThingException("Input was not a valid thing")

        return self.parse_stls(files)

    @staticmethod
    def parse_stls(files):
        log.debug("looking for stl links")
        download_list = []
        for file in files:
            if file['name'].endswith(".stl"):
                log.debug(f"found an stl: {file['public_url']}")
                download_list.append(file['public_url'])
        return download_list

    @staticmethod
    def download_stls(tempdir: str, stls: list):
        log.info(f"downloading stls: {','.join(stls)} to {tempdir}")
        downloaded_files = []
        for stl in stls:
            log.debug(f"pulling down {stl}")
            stl_id = stl.split("download:")[1]
            r = get(stl)
            filename = f"{tempdir}/{stl_id}.stl"
            log.debug(f"saving to: {filename}")
            with open(filename, "wb") as f:
                f.write(r.content)
            downloaded_files.append(filename)
        return downloaded_files

    @staticmethod
    def validate_thing_url(url):
        url_pattern = re.compile(f"^{THINGIVERSE_HOST}/thing:[0-9]+$")
        return url_pattern.match(url)

    @staticmethod
    def validate_thing_id(thing_id):
        id_pattern = re.compile("^[0-9]+$")
        return id_pattern.match(thing_id)

    @staticmethod
    def get_thing_id_from_url(url):
        if ThingiverseClient.validate_thing_url(url):
            return url.split("thing:")[1]
