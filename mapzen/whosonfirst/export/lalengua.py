import mapzen.whosonfirst.export

import logging
logging.warning("DEPRECATED - please finish and use mapzen.whosonfirst.import instead")

class exporter(mapzen.whosonfirst.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.whosonfirst.export.flatfile.__init__(self, root, **kwargs)

    def massage_feature(self, f):

        props = {}
        props['wof:placetype'] = 'neighbourhood'
        props['iso:country'] = 'US'
        props['wof:name'] = 'La Lengua'

        f['properties'] = props
