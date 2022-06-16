import pandas as pd
import json
import os
from models import AdministrativeUnit, Base, Zip, CustomArea
from dataclasses import asdict
import sys
from itertools import groupby, count
from collections import Counter
from statistics import mode


def modify_list(zips: list[Base], custom_units: list[Base], admin_unit: list[Base], new_data: json,
                _zip_max, _custom_area_max,
                _administrative_unit_max):
    for postal_object in new_data:
        code = str(postal_object.get('Postal_Code'))
        code = code[:3] + " " + code[3:]
        if code in [item.fields.code for item in zips]:
            continue
        else:
            # Look up and/or add administrative unit
            _zip_max = _zip_max + 1
            _filtered_admin_unit = match_administrative_unit(admin_unit.copy(), postal_object, zips.copy())
            if _filtered_admin_unit is None:
                continue  # Skip adding zips that doesn't have a matching administration unit

                # _administrative_unit_max = _administrative_unit_max + 1
                # admin_unit, _filtered_admin_unit = add_administrative_unit(admin_unit.copy(), postal_object,
                #                                                            _administrative_unit_max)

            # Look up and add custom area
            _filtered_custom, _filtered_country = match_custom_unit(zips.copy(), code[:3])
            if _filtered_custom is None:
                _custom_area_max = _custom_area_max + 1
                custom_units, _filtered_custom, _filtered_country = add_custom_unit(custom_units.copy(),
                                                                                    admin_unit.copy(),
                                                                                    _custom_area_max,
                                                                                    _filtered_admin_unit
                                                                                    )

            # Add new zipcode
            zips.append(Base(model='targeter.zip',
                             pk=_zip_max,
                             fields=Zip(administrative_unit_id=_filtered_admin_unit,
                                        # postal_object.get('administrative_unit_id'),
                                        code=code,
                                        country_id=_filtered_country,  # postal_object.get('country_id'),
                                        google_maps_id=None,  # postal_object.get('google_maps_id'),
                                        coordinates=None,  # postal_object.get('coordinates'),
                                        custom_area_id=_filtered_custom,  # postal_object.get('custom_area_id')
                                        )
                             ))

    return zips, custom_units, admin_unit


def match_administrative_unit(_admin_unit: list[Base], _postal_object, _zips: list[Base]):
    matched_administrative_unit = []
    if _postal_object.get('municipality'):
        matched_administrative_unit = [x for x in _admin_unit if
                                       x.fields.name.lower() == str(_postal_object.get('municipality')).lower()]
    if _postal_object.get('Municipality') is not None and not matched_administrative_unit:
        matched_administrative_unit = [x for x in _admin_unit if
                                       x.fields.name.lower() == str(_postal_object.get('Municipality')).split(' ')[
                                           0].lower()]
        if not matched_administrative_unit:
            matched_administrative_unit = [x for x in _admin_unit if
                                           x.fields.name.lower() == str(_postal_object.get('Municipality')).split(' ')[
                                                                        0].lower()[:-1]]
    if _postal_object.get('City') is not None and not matched_administrative_unit:
        matched_administrative_unit = [x for x in _admin_unit if
                                       x.fields.name.lower() == str(_postal_object.get('City')).lower()]

    if not matched_administrative_unit:
        matched_custom_admin = [x for x in _zips if x.fields.code[:3] == str(_postal_object.get('Postal_Code'))[:3]]

        if len(Counter(matches.fields.administrative_unit_id for matches in matched_custom_admin)) == 1:
            return matched_custom_admin[0].fields.administrative_unit_id
        else:
            return None

    if matched_administrative_unit:
        return matched_administrative_unit[0].pk
    else:
        return None


def add_administrative_unit(_admin_unit: list[Base], _postal_object, _admin_pk: int):
    _admin_name = None
    if municipality := _postal_object.get('municipality'):
        _admin_name = municipality.lower()
    elif municipality := _postal_object.get('Municipality'):
        _admin_name = municipality.split(' ')[0].lower()
    elif municipality := _postal_object.get('City'):
        _admin_name = municipality.lower()

    _admin_unit.append(Base(model='targeter.administrativeunit',
                            pk=_admin_pk,
                            fields=AdministrativeUnit(name=_admin_name)))
    return _admin_unit, _admin_pk


def match_custom_unit(_zips: list[Base], search: str):
    matched_custom_unit = [x for x in _zips if x.fields.code[:3] == search]
    if matched_custom_unit:
        return matched_custom_unit[0].fields.custom_area_id, matched_custom_unit[0].fields.country_id
    else:
        return None, None


def add_custom_unit(_custom_units: list[Base], _admin_unit: list[Base], _custom_pk: int, admin_id: int):
    matched_admin_units = [x for x in _admin_unit if x.pk == admin_id]
    if matched_admin_units:
        _admin_unit_name = matched_admin_units[0].fields.name
        _custom_units_name = _admin_unit_name
        matched_custom_units = [x for x in _custom_units if
                                " ".join(x.fields.name.split(' ')[:-1]).lower() == _admin_unit_name.lower()]

        if matched_custom_units:
            matched_custom_units_counter = [x.fields.name.split(' ')[-1] for x in matched_custom_units]
            matched_custom_units_are_type = [x.fields._area_type for x in matched_custom_units]
            matched_custom_units_coastal = [x.fields.coastal for x in matched_custom_units]

            _custom_units_name = _admin_unit_name + ' ' + str(int(max(matched_custom_units_counter)) + 1)

        _custom_units.append(Base(model='targeter.customarea',
                                  pk=_custom_pk,
                                  fields=CustomArea(name=_custom_units_name,
                                                    coastal=mode(matched_custom_units_coastal),
                                                    _area_type=max(matched_custom_units_are_type),
                                                    country_id=matched_custom_units[0].fields.country_id)))

    # _custom_units_name = _postal_object.get('Postal_Code')
    return _custom_units, _custom_pk, matched_custom_units[0].fields.country_id


def create_data(data: json) -> list[Base]:
    result = []
    if data[0]['model'] == 'targeter.customarea':
        for i in range(len(data)):
            result.append(Base(model=data[i]['model'],
                               pk=data[i]['pk'],
                               fields=CustomArea(name=data[i]['fields'].get('name'),
                                                 coastal=data[i]['fields'].get('coastal'),
                                                 _area_type=data[i]['fields'].get('_area_type'),
                                                 country_id=data[i]['fields'].get('country_id'))
                               )
                          )
    elif data[0]['model'] == 'targeter.administrativeunit':
        for i in range(len(data)):
            result.append(Base(model=data[i]['model'],
                               pk=data[i]['pk'],
                               fields=AdministrativeUnit(name=data[i]['fields'].get('name'),
                                                         population=data[i]['fields'].get('population'),
                                                         area=data[i]['fields'].get('area'),
                                                         state_id=data[i]['fields'].get('state_id'),
                                                         _average_household_net_yearly_income=data[i]['fields'].get(
                                                             '_average_household_net_yearly_income'),
                                                         _average_home_size_m2=data[i]['fields'].get(
                                                             '_average_home_size_m2'),
                                                         _recreational_properties_count=data[i]['fields'].get(
                                                             '_recreational_properties_count'),
                                                         _average_price_per_m2=data[i]['fields'].get(
                                                             '_average_price_per_m2'))
                               )
                          )
    else:
        for i in range(len(data)):
            result.append(Base(model=data[i]['model'],
                               pk=data[i].get('pk'),
                               fields=Zip(administrative_unit_id=data[i]['fields'].get('administrative_unit_id'),
                                          code=data[i]['fields'].get('code'),
                                          country_id=data[i]['fields'].get('country_id'),
                                          google_maps_id=data[i]['fields'].get('google_maps_id'),
                                          coordinates=data[i]['fields'].get('coordinates'),
                                          custom_area_id=data[i]['fields'].get('custom_area_id'))
                               )
                          )

    return result


if __name__ == '__main__':
    zip_max = 22987
    administrative_unit_max = 1263
    custom_area_max = 8308

    # Load Zip data
    f = open('data/zips_sweden.json')
    zip_data = create_data(json.load(f))

    # Load AdministrativeUnit data
    f = open('data/administrative_units_sweden.json')
    admin_data = create_data(json.load(f))

    # Load AdministrativeUnit data
    f = open('data/custom_areas_sweden.json')
    custom_data = create_data(json.load(f))

    # Load new data
    f = open('data/new_zips_sweden.json')
    new_json = json.load(f)

    # Get modified lists
    new_zips, new_customunits, new_adminunits = modify_list(zip_data.copy(), custom_data.copy(), admin_data.copy(),
                                                            new_json.copy(), zip_max,
                                                            custom_area_max, administrative_unit_max)

    # Export data
    os.makedirs(os.path.dirname('output/'), exist_ok=True)

    custom_area_export = [asdict(x) for x in new_customunits]
    with open('output/new_custom_areas_sweden.json', 'w', encoding='utf-8') as f:
        json.dump(custom_area_export, f, indent=2)

    administration_unit_export = [asdict(x) for x in new_adminunits]
    with open('output/new_administrative_units_sweden.json', 'w', encoding='utf-8') as f:
        json.dump(administration_unit_export, f, indent=2)

    zip_export = [asdict(x) for x in new_zips]
    with open('output/new_zips_sweden.json', 'w', encoding='utf-8') as f:
        json.dump(zip_export, f, indent=2)

