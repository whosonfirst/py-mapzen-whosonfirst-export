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

import mapzen.whosonfirst.utils
import woe.isthat

class flatfile:

    def __init__(self, root, **kwargs):

        path = os.path.abspath(root)        
        self.root = path

        self.debug = kwargs.get('debug', False)

        # concordances stuff - for when we are plowing through
        # a dataset that takes a long time and may need to be
        # restarted.

        concordances_db = kwargs.get('concordances_db', None)
        concordances_key = kwargs.get('concordances_key', None)

        self.concordances_db = None
        self.concordances_key = None

        if concordances_db:

            if not concordances_key:
                raise Exception, "You forget to specify a concordances key"
            
            self.concordances_key = concordances_key

            i = woe.isthat.importer(concordances_db)
            self.concordances_db = i

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

        wofid = props.get('wof:id', None)

        # do we have a concordance with which to help find ourselves ?

        if not wofid:

            if self.concordances_db:

                lookup = props.get(self.concordances_key, None)

                if lookup:
                    wofid = self.concordances_db.woe_id(lookup)
                    logging.debug("got %s for %s" % (wofid, lookup))

                    if wofid != 0:
                        props['wof:id'] = wofid
                    else:
                        wofid = None
                else:
                    logging.warning("failed to find concordances key %s" % lookup)

        if not wofid:

            logging.debug("This record has no wofid so now asking what Brooklyn would do...")

            wofid = mapzen.whosonfirst.utils.generate_id()

            if wofid == 0:
                logging.error("OH NO - can't get integer!")
                return False

            props['wof:id'] = wofid

        # what time is it?

        now = int(time.time())
        props['wof:lastmodified'] = now

        f['properties'] = props

        if self.debug:
            logging.info("debugging is enabled so not writing anything to disk...")
            logging.info("if I did though I would write stuff to %s" % (self.feature_path(f)))

            logging.info(pprint.pformat(props))
            return True

        # store concordances

        if self.concordances_db:

            concordance = props.get(self.concordances_key, None)
            logging.info("%s : %s" % (self.concordances_key, concordance))

            if concordance:
                logging.info("concordifying %s with %s" % (wofid, concordance))
                self.concordances_db.import_concordance(wofid, concordance)
            else:
                logging.warning("unable to find %s key to concordify with %s" % (self.concordance_key, wofid))

                
        #

        return self.write_feature(f, **kwargs)

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

    def feature_path(self, f):

        props = f['properties']
        wofid = props.get('wof:id', None)

        fname = "%s.geojson" % wofid
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