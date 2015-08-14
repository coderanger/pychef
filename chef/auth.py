import six.moves
import base64
import datetime
import hashlib
import re

def _ruby_b64encode(value):
    """The Ruby function Base64.encode64 automatically breaks things up
    into 60-character chunks.
    """
    b64 = base64.b64encode(value)
    for i in six.moves.range(0, len(b64), 60):
        yield b64[i:i + 60].decode()

def ruby_b64encode(value):
    return '\n'.join(_ruby_b64encode(value))

def sha1_base64(value):
    """An implementation of Mixlib::Authentication::Digester."""
    return ruby_b64encode(hashlib.sha1(value.encode()).digest())

class UTC(datetime.tzinfo):
    """UTC timezone stub."""

    ZERO = datetime.timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return self.ZERO

utc = UTC()

def canonical_time(timestamp):
    if timestamp.tzinfo is not None:
        timestamp = timestamp.astimezone(utc).replace(tzinfo=None)
    return timestamp.replace(microsecond=0).isoformat() + 'Z'

canonical_path_regex = re.compile(r'/+')
def canonical_path(path):
    path = canonical_path_regex.sub('/', path)
    if len(path) > 1:
        path = path.rstrip('/')
    return path

def canonical_request(http_method, path, hashed_body, timestamp, user_id):
    # Canonicalize request parameters
    http_method = http_method.upper()
    path = canonical_path(path)
    if isinstance(timestamp, datetime.datetime):
        timestamp = canonical_time(timestamp)
    hashed_path = sha1_base64(path)
    return ('Method:%(http_method)s\n'
            'Hashed Path:%(hashed_path)s\n'
            'X-Ops-Content-Hash:%(hashed_body)s\n'
            'X-Ops-Timestamp:%(timestamp)s\n'
            'X-Ops-UserId:%(user_id)s' % vars())

def sign_request(key, http_method, path, body, host, timestamp, user_id):
    """Generate the needed headers for the Opscode authentication protocol."""
    timestamp = canonical_time(timestamp)
    hashed_body = sha1_base64(body or '')

    # Simple headers
    headers = {
        'x-ops-sign': 'version=1.0',
        'x-ops-userid': user_id,
        'x-ops-timestamp': timestamp,
        'x-ops-content-hash': hashed_body,
    }

    # Create RSA signature
    req = canonical_request(http_method, path, hashed_body, timestamp, user_id)
    sig = _ruby_b64encode(key.private_encrypt(req))
    for i, line in enumerate(sig):
        headers['x-ops-authorization-%s'%(i+1)] = line
    return headers
