# py-mapzen-gazetteer-export

Export tools for the Who's On First

## Install

Depending on which version of rage-making Python or more likely the rage-making-er `setuptools` you are using you may need to expicitly tell the install script to put the command line tools in `/usr/local/bin` like this:

```
sudo python ./setup.py install --install-scripts /usr/local/bin
```

## Usage

_Please write me_

## Command line tools

### wof-concordify

```
$> /usr/local/bin/wof-concordify -s /usr/local/mapzen/gaztteer -f 'wof:puid' -c /usr/local/mapzen/gazetteer-concordances/concordances-wofid-wofpuid.csv
```
