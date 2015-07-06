import mapzen.gazetteer.export

class exporter(mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)

    def massage_feature(self, f):

        props = {}
        props['mz:placetype'] = 'neighbourhood'
        props['iso:country'] = 'US'
        props['mz:name'] = 'La Lengua'

        f['properties'] = props
