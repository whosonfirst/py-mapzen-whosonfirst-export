import mapzen.whosonfirst.export
import logging

import logging
logging.warning("DEPRECATED - please finish and use mapzen.whosonfirst.import instead")

class exporter (mapzen.whosonfirst.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.whosonfirst.export.flatfile.__init__(self, root, **kwargs)
        
    def massage_feature(self, f):

        sgid = f.get('id', None)

        props = f['properties']
        props['wof:placetype'] = 'venue'
        props['wof:source'] = 'simplegeo'

        props['sg:id'] = sgid

        f['properties'] = props
