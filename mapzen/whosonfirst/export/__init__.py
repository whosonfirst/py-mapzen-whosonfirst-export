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

import edtf
import arrow

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

        # ensure 'mz:' properties
        # https://github.com/whosonfirst/whosonfirst-data/issues/320

        if props.get('mz:hierarchy_label', None) == None:

            props['mz:hierarchy_label'] = 1

        is_current = props.get("mz:is_current", None)

        if not is_current in (-1, 0, 1):

            if str(is_current) == "-1":
                is_current = -1
            elif str(is_current) == "0":
                is_current = 0
            elif str(is_current) == "1":
                is_current = 1
            else:
                is_current = -1
                
            props['mz:is_current'] = is_current

        # ensure 'wof:repo'
        # https://github.com/whosonfirst/whosonfirst-data/issues/338

        if props.get('wof:repo', None) == None:

            data_root = self.root
            repo_root = os.path.dirname(data_root)
            props['wof:repo'] = os.path.basename(repo_root)

        # ensure edtf stuff - it might be time for py-whosonfirst-dates/edtf package
        # but not today... (20180503/thisisaaronland)

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

        # now we try to append upper/lower ranges for inception and cessation
        # dates - specifically plain vanilla YMD values that can be indexed by
        # plain old databases (20180503/thisisaaronland)

        # note the use of arrow (.py) since datetime.strptime can't deal with
        # parsing YYYY-MM-DD dates before 1900 because... I mean really, who
        # cares why it's just kind of... bad (20180503/thisisaaronland)

        inception = props.get("edtf:inception", "")
        cessation = props.get("edtf:cessation", "")        

        fmt = "YYYY-MM-DD"

        # skip "uuuu" because it resolves to 0001-01-01 9999-12-31 (in edtf.py land)
        
        if not inception in ("", "uuuu"):
            try:
            
                e = edtf.parse_edtf(unicode(inception))

                lower = arrow.get(e.lower_strict())
                upper = arrow.get(e.upper_strict())
                
                props["date:inception_lower"] = lower.format(fmt)
                props["date:inception_upper"] = upper.format(fmt)

            except Exception, e:
                logging.warning("Failed to parse inception '%s' because %s" % (inception, e))

            if not cessation in ("", "uuuu", "open"):                

                # we'll never get here because of the test above but the point
                # is a) edtf.py freaks out when an edtf string is just "open" (not
                # sure if this is a me-thing or a them-thing and b) edtf.py interprets
                # "open" as "today" which is not what we want to store in the database
                # (20180418/thisisaaronland)
                
                if cessation == "open" and not inception in ("", "uuuu"):
                    cessation = "%s/open" % inception
                
                try:                
                    e = edtf.parse_edtf(unicode(cessation))

                    lower = arrow.get(e.lower_strict())
                    upper = arrow.get(e.upper_strict())
                    
                    props["date:cessation_lower"] = lower.format(fmt)
                    props["date:cessation_upper"] = upper.format(fmt)

                except Exception, e:
                    logging.warning("Failed to parse cessation '%s' because %s" % (cessation, e))
                    
        # end of edtf stuff

        # ensure hierarchy contains self

        for h in props['wof:hierarchy']:

            k = "%s_id" % props['wof:placetype']
            v = props['wof:id']

            if not h.get(k, False) or h[k] == -1:
                h[k] = int(v)

        # ensure belongs to

        belongsto = []

        for h in props['wof:hierarchy']:

            for ignore, id in h.items():

                if id != wofid and id != -1 and not id in belongsto:
                    belongsto.append(id)

        props['wof:belongsto'] = belongsto

        if props['wof:parent_id'] > 0 and not props['wof:parent_id'] in props['wof:belongsto']:
            props['wof:belongsto'].append(props['wof:parent_id'])

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
            props['iso:country'] = props.get('wof:country', '')

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

        try:
            shp = shapely.geometry.asShape(f['geometry'])
        except Exception, e:
            path = self.feature_path(f)
            logging.error("feature (%s) has a bunk geoemtry!" % path)
            raise Exception, e

        bbox = list(shp.bounds)
        coords = shp.centroid
        area = shp.area

        props['geom:latitude'] = coords.y
        props['geom:longitude'] = coords.x
        props['geom:area'] = area
        props['geom:bbox'] = ",".join(map(str, bbox))

        try:

            # From Kelso (21060722/thisisaaronland)
            # 
            # Global" equal area projection: http://spatialreference.org/ref/epsg/3410/
            # if you wanted to get super geeky for the poles, you’d do this one above 86°: http://spatialreference.org/ref/epsg/3408/
            # and this one below -86°: http://spatialreference.org/ref/epsg/3409/
            # (they look like this: http://nsidc.org/data/ease/)
            # EASE | Overview | National Snow and Ice Data Center
            # What is EASE-Grid? The Equal-Area Scalable Earth Grid (EASE-Grid) is intended to be a versatile format for global-scale
            # gridded data, specifically remotely sensed data, although it has gained popularity as a common gridding scheme for other
            # data as well. Data from various sources can be expressed as digital arrays of varying grid resolutions, which are defined
            # in relation to one of three possible projections: Northern and Southern Hemisphere (Lambert's equal-area, azimuthal) and
            # full global (cylindrical, Show more... 
            # It’s known as "Cylindrical Equal-Area”, but I guess it’s called the other thing in EPSG because that agency was the first
            # one to add it under their own product name. </sigh>
            # https://nsidc.org/data/atlas/epsg_3410.html

            from osgeo import ogr
            from osgeo import osr

            source = osr.SpatialReference()
            source.ImportFromEPSG(4326)

            target = osr.SpatialReference()
            target.ImportFromEPSG(3410)

            transform = osr.CoordinateTransformation(source, target)

            poly = ogr.CreateGeometryFromJson(geojson.dumps(f['geometry']))
            poly.Transform(transform)

            sq_m = format(poly.GetArea(), 'f')
            props['geom:area_square_m'] = float(sq_m)

        except Exception, e:
            logging.warning("failed to calculate area in square meters, because %s" % e)

        f['bbox'] = bbox

        # ensure that all properties are prefixed

        for k, v in props.items():

            parts = k.split(":", 1)

            if len(parts) == 2:
                continue
            
            old_k = k
            new_k = "misc:%s" % parts[0]
        
            props[new_k] = v
            del(props[old_k])

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

        return self.write_feature(f, **kwargs)

    # see this – there is currently no 'export_display_feature' method
    # there probably should be but today there isn't...
    # (20160822/thisisaaronland)

    def export_alt_feature(self, f, **kwargs):

        _props = f['properties']
        _props['wof:geomhash'] = u.hash_geom(f)

        f['id'] = _props['wof:id']

        f['properties'] = _props

        shp = shapely.geometry.asShape(f['geometry'])
        bbox = list(shp.bounds)

        f['bbox'] = bbox

        # https://github.com/whosonfirst/py-mapzen-whosonfirst-uri/blob/master/mapzen/whosonfirst/uri/__init__.py
        #
        # remember that is where filenames are sorted out and as of this writing
        # it's not very sophisticated. like if you're thinking "I wonder if..."
        # the answer is probably still no-slash-patches-welcome
        # (21060822/thisisaaronland)

        if not kwargs.get('alt', None):
            alt = _props.get('src:geom', 'unknown')
            kwargs['alt'] = alt

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
