import mapzen.gazetteer.export
import woe.isthat

# base class just so we don't have to write the same __init__ block
# for everything (20150625/thisisaaronland)

class exporter(mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)

        self.lookup = None

        if kwargs.get('concordances', None):
            self.lookup = woe.isthat.lookup(kwargs['concordances'])

# countries

class adm0_exporter (exporter):

    def massage_feature(self, f):

        props = f['properties']
        
        # because there are no QS UIDS for countries...
        props['qs:id'] = props['qs_iso_cc']

        props['mz:name'] = props['qs_adm0']
        props['mz:source'] = 'quattroshapes'
        props['mz:placetype'] = 'country'

        f['properties'] = props
        # pass-by-ref

# regions

class adm1_exporter(exporter):

    def massage_feature(self, f):
        raise Exception, "please write me"

# counties (or whatever we end up calling them)

class adm2_exporter(exporter):

    def massage_feature(self, f):
        raise Exception, "please write me"

# localities (or whatever we end up calling them)

class locality_exporter(exporter):

    def massage_feature(self, f):
        raise Exception, "please write me"
