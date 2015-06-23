import requests

def reverse_geo_neighbourhoods(lat, lon, **kwargs):
    
    endpoint = kwargs.get('endpoint', 'http://localhost:5001/')

    params = {'lat': lat, 'lng': lon}

    rsp = requests.get(endpoint, params=params)

    data = json.loads(rsp.content)

    possible = []

    for row in data:

        woeid = row.get('woe_id', None)

        if woeid:
            possible.append(str(woeid))

    return possible

def reverse_geo_localities(lat, lon):
    
    endpoint = kwargs.get('endpoint', 'http://localhost:5003/')
    params = {'lat': lat, 'lng': lon}

    rsp = requests.get(endpoint, params=params)

    data = json.loads(rsp.content)

    possible = []

    for row in data:

        gnid = row.get('qs_gn_id', None)

        if gnid:
            possible.append(str(gnid))

    return possible
