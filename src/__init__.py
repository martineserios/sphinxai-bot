import pyrebase 
from urllib.parse import quote

############################
# Monkey patch pyrebase: replace quote function in pyrebase to workaround a bug.
# See https://github.com/thisbejim/Pyrebase/issues/294.
pyrebase.pyrebase.quote = lambda s, safe=None: s

# Monkey patch pyrebase: the Storage.get_url method does need quoting :|
def get_url(self, token=None):
    path = self.path
    self.path = None
    if path.startswith('/'):
        path = path[1:]
    if token:
        return "{0}/o/{1}?alt=media&token={2}".format(self.storage_bucket, quote(path, safe=''), token)
    return "{0}/o/{1}?alt=media".format(self.storage_bucket, quote(path, safe=''))

pyrebase.pyrebase.Storage.get_url = lambda self, token=None: \
    get_url(self, token)
#############################