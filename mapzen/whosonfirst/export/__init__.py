# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import time
import sys
import re
import os.path
import json
import geojson
import logging
import requests
import pprint
import hashlib
import shapely.geometry

import mapzen.whosonfirst.utils
import mapzen.whosonfirst.concordances

class flatfile:

    def __init__(self, root, **kwargs):

        path = os.path.abspath(root)        
        self.root = path

        self.debug = kwargs.get('debug', False)

        # concordances stuff - for when we are plowing through
        # a dataset that takes a long time and may need to be
        # restarted.

        concordances = kwargs.get('concordances', False)
        concordances_dsn = kwargs.get('concordances_dsn', None)
        concordances_key = kwargs.get('concordances_key', None)

        if concordances and not concordances_key:
            raise Exception, "Missing concordances key"

        if concordances and not concordances_dsn:
            raise Exception, "Missing concordances DSN"
            
        if concordances:

            idx = mapzen.whosonfirst.concordances.index(concordances_dsn)
            qry = mapzen.whosonfirst.concordances.query(concordances_dsn)

            self.concordances_dsn = concordances_dsn
            self.concordances_key = concordances_key

            self.concordances_idx = idx
            self.concordances_qry = qry
            self.concordances = True

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

        mapzen.whosonfirst.utils.ensure_bbox(f)

        self.massage_feature(f)
        
        props = f['properties']
        props['wof:geomhash'] = self.hash_geom(f)

        # who am I ?
        # have I been here before ?
        # why is the sky blue ?

        wofid = None

        if props.has_key('wof:id'):
            wofid = props['wof:id']

        # do we have a concordance with which to help find ourselves ?

        # PLEASE REPLACE ME WITH py-mapzen-whosonfirst-concordances
        # AS SOON AS IT MAKES SENSE (20150728/thisisaaronland)

        if wofid == None:

            if self.concordances:

                concordances = props.get('wof:concordances', {})

                other_src = self.concordances_key
                other_id = concordances.get(other_src, None)

                if other_id:

                    row = self.concordances_qry.by_other_id(other_id, other_src)
                    logging.debug("concordance lookup %s for %s" % (wofid, row))

                    if row:
                        wofid = row[0]
                        props['wof:id'] = wofid
                    else:
                        wofid = None

                else:
                    logging.warning("failed to find concordances key %s:%s" % (other_src, other_id))

        if wofid == None:

            logging.debug("This record has no wofid so now asking what Brooklyn would do...")

            wofid = mapzen.whosonfirst.utils.generate_id()

            if wofid == 0:
                logging.error("OH NO - can't get integer!")
                return False

            props['wof:id'] = wofid
            f['id'] = wofid

        # what time is it?

        now = int(time.time())
        props['wof:lastmodified'] = now

        # stubs

        for k in ('supersedes', 'superseded_by', 'hierarchy', 'belongsto', 'breaches'):
            k = "wof:%s" % k

            if not props.get(k, False):
                props[k] = []

        # ensure hierarchy contains self

        for h in props['wof:hierarchy']:

            k = "%s_id" % props['wof:placetype']
            v = props['wof:id']

            if not h.get(k, False):
                h[k] = v

        # ensure belongs to

        belongsto = []

        for h in props['wof:hierarchy']:

            for ignore, id in h.items():

                if id != wofid and id != -1 and not id in belongsto:
                    belongsto.append(id)

        props['wof:belongsto'] = belongsto

        # ensure minimum viable geom: properties
        # maybe move this in to mapzen.whosonfirst.utils
        # as we do with bbox ?

        """
        calc_geom = False

        for k in ('area', 'latitude', 'longitude'):
            k = "geom:%s" % k

            if not props.get(k, False):
                calc_geom = True
                break
        """

        # just always recalculate the geom properties because it
        # keeps things simple (20150811/thisisaaronland)

        calc_geom = True

        if calc_geom:

            shp = shapely.geometry.asShape(f['geometry'])
            coords = shp.centroid
            area = shp.area

            props['geom:latitude'] = coords.y
            props['geom:longitude'] = coords.x
            props['geom:area'] = area

        f['properties'] = props

        if self.debug:
            logging.info("debugging is enabled so not writing anything to disk...")
            logging.info("if I did though I would write stuff to %s" % (self.feature_path(f)))

            logging.info(pprint.pformat(props))
            return True

        # store concordances

        if self.concordances:

            concordance = props.get('wof:concordances', {})
            
            other_src = self.concordances_key
            other_id = concordances.get(other_src, None)

            if other_id:
                self.concordances_idx.import_concordance(wofid, other_id, other_src)
                logging.info("concordifying %s with %s:%s" % (wofid, other_src, other_id))
                
        #

        return self.write_feature(f, **kwargs)

    def export_alt_features(self, f, alt, **kwargs):
        
        return self.write_alt_features(f, alt, **kwargs)

    def write_feature(self, f, **kwargs):

        path = self.feature_path(f)
        root = os.path.dirname(path)

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

    def write_alt_features(self, f, alt, **kwargs):

        path = self.feature_path(f, alt=True)
        root = os.path.dirname(path)

        if kwargs.get('skip_existing', False) and os.path.exists(path):
            logging.debug("%s already exists so whatEVAR" % path)
            return True

        if not os.path.exists(root):
            os.makedirs(root)

        logging.info("writing %s" % (path))

        try:
            fh = open(path, 'w')
            self.write_json(alt, fh)
            fh.close()
        except Exception, e:
            logging.error("failed to write %s, because %s" % (path, e))
            return False

        return True

    def feature_path(self, f, **kwargs):

        props = f['properties']
        wofid = props.get('wof:id', None)

        fname = mapzen.whosonfirst.utils.id2fname(wofid, **kwargs)
        parent = mapzen.whosonfirst.utils.id2path(wofid)

        root = os.path.join(self.root, parent)
        path = os.path.join(root, fname)

        return path

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

    # This is left to subclasses to define

    def massage_feature(self, f):
        pass

    def hash_geom(self, f):

        geom = f['geometry']
        geom = json.dumps(geom)

        hash = hashlib.md5()
        hash.update(geom)
        return hash.hexdigest()
