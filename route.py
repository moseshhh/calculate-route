import pandas as pd
import googlemaps
from geojson import Feature, FeatureCollection, LineString

def decode_polyline(polyline_str):
    '''Pass a Google Maps encoded polyline string; returns list of lat/lon pairs'''
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']: 
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index+=1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append(( lng / 100000.0, lat / 100000.0 ))

    return coordinates

def find_route(origin,destination):
    gmaps = googlemaps.Client(key="Insert your API Key")
    direction_result = gmaps.directions(origin, destination, mode="driving", avoid="tolls")

    result = {
        "distance" : direction_result[0]['legs'][0]['distance']['value'],
        "distance_km" : direction_result[0]['legs'][0]['distance']['text'],
        "duration_min" : direction_result[0]['legs'][0]['duration']['text'],
        "duration_second" : direction_result[0]['legs'][0]['duration']['value'],
        "start_address" : direction_result[0]['legs'][0]['start_address'],
        "end_address" : direction_result[0]['legs'][0]['end_address'],
        "polyline" :  direction_result[0]['overview_polyline']['points'],
    }
    return result


# Read CSV
df = pd.read_csv('origin_dest.csv', index_col="order_no")


feature_array = []

# LOOPING every origin and destination, and execute find_route func and decode_polyline func
for index, row in df.iterrows():
    order_id = index
    origin_lon = row['origin_longitude'].item()
    origin_lat = row['origin_latitude'].item()
    destination_lon = row['destination_longitude'].item()
    destination_lat = row['destination_latitude'].item()
    
    route = find_route("{},{}".format(origin_lat, origin_lon), "{},{}".format(destination_lat, destination_lon))
    decoded_polyline = decode_polyline(route['polyline'])

    # Create Geojson Feature Object
    my_feature = Feature( geometry = LineString(decoded_polyline), properties={
        "order_id" : str( index ),
        "distance" : route['distance'],
        "distance_km" : route['distance_km'],
        "duration_min" : route['duration_min'],
        "duration_second" : route['duration_second'],
        "start_address" : route['start_address'],
        "end_address" : route['end_address']
        }  )
    
    # Append Geojson feature to array
    feature_array.append(my_feature)

# Create Geojson File
my_feature_col = FeatureCollection(feature_array)
file1 = open("route.geojson","w")   
file1.write( str( my_feature_col)) 
file1.close() 
