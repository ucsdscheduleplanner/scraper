import copy
import itertools
import sqlite3
from itertools import groupby
from typing import List, Dict

from sd_parser.course_parser import ClassRow
from settings import DATABASE_PATH, QUARTERS_TO_SCRAPE
from utils.timeutils import TimeIntervalCollection

"""
Takes input from CourseParser
"""


class CourseCleaner:
    def __init__(self):
        self.database = sqlite3.connect(DATABASE_PATH)
        # will set the return value to a dict
        self.database.row_factory = sqlite3.Row
        self.cursor = self.database.cursor()

    def clean(self, data: Dict[str, List[ClassRow]]):
        print('Begin cleaning database.')
        self.setup_tables()
        self._clean(data)
        self.close()
        print('Finished cleaning database.')

    def setup_tables(self):
        for quarter in QUARTERS_TO_SCRAPE:
            self.cursor.execute("DROP TABLE IF EXISTS {}".format(quarter))
            self.cursor.execute("CREATE TABLE {}"
                                "(DEPARTMENT TEXT, COURSE_NUM TEXT, SECTION_ID TEXT, COURSE_ID TEXT,"
                                "SECTION_TYPE TEXT, DAYS TEXT, TIME TEXT, LOCATION TEXT, ROOM TEXT, "
                                "INSTRUCTOR TEXT, DESCRIPTION TEXT, UNITS TEXT, FOREIGN KEY (DEPARTMENT)"
                                "REFERENCES DEPARTMENT(DEPT_CODE))".format(quarter))

    def _clean(self, data: Dict[str, List[ClassRow]]):
        # getting list of departments
        self.cursor.execute("SELECT * FROM DEPARTMENT")
        departments = [i["DEPT_CODE"] for i in self.cursor.fetchall()]

        # handle each department and quarter separately
        for quarter in QUARTERS_TO_SCRAPE:
            quarter_data = data[quarter]
            print("Cleaning quarter {}".format(quarter))
            for department in departments:
                classes = self.process_department(department, quarter_data)
                self.save_classes(classes, quarter)

    """
    Will store in format with partitions for the courseNums in the same format : i.e CSE3$0 means section 0 of CSE3.
    """

    def process_department(self, department, data: List[ClassRow]) -> List[ClassRow]:
        visible_classes = [row for row in data if row.department == department]
        # doing this so fast_ptr knows where to stop
        visible_classes.append(ClassRow(course_num=None))

        # blank class list for ones to insert
        classes_to_insert = []

        fast_ptr, slow_ptr = 0, 0
        # course num will be set later
        course_num = None
        section_count = {}
        while fast_ptr < len(visible_classes):
            slow_class = visible_classes[slow_ptr]
            fast_class = visible_classes[fast_ptr]

            if slow_class.course_num:
                slow_ptr += 1

            if fast_class.course_num:
                course_num = fast_class.course_num

            # We know we have hit the end of a section
            if not fast_class.course_num and slow_ptr != fast_ptr:
                classes_to_insert.extend(
                    # we want slow_ptr + 1 and fast_ptr to be the lower and upper bounds
                    self.process_current_course(visible_classes[slow_ptr + 1: fast_ptr],
                                                section_count,
                                                department,
                                                course_num))

                slow_ptr = fast_ptr
            fast_ptr += 1
        return classes_to_insert

    def save_classes(self, classes_to_insert: List[ClassRow], quarter):
        sql_str = """\
                      INSERT INTO {}(DEPARTMENT, COURSE_NUM, SECTION_ID, \
                      COURSE_ID, SECTION_TYPE, DAYS, TIME, LOCATION, ROOM, INSTRUCTOR, DESCRIPTION, UNITS)  \
                      VALUES 
                      (:department, 
                      :course_num, 
                      :section_id, 
                      :course_id,
                      :section_type,
                      :days,
                      :times, 
                      :location,
                      :room,
                      :instructor,
                      :description,
                      :units) \
                    """.format(quarter)
        for c in classes_to_insert:
            self.cursor.execute(sql_str, vars(c))

    def sanitize_classes(self, classes: List[ClassRow]):
        return [c for c in classes if not c.is_cancelled()]

    def process_current_course(self, classes: List[ClassRow], section_count: Dict[str, int], department, course_num):
        classes = self.sanitize_classes(classes)

        ret: List[ClassRow]
        ret = []

        class_sections: List[List[ClassRow]]
        class_sections = []

        # Classes that must be duplicated across all sections
        classes_to_replicate: List[ClassRow]
        classes_to_replicate = [c for c in classes if not c.course_id]

        # Unique classes which delimit section
        classes_to_add: List[ClassRow]
        classes_to_add = [c for c in classes if c not in classes_to_replicate]

        # can only be one unique copy of var$Class per Class because of COURSE_ID uniqueness
        for Class in classes_to_add:
            type_groups = groupby(classes_to_replicate, lambda x: x.section_type)

            cur_class_sections = [[Class]]
            # groups of replicas based on types
            for key, type_group in type_groups:
                type_group: List[ClassRow]
                type_group = list(type_group)

                # making temp section for setting later
                temp_sections = []
                # adding cartesian product to temp
                # cur section is a list
                for cur_section in cur_class_sections:
                    # replica is a section (collection of classes, used replica here for reference to Tales of the Abyss)
                    replica: List[ClassRow]
                    replica = cur_section.copy()

                    # class with type is a class
                    for class_with_type in type_group:
                        new_class = copy.copy(class_with_type)
                        # always guaranteed to have at least one element in the list
                        new_class.course_id = replica[0].course_id
                        # handle the passing of variable information through rows here
                        if not replica[0].instructor and new_class.instructor:
                            replica[0].instructor = new_class.instructor
                        elif not new_class.instructor:
                            new_class.course_id = replica[0].instructor

                        replica.append(new_class)
                    temp_sections.append(replica)
                # setting current to temp
                cur_class_sections = temp_sections
            class_sections.extend(cur_class_sections)

        # now we are going to set ids based on class_section
        # also going to split courseNums into their subclasses
        for class_section in class_sections:
            if department not in section_count:
                section_count[department] = {}
            if course_num not in section_count[department]:
                section_count[department][course_num] = 0
            id = department + course_num
            for section in class_section:
                # setting id based on sectionn
                section.section_id = id + "$" + \
                                     str(section_count[department][course_num])
                subsections = self.split_into_subsections(section)

                # only add if we could create the subsections
                ret.extend(subsections)
            # incrementing to signify going to next section
            section_count[department][course_num] += 1
        return ret

    def split_into_subsections(self, section: ClassRow):
        """
        Takes in a section and splits it into its subsections for easy insertion into rdbms table.

        :param section: the section to split
        :return returns a list of subsections
        """

        ret = []
        # TimeIntervalCollection functions will parse days and times correctly into lists
        days = TimeIntervalCollection.get_days(section.days)
        # times is a list of TimeInterval objects, want to convert to string
        times = TimeIntervalCollection.get_times(section)
        for i in range(0, len(times)):
            # both datetime objects
            start_time = times[i].start_time
            end_time = times[i].end_time

            start_time_str = start_time.strftime('%H:%M')
            end_time_str = end_time.strftime('%H:%M')
            # combining into one string
            time_str = "{}-{}".format(start_time_str, end_time_str)
            times[i] = time_str

        # If it had no days or times just return the original
        if not days or not times:
            return [section]

        # make each day go with a time
        day_time_pairs = list(itertools.zip_longest(days, times,
                                                    fillvalue=times[len(times) - 1] if len(days) > len(times) else days[
                                                        len(days) - 1]))
        for entry in day_time_pairs:
            # each subsection has mostly the same info as the section
            subsection = copy.copy(section)
            subsection.days = entry[0]
            subsection.times = entry[1]
            ret.append(subsection)
        return ret

    def close(self):
        self.database.commit()
        self.database.execute("VACUUM")
        self.database.close()

# Cleaner().clean()
