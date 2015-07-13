import mapzen.gazetteer.export

class exporter(mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)

    def massage_feature(self, f):

        props = {}
        props['wof:placetype'] = 'neighbourhood'
        props['wof:source'] = 'woedb'
        props['iso:country'] = 'US'
        props['wof:name'] = 'Gowanus Heights'
        props['woe:id'] = 18807771

        f['properties'] = props
