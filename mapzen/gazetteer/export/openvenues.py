import sys
import logging
import hashlib
import address_normalizer

import mapzen.gazetteer.export
import woe.isthat

class exporter (mapzen.gazetteer.export.flatfile):

    def __init__(self, root, **kwargs):

        mapzen.gazetteer.export.flatfile.__init__(self, root, **kwargs)

    def massage_feature(self, f):

        props = f['properties']
        props['mz:placetype'] = 'venue'
        props['mz:source'] = 'openvenues'

        loc = props.get('locality', '')
        addr = props.get('street_address', '')

        loc = loc.encode('utf8')

        addr = address_normalizer.expand_street_address(addr)
        addr = " ".join(addr)
        addr = addr.encode('utf8')

        md5 = hashlib.md5()
        md5.update("%s %s" % (addr, loc))
        
        puid = md5.hexdigest()
        props['mz:puid'] = puid

        f['properties'] = props
        # pass-by-ref

"""
We are also generating a "puid" (in openvenues_exporter:massage_feature) for
each venue that we subsequently export using export-venues-puids in to a CSV
file that can turned in a woeisthat lookup database. We use this database to
see whether any given puid already has a (brooklyn) UID so that we are not 
constantly assigning new IDs to venues.

If you're thinking this approach is a bit casual and sloppy (and prone to errors
here and there) you'd be right but the point is to stand up something more tangible
(than what we've got) so this is the poison we choose, today.

Also this, from Al:

---
If the goal is just to have unique IDs, we can add random GUIDs e.g. using
str(uuid.uuid4()) to every record. We'll need to assign random IDs anyway for
deduping. 

libpostal is not just the faster version of address_normalizer, it's
significantly more advanced. One particularly important difference is that
address_normalizer is English-only while libpostal is designed to work for
basically any language, so if you're doing a few American cities for maps or a
prototype or whatever and there are too many dupes in the set you have, feel
free to use address_normalizer, but I'd strongly prefer not to publicly release
anything global until it's been run through libpostal. 

If you need address_normalizer in the interim, you wouldn't want to MD5 all the
permutations of the string. In ambiguous cases e.g. ("Dr" => "Drive", "Doctor"),
address_normalizer outputs both possibilities regardless of which one is correct
/ more likely. So:

>>> address_normalizer.expand_street_address('FDR Dr')
{u'fdr doctor', u'fdr drive'}

but

>>> address_normalizer.expand_street_address('FDR Drive')
{u'fdr drive'}

so those two wouldn't match using concatenation as above. This generator is more
correct (assuming the set fits in memory):

    def deduped_venues(places):
        seen = set()
        for props in places:
            addr = props['street_address']
            norm = address_normalizer.expand_street_address(addr)
            new_venue = True
            for n in norm:
                if n in seen:
                    new_venue = False    
                    break
                else:
                    seen.add(n)
            if new_venue:
                props['guid'] = str(uuid.uuid4())
                yield props
---

(20150623/thisisaaronland)
"""
