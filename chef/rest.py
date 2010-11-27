import datetime
import json
import urllib2
import urlparse

from auth import sign_request
from rsa import Key

def api_request(url, headers={}, data=None):
    """Make an JSON API call against a Chef server."""
    headers = {'Accept': 'application/json'}
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
        method = 'POST'
    else:
        method = 'GET'
    urlp = urlparse.urlparse(url)
    headers.update(sign_request(key=Key(r'client.pem'),
                                http_method=method, 
                                path=urlp.path,
                                body=data,
                                host=urlp.netloc,
                                timestamp=datetime.datetime.utcnow(),
                                user_id='client'))
    reply = urllib2.urlopen(urllib2.Request(url, data, headers)).read()
    return json.loads(reply)

if __name__ == '__main__':
    try:
        print api_request('http://risk-chef:4000/nodes')
    except urllib2.HTTPError, e:
        print e.read()
