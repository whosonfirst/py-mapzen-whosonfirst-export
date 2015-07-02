import mapzen.gazetteer.export

class exporter(mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)

class timezone_exporter(exporter):

    def massage_feature(self, f):

        woe_props = f['properties']

        props = {}
        props['mz:placetype'] = 'timezone'
        props['mz:source'] = 'woedb'
        props['mz:name'] = woe_props.get('name', '')
        props['mz:fullname'] = woe_props.get('fullname', '')
        props['woe:id'] = woe_props.get('woe:id', 0)

        if woe_props.get('provider', False):
            props['woe:source'] = woe_props['provider']

        f['properties'] = props
