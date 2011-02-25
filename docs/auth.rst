.. _auth:

===============================
Opscode Authentication protocol
===============================

The Opscode authentication protocol is a specification for an HTTP
authentication method using RSA signatures. It is used with chef-server-api as
well as the Opscode Platform service.

.. _auth-keys:

Keys
====

Every client to a Chef server requires an RSA private key. These are generated
by the server (or Platform) and should be stored securely. Keys must be in PEM
format as defined by OpenSSL.

.. _auth-headers:

Headers
=======

Each request must include 5 headers:

X-Ops-Sign
    Must be ``version=1.0``.
X-Ops-Userid
    The name of the API client.
X-Ops-Timestamp
    The current time. See :ref:`Timestamp <auth-canonical-timestamp>`.
X-Ops-Content-Hash
    The hash of the content of the request. See :ref:`Hashing <auth-hash>`.
X-Ops-Authorization-$N
    The lines of the RSA signature. See :ref:`Signature <auth-sign>`.

.. _auth-canonical:

Canonicalization
================

Rules for canonicalizing request data.

.. _auth-canonical-method:

HTTP Method
-----------

HTTP methods must be capitalized. Examples::
    
    GET
    POST

.. _auth-canonical-timestamp:

Timestamp
---------

All timestamps must in `ISO 8601`__ format using ``T`` as the separator. The
timezone must be UTC, using ``Z`` as the indicator. Examples::
    
    2010-12-04T15:47:49Z

__ http://en.wikipedia.org/wiki/ISO_8601

.. _auth-canonical-path:

Path
----

The path component of the URL must not have consecutive ``/`` characters. If
it is not the root path (``^/$``), it must not end with a ``/`` character.
Example::
    
    /
    /nodes
    /nodes/example.com

.. _auth-hash:

Hashing
=======

All hashes are Base64-encoded SHA1. The Base64 text must have line-breaks
every 60 characters. The Base64 alphabet must be the standard alphabet
defined in `RFC 3548`__ (``+/=``).

__ http://tools.ietf.org/html/rfc3548.html

.. _auth-sign:

Signature
=========

The ``X-Ops-Authorization-$N`` headers must be a Base64 hash of the output
of ``RSA_private_encrypt``. Each line of the Base64 output is a new header,
with the numbering starting at 1.

Base String
-----------

The signature base string is defined as::
    
    Method:<HTTP method>\n
    Hashed Path:<hashed path>\n
    X-Ops-Content-Hash:<hashed_body>\n
    X-Ops-Timestamp:<timestamp>\n
    X-Ops-UserId:<client name>

All values must be canonicalized using the above rules.
