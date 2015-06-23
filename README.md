# py-mapzen-pelias

Simple Python wrapper for the Mapzen Pelias API

## Usage

### Simple

### Geocoding

	import mapzen.pelias
	api = mapzen.pelias.api()

	method = 'search'
	params = {'input':'brooklyn'}

	rsp = api.execute_method(method, params)

	print type(rsp)
	<class 'geojson.feature.FeatureCollection'>	

### Reverse-geocoding

	import mapzen.pelias
	api = mapzen.pelias.api()

	method = 'reverse'
	params = {'lat': 37.775740, 'lon': -122.413595}

	rsp = api.execute_method(method, params)

	print type(rsp)
	<class 'geojson.feature.FeatureCollection'>	

### Less simple

#### Formatting results as Markdown

_Important: This part is incomplete and may not even produce valid Markdown yet..._

	import mapzen.pelias
	api = mapzen.pelias.api()

	method = 'search'
	params = {'input':'brooklyn'}

	rsp = api.execute_method(method, params)

	fmt = mapzen.pelias.formatter(rsp)
	fmt.markdown(sys.stdout)

## See also

* http://pelias.mapzen.com/
