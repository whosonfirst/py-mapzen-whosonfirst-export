import mapzen.gazetteer.export
import logging

class exporter (mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)
        
    def massage_feature(self, f):

        sgid = f.get('id', None)

        props = f['properties']
        props['mz:placetype'] = 'venue'
        props['mz:source'] = 'simplegeo'

        props['sg:id'] = sgid

        f['properties'] = props
