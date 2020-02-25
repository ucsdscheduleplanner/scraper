from sqlalchemy import Column, String, Integer

from database.db_interface import Base

Registry = {}


def get_class_object(quarter):
    if quarter in Registry:
        return Registry[quarter]

    class ClassRow(Base):
        __tablename__: str = quarter

        id = Column(Integer, primary_key=True)
        course_id = Column(String)
        department = Column(String)
        course_num = Column(String)
        section_id = Column(String)
        section_type = Column(String)
        days = Column(String)
        times = Column(String)
        location = Column(String)
        room = Column(String)
        instructor = Column(String)
        description = Column(String)
        units = Column(String)

        def is_cancelled(self):
            return self.times == "Cancelled" or self.days == "Cancelled" or self.location == "Cancelled" \
                   or self.room == "Cancelled" or self.instructor == "Cancelled"

        def __repr__(self):
            params = ', '.join(f'{k}={v}' for k, v in self.asdict().items())
            return f"{self.__class__.__name__}({params})"

    Registry[quarter] = ClassRow
    return ClassRow
