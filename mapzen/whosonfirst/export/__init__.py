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
import shapely.geometry
import random
import atomicwrites

# See this - it's because of some hair-brained nonsense importing
# things in OS X... I have no idea, honestly (20151109/thisisaaronland)

import mapzen.whosonfirst.utils as u
import mapzen.whosonfirst.geojson as g

class flatfile:

    def __init__(self, root, **kwargs):

        path = os.path.abspath(root)        
        self.root = path

        self.debug = kwargs.get('debug', False)

        # the thing that actually generates the geojson
        # we write to disk

        encoder = g.encoder()
        self.encoder = encoder

        # concordances stuff - for when we are plowing through
        # a dataset that takes a long time and may need to be
        # restarted.

        self.concordances = kwargs.get('concordances', False)
        self.concordances_dsn = kwargs.get('concordances_dsn', None)
        self.concordances_key = kwargs.get('concordances_key', None)

        # because this: http://initd.org/psycopg/docs/usage.html#thread-safety       

        self.concordances_idx_maxconns = 20
        self.concordances_qry_maxconns = 20
        
        self.concordances_idx_conns = []
        self.concordances_qry_conns = []

        if self.concordances and not self.concordances_key:
            raise Exception, "Missing concordances key"

        if self.concordances and not self.concordances_dsn:
            raise Exception, "Missing concordances DSN"

        logging.debug("enable concordances for exporter: %s" % self.concordances)

        if self.concordances:

            try:
                import mapzen.whosonfirst.concordances
            except Exception, e:
                logging.error("failed to import mapzen.whosonfirst.concordances because %s" % e)
                raise Exception, e

            self.concordances_dsn = concordances_dsn
            self.concordances_key = concordances_key

            # because this: http://initd.org/psycopg/docs/usage.html#thread-safety       

            self.concordances_idx_maxconns = 20
            self.concordances_qry_maxconns = 20

            self.concordances_idx_conns = []
            self.concordances_qry_conns = []

            self.concordances = True

    # see what's going on here? we're invoking and returning new connections
    # everytime (assuming they will get disconnected when the variables fall
    # out scope) so that we can not get blocked waiting on postgres when doing
    # stuff in a multiprocessing environment (20150902/thisisaaronland)

    def concordances_idx(self):

        if len(self.concordances_idx_conns) < self.concordances_idx_maxconns:

            conn = mapzen.whosonfirst.concordances.index(self.concordances_dsn)
            self.concordances_idx_conns.append(conn)

            logging.debug("return new concordances index connection")
            return conn

        logging.debug("return existing concordances index connection")
        random.shuffle(self.concordances_idx_conns)
        return self.concordances_idx_conns[0]

    def concordances_qry(self):

        if len(self.concordances_qry_conns) < self.concordances_qry_maxconns:

            conn = mapzen.whosonfirst.concordances.query(self.concordances_dsn)
            self.concordances_qry_conns.append(conn)

            logging.debug("return new concordances query connection")
            return conn

        logging.debug("return existing concordances query connection")
        random.shuffle(self.concordances_qry_conns)
        return self.concordances_qry_conns[0]

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
        props['wof:geomhash'] = u.hash_geom(f)

        # who am I ?
        # have I been here before ?
        # why is the sky blue ?

        wofid = None

        if props.has_key('wof:id'):
            wofid = props['wof:id']

        # do we have a concordance with which to help find ourselves ?

        if wofid == None:

            if self.concordances:

                concordances = props.get('wof:concordances', {})

                other_src = self.concordances_key
                other_id = concordances.get(other_src, None)

                if other_id:

                    qry = self.concordances_qry()
                    row = qry.by_other_id(other_id, other_src)

                    logging.debug("concordance lookup %s:%s is %s" % (other_src, other_id, row))

                    if row:
                        wofid = row[0]
                        props['wof:id'] = wofid
                    else:
                        wofid = None

                else:
                    logging.warning("failed to find concordances key %s:%s" % (other_src, other_id))

        if wofid == None:

            logging.debug("This record has no wofid so now asking what Brooklyn would do...")

            wofid = u.generate_id()

            if wofid == 0:
                logging.error("OH NO - can't get integer!")
                return False

            props['wof:id'] = wofid
            f['id'] = wofid

        # what time is it?

        now = int(time.time())
        props['wof:lastmodified'] = now

        # TO DO: FIGURE OUT HOW TO DERIVE DEFAULTS FROM
        # py-mapzen-whosonfirst-validator (20150922/thisisaaronland)

        # stubs

        for k in ('supersedes', 'superseded_by', 'hierarchy', 'belongsto', 'breaches'):
            k = "wof:%s" % k

            if not props.get(k, False):
                props[k] = []

        # ensure edtf stuff

        for k in ('inception', 'cessation'):
            k = "edtf:%s" % k

            if not props.has_key(k):
                props[k] = u"u"	# section 5.2.2 (EDTF)

        # ensure hierarchy contains self

        for h in props['wof:hierarchy']:

            k = "%s_id" % props['wof:placetype']
            v = props['wof:id']

            if not h.get(k, False) or h[k] == -1:
                h[k] = v

        # ensure belongs to

        belongsto = []

        for h in props['wof:hierarchy']:

            for ignore, id in h.items():

                if id != wofid and id != -1 and not id in belongsto:
                    belongsto.append(id)

        props['wof:belongsto'] = belongsto

        # ensure tags

        tags = props.get('wof:tags', [])
        props['wof:tags'] = tags

        # ensure wof:country

        props['wof:country'] = props.get('iso:country', '')

        # ensure minimum viable geom: properties
        # maybe move this in to mapzen.whosonfirst.utils
        # as we do with bbox ?

        shp = shapely.geometry.asShape(f['geometry'])
        bbox = list(shp.bounds)
        coords = shp.centroid
        area = shp.area
        
        props['geom:latitude'] = coords.y
        props['geom:longitude'] = coords.x
        props['geom:area'] = area
        props['geom:bbox'] = ",".join(map(str, bbox))

        f['bbox'] = bbox
        f['properties'] = props

        if self.debug:

            path = self.feature_path(f)

            logging.info("debugging is enabled so not writing anything to disk...")
            logging.info("if I did though I would write stuff to %s" % path)
            logging.debug(pprint.pformat(props))

            root = os.path.dirname(path)
            fname = os.path.basename(path)
            fname = "DEBUG-%s" % fname
            path = os.path.join(root, fname)

            return path

        # store concordances

        if self.concordances:

            concordance = props.get('wof:concordances', {})
            
            other_src = self.concordances_key
            other_id = concordances.get(other_src, None)

            if other_id:
                idx = self.concordances_idx()
                idx.import_concordance(wofid, other_id, other_src)
                logging.info("concordifying %s with %s:%s" % (wofid, other_src, other_id))
                
        #

        return self.write_feature(f, **kwargs)

    def export_alt_feature(self, f, **kwargs):

        _props = wof['properties']
        _props['wof:geomhash'] = u.hash_geom(_f)

        f['properties'] = _props

        return self.write_feature(f, **kwargs)

    def write_feature(self, f, **kwargs):

        indent = kwargs.get('indent', None)

        path = self.feature_path(f)
        root = os.path.dirname(path)

        if kwargs.get('skip_existing', False) and os.path.exists(path):
            logging.debug("%s already exists so whatEVAR" % path)
            return path

        if not os.path.exists(root):
            os.makedirs(root)

        logging.info("writing %s" % (path))

        try:

            with atomicwrites.atomic_write(path, overwrite=True) as fh:
                self.encoder.encode_feature(f, fh)

        except Exception, e:
            logging.error("failed to write %s, because %s" % (path, e))
            return None

        return path

    def feature_path(self, f, **kwargs):

        wofid = None

        if f['type'] == 'Feature':
            props = f['properties']
            wofid = props.get('wof:id', None)

        elif f['type'] == 'FeatureCollection':
            
            for _f in f['features']:
                props = _f['properties']
                wofid = props.get('wof:id', None)

                if wofid:
                    break
        else:
            pass

        if not wofid:
            raise Exception, "Missing WOF ID"

        fname = u.id2fname(wofid, **kwargs)
        parent = u.id2path(wofid)

        root = os.path.join(self.root, parent)
        path = os.path.join(root, fname)

        return path

    # This is left to subclasses to define

    def massage_feature(self, f):
        pass
