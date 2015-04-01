import urllib
from hashlib import sha1
import datetime as dt
import random as rnd
import requests
import base64
import hmac
import binascii
import json
import email

class LookerClient(object):

    def __init__(self, token, secret, host, port=443):
        self.token = token
        self.secret = secret
        self.host = host
        self.port = port

    def query(self, query, dictionary, fields, filters=None, limit=1000, output='json', method='GET'):
        return Query(self, query, dictionary, fields, filters=filters, limit=limit, output=output, method=method)


class Query(object):

    # only support for JSON and GET
    def __init__(self, credentials, query, dictionary, fields, filters=None, limit=1000, output='json', method='GET'):
        self.credentials = credentials
        self.query = query
        self.dictionary = dictionary
        self.fields = fields
        self.limit = limit
        self.set_output(output)
        self.method = method
        self.filters = {}
        self.add_filters(filters)

    def run(self):
        uri = "/api/dictionaries/%s/queries/%s.%s" % (
            self.dictionary, self.query, self.output)
        url = "%s%s?%s" % (self.credentials.host, uri, self.__query_params())
        r = requests.get(url, headers=self.__headers(uri))
        return json.loads(r.text)

    def set_output(self, output):
        self.output = output

    def add_filters(self, filters):
        if filters:
            self.filters.update(filters)
        return self

    ## private methods ##

    def __query_params(self):
        fields_string = ",".join(sorted([field.lower() for field in self.fields]))
        filters_list = []
        for key, value in iter(self.filters.items()):
            filters_list.append("filters[%s]=%s" % (str(key).lower(), urllib.parse.quote_plus(str(value))))
        return "fields=%s&%s&limit=%i" % (fields_string, "&".join(sorted(filters_list)), self.limit)

    def __headers(self, uri):
        today = email.utils.formatdate(localtime=True)
        nonce = hex(rnd.getrandbits(128))[2:-1]
        stringToSign = self.__generateStringToSign(uri, today, nonce)
        hashed = hmac.new(str.encode(self.credentials.secret, "utf-8"), str.encode(stringToSign, "utf-8"), sha1)
        signature = binascii.b2a_base64(hashed.digest())[:-1]
        return {"Authorization": self.credentials.token + ':' + bytes.decode(signature, "utf-8"),
                "Date": today,
                "x-llooker-nonce": nonce,
                "Accept": "application/json",
                "x-llooker-api-version": 1}

    # creates StringToSign, which goes in the header signature
    def __generateStringToSign(self, uri, today, nonce):
        fields = [self.method,
                  uri,
                  today,
                  nonce,
                  self.__query_params().replace("&", "\n")]
        return "\n".join(fields) + "\n"
