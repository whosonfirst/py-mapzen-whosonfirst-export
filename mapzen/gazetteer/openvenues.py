import sys
import logging
import hashlib
import address_normalizer

import mapzen.export
import woe.isthat

class exporter (mapzen.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.export.flatfile.__init__(self, root)

        self.lookup = None

        if kwargs.get('concordances', None):
            self.lookup = woe.isthat.lookup(kargs['concordances'])

    def massage_feature(self, f):

        props = f['properties']
        props['mz:placetype'] = 'venue'
        props['mz:datasource'] = 'openvenues'

        loc = props.get('locality', '')
        addr = props.get('street_address', '')

        loc = loc.encode('utf8')

        addr = address_normalizer.expand_street_address(addr)
        addr = " ".join(addr)
        addr = addr.encode('utf8')

        md5 = hashlib.md5()
        md5.update("%s %s" % (addr, loc))
        
        puid = md5.hexdigest()
        props['mz:puid'] = puid

        if self.lookup:

            mzid = self.lookup.woe_id(puid)
            logging.debug("got %s for %s" % (mzid, puid))

            if mzid != 0:
                props['mz:id'] = mzid

        f['properties'] = props
