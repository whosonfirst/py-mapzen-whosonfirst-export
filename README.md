# py-mapzen-whosonfirst-export

Export tools for the Who's On First

## Description

This package provides library code and tools for "exportifying" Who's Of First
(WOF) GeoJSON documents which makes them ready to be included in a commit or
pull request in a [https://github.com/whosonfirst-data](whosonfirst-data)
repository. 

When a WOF record is "exportified" a number of derived properties are
automatically updated (for example `wof:belongsto`, `src:geom_hash` and
`wof:lastmodified`) and the document is formatted according to the WOF style
guide (specifically that GeoJSON properties but _not_ geometries be indented).

## Install

```
sudo pip install -r requirements.txt --process-dependency-links .
```

### Caveats

* This won't work without `--process-dependency-links` so I am not sure yet what
  happens when it gets removed from pip 1.6...

* This package has _a lot_ of dependencies including things that require
  installing compiled code from other sources, like `GDAL` and other geo-related
  tools. There is a handy
  [docker-whosonfirst-exportify](https://github.com/whosonfirst/docker-whosonfirst-exportify)
  container image if you just want to get started using the command line tools
  and don't need to use the underlying library code in your own work.

## IMPORTANT

This library is provided as-is, right now. It lacks proper documentation which
will probably make it hard for you to use unless you are willing to poke and
around and investigate things on your own. 

## Example

### Export records to STDOUT

```
import os
import sys

import mapzen.whosonfirst.utils
import mapzen.whosonfirst.export

if __name__ == "__main__":

    ex = mapzen.whosonfirst.export.stdout()

    for path in sys.argv[1:]:
        f = mapzen.whosonfirst.utils.load_file(path)
        ex.export_feature(f)
```

### Export records to a string

```
import os
import sys

import mapzen.whosonfirst.utils
import mapzen.whosonfirst.export

if __name__ == "__main__":

    ex = mapzen.whosonfirst.export.string()

    for path in sys.argv[1:]:
        f = mapzen.whosonfirst.utils.load_file(path)
        print ex.export_feature(f)
```

### Export records to a nested directory structure

```
import os
import sys

import mapzen.whosonfirst.utils
import mapzen.whosonfirst.export

if __name__ == "__main__":

    data_root = "/path/to/data"
    ex = mapzen.whosonfirst.export.flatfile(data_root)

    for path in sys.argv[1:]:
        f = mapzen.whosonfirst.utils.load_file(path)
        ex.export_feature(f)
```

## Tools

### wof-exportify

For example:

```
./scripts/wof-exportify -e stdout -p 101736545.geojson | jq '.properties["wof:name"]'
"Montreal"
```

## See also

* https://github.com/whosonfirst/whosonfirst-data/
* https://github.com/whosonfirst/whosonfirst-www-exportify
* https://github.com/whosonfirst/docker-whosonfirst-exportify
