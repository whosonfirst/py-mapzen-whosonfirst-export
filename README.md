# py-mapzen-whosonfirst-export

Export tools for the Who's On First

## Install

```
sudo pip install -r requirements.txt --process-dependency-links .
```

### Caveats

This won't work without `--process-dependency-links` so I am not sure yet what happens when it gets removed from pip 1.6...

## IMPORTANT

This library is provided as-is, right now. It lacks proper documentation which will probably make it hard for you to use unless you are willing to poke and around and investigate things on your own.

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
