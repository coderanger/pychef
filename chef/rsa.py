import sys
from ctypes import *

if sys.platform == 'win32' or sys.platform == 'cygwin':
    _eay = CDLL('libeay32.dll')
elif sys.platform == 'darwin':
    _eay = CDLL('libcrypto.dylib')
else:
    _eay = CDLL('libcrypto.so')

class SSLError(Exception):
    """An error in OpenSSL."""

# BIO *BIO_new_mem_buf(void *buf, int len);
BIO_new_mem_buf = _eay.BIO_new_mem_buf
BIO_new_mem_buf.argtypes = [c_void_p, c_int,]
BIO_new_mem_buf.restype = c_void_p

# int    BIO_free(BIO *a)
BIO_free = _eay.BIO_free
BIO_free.argtypes = [c_void_p]
BIO_free.restype = c_int
def BIO_free_errcheck(result, func, arguments):
    if result == 0:
        raise SSLError('Unable to free BIO')
BIO_free.errcheck = BIO_free_errcheck

#RSA *PEM_read_bio_RSAPrivateKey(BIO *bp, RSA **x,
#                                        pem_password_cb *cb, void *u);
PEM_read_bio_RSAPrivateKey = _eay.PEM_read_bio_RSAPrivateKey
PEM_read_bio_RSAPrivateKey.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]
PEM_read_bio_RSAPrivateKey.restype = c_void_p

#int RSA_private_encrypt(int flen, unsigned char *from,
#    unsigned char *to, RSA *rsa,int padding);
RSA_private_encrypt = _eay.RSA_private_encrypt
RSA_private_encrypt.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_int]
RSA_private_encrypt.restype = c_int

RSA_PKCS1_PADDING = 1
RSA_NO_PADDING = 3

# int RSA_size(const RSA *rsa);
RSA_size = _eay.RSA_size
RSA_size.argtypes = [c_void_p]
RSA_size.restype = c_int

# void RSA_free(RSA *rsa);
RSA_free = _eay.RSA_free
RSA_free.argtypes = [c_void_p]

class Key(object):
    """An OpenSSL RSA private key."""
    
    def __init__(self, fp):
        if isinstance(fp, basestring):
            fp = open(fp, 'rb')
        self.raw = fp.read()
        self.key = None
        self._load_key()
        
    def _load_key(self):
        if '\0' in self.raw:
            # Raw string has embedded nulls, treat it as binary data
            buf = create_string_buffer(self.raw, len(self.raw))
        else:
            buf = create_string_buffer(self.raw)
        
        bio = BIO_new_mem_buf(buf, len(buf))
        try:
            self.key = PEM_read_bio_RSAPrivateKey(bio, 0, 0, 0)
            if not self.key:
                raise SSLError('Unable to load RSA private key')
        finally:
            BIO_free(bio)
    
    def encrypt(self, value, padding=RSA_PKCS1_PADDING):
        buf = create_string_buffer(value, len(value))
        size = RSA_size(self.key)
        output = create_string_buffer(size)
        ret = RSA_private_encrypt(len(buf), buf, output, self.key, padding)
        if ret == 0:
            raise SSLError('Unable to encrypt data')
        return output.raw[:ret]
    
    def __del__(self):
        if self.key and RSA_free:
            RSA_free(self.key)
