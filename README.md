# py-mapzen-gazetteer-export

Export tools for the Mapzen gazetteer

## Install

Depending on which version of rage-making Python or more likely the rage-making-er `setuptools` you are using you may need to expicitly tell the install script to put the command line tools in `/usr/local/bin` like this:

```
sudo python ./setup.py install --install-scripts /usr/local/bin
```

## Usage

_Please write me_

## Command line tools

### mzg-concordify

```
$> /usr/local/bin/mzg-concordify -s /usr/local/mapzen/gaztteer -f 'mz:puid' -c /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.csv
```

### mzg-exportify

```
$> /usr/local/bin/mzg-exportify -d /usr/local/mapzen/gazetteer-local -s openvenues --concordances-db /usr/local/mapzen/gazetteer-concordances/concordances-mzid-mzpuid.db --concordances-key 'mz:puid' --skip --verbose /usr/local/mapzen/openvenues-data/*_*.geojson
```

By default this tool expects a list of GeoJSON files on the command-line. A subset of specific import sources allow you to pass a directory that will be traversed (in search of GeoJSON files). For example:

```
$> /usr/local/bin/mzg-exportify -d /usr/local/mapzen/gazetteer-local -s woedb --place-type timezone --concordances-db /usr/local/mapzen/gazetteer-concordances/concordances-mzid-woedb.db --concordances-key 'woe:id' --skip --verbose /usr/local/mapzen/woe-data/whereonearth-timezone/data
```

## Known knowns

* For some reason simply listing Al's [address_normalizer](https://github.com/openvenues/address_normalizer) library in `setup.py` causes the install stuff to break. I have no idea...

## See also

* [py-mapzen-gazetteer](https://github.com/mapzen/py-mapzen-gazetteer)
