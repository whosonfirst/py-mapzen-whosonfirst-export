import sys
import re
import os.path
import json
import geojson
import logging
import requests

class flatfile:

    def __init__(self, root):

        path = os.path.abspath(root)        
        self.root = path

    def export_geojson(self, file, **kwargs):

        path = os.path.abspath(file)
        fh = open(path, 'r')
        
        if kwargs.get('line_delimited', False):

            for ln in fh.readlines():

                data = geojson.loads(ln)

                if not data:
                    logging.warning("failed to parse line")
                    logging.debug(ln)
                    continue

                self.export_feature(data)

        else:

            try:
                data = geojson.load(fh)
            except Exception, e:
                logging.error("Failed to load JSON for %s, because" % (path, e))
                return False

            features = data.get('features', [])

            if len(features) == 0:
                logging.warning("%s has not features" % path)
                return False

            for f in features:
                self.export_feature(f, **kwargs)

    def export_feature(self, f, **kwargs):

        self.massage_feature(f)

        props = f['properties']
        mzid = props.get('mz:id', None)

        if not mzid:

            logging.debug("This record has no mzid so now asking what Brooklyn would do...")

            mzid = self.generate_id()

            if mzid == 0:
                logging.error("OH NO - can't get integer!")
                return False

            props['mz:id'] = mzid

        """
        id = f.get('id', None)
        
        if not id:
            f['id'] = props['mz:id']
        elif id != props['mz:id']:
            f['id'] = props['mz:id']
        else:
            pass
        """

        f['properties'] = props

        return self.write_feature(f, **kwargs)

    def write_feature(self, f, **kwargs):

        props = f['properties']
        mzid = props.get('mz:id', None)

        fname = "%s.geojson" % mzid
        parent = self.id2path(mzid)

        root = os.path.join(self.root, parent)
        path = os.path.join(root, fname)

        if kwargs.get('skip_existing', False) and os.path.exists(path):
            logging.debug("%s already exists so whatEVAR" % path)
            return True

        if not os.path.exists(root):
            os.makedirs(root)

        logging.info("writing %s" % (path))

        try:
            fh = open(path, 'w')
            self.write_json(f, fh)
            fh.close()
        except Exception, e:
            logging.error("failed to write %s, because %s" % (path, e))
            return False

        return True

    def write_json(self, data, out, indent=2): 

        # From TileStache's vectiles GeoJSON encoder thingy
        # (20130317/straup)

        float_pat = re.compile(r'^-?\d+\.\d+(e-?\d+)?$')
        charfloat_pat = re.compile(r'^[\[,\,]-?\d+\.\d+(e-?\d+)?$')

        encoder = json.JSONEncoder(separators=(',', ':'))
        encoded = encoder.iterencode(data)
    
        for token in encoded:
            if charfloat_pat.match(token):
                # in python 2.7, we see a character followed by a float literal
                out.write(token[0] + '%.6f' % float(token[1:]))
        
            elif float_pat.match(token):
                # in python 2.6, we see a simple float literal
                out.write('%.6f' % float(token))
        
            else:
                out.write(token)

    def id2path(self, id):

        tmp = str(id)
        parts = []

        while len(tmp) > 3:
            parts.append(tmp[0:3])
            tmp = tmp[3:]

        if len(tmp):
            parts.append(tmp)

        return "/".join(parts)

    # This is left to subclasses to define

    def massage_feature(self, f):
        pass

    def generate_id(self):

        url = 'http://api.brooklynintegers.com/rest/'
        params = {'method':'brooklyn.integers.create'}

        try :
            rsp = requests.post(url, params=params)    
            data = rsp.content
        except Exception, e:
            logging.error(e)
            return 0

        # Note: this is because I am lazy and can't
        # remember to update the damn code to account
        # for PHP now issuing warnings for the weird
        # way it does regular expressions in the first
        # place... (20150623/thisisaaronland)

        try:
            data = re.sub(r"^[^\{]+", "", data)
            data = json.loads(data)
        except Exception, e:
            logging.error(e)
            return 0
    
        return data.get('integer', 0)

