import json
import statistics
from math import radians, sin, cos, sqrt, asin
import pandas as pd
import numpy as np
from models import AdministrativeUnit, Base, Zip, CustomArea


class Point:
    def __init__(self, lat, lon):
        self.lat = float(lat)
        self.lon = float(lon)


def make_point(x: str) -> Point:
    result = None
    tmp = x.split(',')
    if len(tmp) == 2:
        print('hereeeeeee')
        result = Point(lat=tmp[1],
                       lon=tmp[0])
    else:
        tmp = x.split(' ')
        if len(tmp) == 2:
            result = Point(lat=tmp[1],
                           lon=tmp[0])
    return result


def create_data(data: json) -> list[Base]:
    result = []
    for i in range(len(data)):
        coords = data[i]['fields'].get('coordinates')
        if coords:
            coords = make_point(coords.replace('POINT(', '').replace(')', ''))
        result.append(Base(model=data[i]['model'],
                           pk=data[i].get('pk'),
                           fields=Zip(administrative_unit_id=data[i]['fields'].get('administrative_unit_id'),
                                      code=data[i]['fields'].get('code'),
                                      country_id=data[i]['fields'].get('country_id'),
                                      google_maps_id=data[i]['fields'].get('google_maps_id'),
                                      coordinates=coords,
                                      custom_area_id=data[i]['fields'].get('custom_area_id'))
                           )
                      )
    return result


def calculate_distance(point1: Point, point2: Point):
    """
    Calculates the distance between two points using the haversine formula
    Distance is calculated in kilometers.
    https://www.movable-type.co.uk/scripts/latlong.html
    """
    earth_radius_km = 6372.8
    d_lat = radians(point2.lat - point1.lat)
    d_lon = radians(point2.lon - point1.lon)
    lat_r1 = radians(point1.lat)
    lat_r2 = radians(point2.lat)

    a = sin(d_lat / 2) ** 2 + cos(lat_r1) * cos(lat_r2) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))

    return earth_radius_km * c


def find_all_distances(x: Base, y: list[Base]) -> list:
    data = []
    x_coords = x.fields.coordinates
    if x_coords:
        for obj in y:
            if obj.fields.coordinates and obj is not x:
                distance = calculate_distance(x_coords, obj.fields.coordinates)
                data.append(distance)
            else:
                continue
    return data


def find_outlier_point(custom_areas: dict):
    data = {}
    for custom_area, distance in custom_areas.items():
        my_list = [value for key, value in custom_areas.items() if key is not custom_area]
        ca_mean = np.mean(my_list)
        ca_std = np.std(my_list)
        if distance > ca_mean + (3 * ca_std):
            data[custom_area] = (distance - (ca_mean + (3 * ca_std)))
    return data


def find_groups(postal_codes):
    data = {}
    data_distances = {}
    data_mean_distances = {}
    data_outliers = {}

    # Create Zip groups
    grouped_data = {'CustomArea': [],
                    'ZipObjects': [],
                    'all_distances': [],
                    'mean_distances': [],
                    'outlying_zips': []}

    for postal_code in postal_codes:
        data.setdefault(postal_code.fields.custom_area_id, []).append(postal_code)

    grouped_data['CustomArea'] = data.keys()
    grouped_data['ZipObjects'] = data.values()

    # Find Distances with in groups
    for group in grouped_data['ZipObjects']:
        data_all_distances = {}
        data_group_mean_distances = {}

        for zip_object in group:
            if zip_object.fields.coordinates:
                distances = find_all_distances(zip_object, group)
                if len(distances) > 0:
                    data_all_distances[zip_object.fields.code] = distances
                    data_group_mean_distances[zip_object.fields.code] = np.mean(distances)
        data_distances[group[0].fields.custom_area_id] = data_all_distances
        data_mean_distances[group[0].fields.custom_area_id] = data_group_mean_distances
        data_outliers[group[0].fields.custom_area_id] = find_outlier_point(
            data_mean_distances[group[0].fields.custom_area_id])

    grouped_data['all_distances'] = data_distances.values()
    grouped_data['mean_distances'] = data_mean_distances.values()
    grouped_data['outlying_zips'] = data_outliers.values()
    return grouped_data


if __name__ == '__main__':
    # Load Zip data
    f = open('output/new_zips_sweden.json')
    zip_data = create_data(json.load(f))

    df = find_groups(zip_data)
    out_df = pd.DataFrame.from_dict(df)


