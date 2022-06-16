from dataclasses import dataclass
from dacite import from_dict


user = from_dict(data_class=User, data=data)

assert user == User(name='John', age=30, is_active=True)