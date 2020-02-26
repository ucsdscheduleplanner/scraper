from dictalchemy import DictableModel
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(cls=DictableModel)
