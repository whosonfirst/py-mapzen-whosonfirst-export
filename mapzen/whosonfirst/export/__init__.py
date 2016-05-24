# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import types
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

        # also, what time is it?
        now = int(time.time())

        wofid = None

        if props.has_key('wof:id'):
            wofid = props['wof:id']

        # PLEASE UPDATE ME TO DO CONCORDANCES AGAIN, YEAH?

        if wofid == None:

            logging.debug("This record has no wofid so now asking what Brooklyn would do...")

            wofid = u.generate_id()

            if wofid == 0:
                logging.error("OH NO - can't get integer!")
                return False

            props['wof:id'] = wofid
            props['wof:created'] = now


        f['id'] = props['wof:id']

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

            # section 5.2.2 (EDTF) - this appears to have changed to 'XXXX' as of
            # the draft sent to ISO (201602) but we're just going to wait...

            if not props.has_key(k):
                props[k] = u"uuuu"

            # my bad - just adding it here in advance of a proper
            # backfill (20160107/thisisaaronland)

            if props.get(k) == "u":
                props[k] = u"uuuu"

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

        if not props.get('wof:country', False):
            props['wof:country'] = props.get('iso:country', '')
        elif props.get('wof:country') == '':
            props['wof:country'] = props.get('iso:country', '')
        else:
            pass

        if not props.get('iso:country', False):
            props['iso:country'] = prop.get('wof:country', '')

        # names - ensure they are lists

        for k, v in props.items():

            if not k.startswith("name:"):
                continue

            if type(v) == types.ListType:
                continue

            if type(v) == types.TupleType:
                props[k] = list(v)
                continue

            # Hey look - see the way we're splitting on ";"?
            # It's pretty arbitrary as far as decisions go.
            # We will keep doing that until we don't...
            # (20160524/thisisaaronland)

            if type(v) == types.UnicodeType:

                props[k] = v.split(";")
                continue

            if type(v) == types.StringType:
                v = unicode(v)
                props[k] = v.split(";")
                continue

            logging.warning("WHAT AM I SUPPOSED TO DO WITH %s (%s) which is a %s" % (k, v, type(v)))

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

        # PLEASE UPDATE ME TO DO CONCORDANCES AGAIN... MAYBE?

        return self.write_feature(f, **kwargs)

    def export_alt_feature(self, f, **kwargs):

        _props = f['properties']
        _props['wof:geomhash'] = u.hash_geom(f)

        f['id'] = _props['wof:id']

        f['properties'] = _props

        shp = shapely.geometry.asShape(f['geometry'])
        bbox = list(shp.bounds)

        f['bbox'] = bbox
        return self.write_feature(f, **kwargs)

    def write_feature(self, f, **kwargs):

        indent = kwargs.get('indent', None)

        path = self.feature_path(f, **kwargs)
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

        perms = kwargs.get('perms', 0644)

        if perms != None:
            os.chmod(path, perms)

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

        # Because remember we made life hard for ourselves by making
        # the Earth WOF ID... zero. Good times.
        # (20160112/thisisaaronland)

        if wofid == None:
            raise Exception, "Missing WOF ID"

        fname = u.id2fname(wofid, **kwargs)
        parent = u.id2path(wofid)

        root = os.path.join(self.root, parent)
        path = os.path.join(root, fname)

        return path

    # This is left to subclasses to define

    def massage_feature(self, f):
        pass
