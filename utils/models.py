from typing import Callable

from sqlalchemy import Column, String, Integer

from database.db_interface import Base


class Department(Base):
    __tablename__: str = "Departments"

    id: str
    id = Column(Integer, primary_key=True)

    quarter: str
    quarter = Column(String)

    dept_code: str
    dept_code = Column(String)

    def __repr__(self):
        params = ', '.join(f'{k}={v}' for k, v in self.asdict().items())
        return f"{self.__class__.__name__}({params})"


class ClassRow(Base):
    __tablename__: str = "ClassData"

    id: str
    id = Column(Integer, primary_key=True)

    quarter: str
    quarter = Column(String)

    course_id: str
    course_id = Column(String)

    department: str
    department = Column(String)

    course_num: str
    course_num = Column(String)

    section_id: str
    section_id = Column(String)

    section_type: str
    section_type = Column(String)

    days: str
    days = Column(String)

    times: str
    times = Column(String)

    location: str
    location = Column(String)

    room: str
    room = Column(String)

    instructor: str
    instructor = Column(String)

    description: str
    description = Column(String)

    units: str
    units = Column(String)

    def is_cancelled(self) -> bool:
        return self.times == "Cancelled" or self.days == "Cancelled" or self.location == "Cancelled" \
               or self.room == "Cancelled" or self.instructor == "Cancelled"

    def __repr__(self):
        params = ', '.join(f'{k}={v}' for k, v in self.asdict().items())
        return f"{self.__class__.__name__}({params})"

    asdict: Callable
