from main import get_coordinates
from anomaly_finder import make_point, calculate_distance
from tqdm import tqdm
import json
import pandas as pd
import ast

if __name__ == '__main__':
    out_data = {'code': [],
                'nominatim_coords_lat': [],
                'nominatim_coords_lon': [],
                'google_coords_lat': [],
                'google_coords_lon': [],
                'distance': []}

    # Get suspected coordinated
    data = pd.read_csv('/Users/ahmarabbas/Desktop/Marketer/random.csv', ';')
    data = data.drop(columns=['Unnamed: 0'], index=0)

    suspected_coords = []
    for datapoint in data.outlying_zips:
        datapoint = ast.literal_eval(datapoint)
        for key, value in datapoint.items():
            if value >= 2:
                suspected_coords.append(key)

    # Load Zip data
    f = open('data/zips_sweden.json')
    zip_data = json.load(f)

    for suspect in tqdm(suspected_coords):
        nominatim_coords = (get_coordinates(suspect.replace(' ', '+')))
        google_coords = None
        distance = None
        for x in zip_data:
            if x.get('fields').get('code') == suspect and x.get('fields').get('coordinates'):
                google_coords = x.get('fields').get('coordinates')
                break

        if nominatim_coords and google_coords:
            nominatim_coords = make_point(nominatim_coords.replace('POINT(', '').replace(')', ''))
            google_coords = make_point(google_coords.replace('POINT(', '').replace(')', ''))
            distance = calculate_distance(nominatim_coords, google_coords)

            out_data['code'].append(suspect)
            out_data['nominatim_coords_lat'].append(nominatim_coords.lat)
            out_data['nominatim_coords_lon'].append(nominatim_coords.lon)
            out_data['google_coords_lat'].append(google_coords.lat)
            out_data['google_coords_lon'].append(google_coords.lon)
            out_data['distance'].append(distance)
