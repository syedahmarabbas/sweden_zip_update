from dataclasses import dataclass


@dataclass
class AdministrativeUnit:
    name: str = None
    population: int = None
    area: float = None
    state_id: str = None
    _average_household_net_yearly_income: int = None
    _average_home_size_m2: float = None
    _recreational_properties_count: int = None
    _average_price_per_m2: int = None


@dataclass
class CustomArea:
    name: str = None
    coastal: bool = None
    _area_type: int = None
    country_id: int = None


@dataclass
class Zip:
    administrative_unit_id: int = None
    code: str = None
    country_id: int = None
    google_maps_id: str = None
    coordinates: str = None
    custom_area_id: int = None


@dataclass
class Base:
    model: str = None
    pk: int = None
    fields: AdministrativeUnit or Zip = None
