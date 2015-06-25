# py-mapzen-gazetteer-export

Export tools for the Mapzen gazetteer

## Usage

_Please write me_

## Command line tools

### mzg-concordify

	$> /usr/local/bin/mzg-concordify -s /usr/local/mapzen/gaztteer -f 'mz:puid' -c /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.csv

### mzg-exportify

	$> /usr/local/bin/mzg-exportify -d /usr/local/mapzen/gazetteer -s openvenues -c /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.csv --skip --verbose /usr/local/mapzen/openvenues-data/*_*.geojson


Or this, if you're being thorough about things. Note the part where we are generating a concordances database (using `woeisthat-import`) from a concordances dump thar we are generating post-export (using `mzg-concordify`). This suggests a separate wrapper tool to bundle all the things, but not today.

	$> /usr/local/bin/woeisthat-import -d concordances-mzid-mzpuid.db -s csv concordances-mzid-mzpuid.csv

	$> /usr/local/bin/mzg-exportify -d /usr/local/mapzen/gazetteer -s openvenues -c /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.csv --skip --verbose /usr/local/mapzen/openvenues-data/*_*.geojson

	$> /usr/local/bin/mzg-concordify -s /usr/local/mapzen/gaztteer -f 'mz:puid' -c /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.csv

## Known knowns

* Something something something generate concordance lookups on the fly / at start up...

* For some reason simply listing Al's [address_normalizer](https://github.com/openvenues/address_normalizer) library in `setup.py` causes the install stuff to break. I have no idea...

## See also

* [py-mapzen-gazetteer](https://github.com/mapzen/py-mapzen-gazetteer)
