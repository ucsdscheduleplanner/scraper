import os
import re
import sqlite3
from typing import List

import bs4

from settings import COURSES_HTML_PATH, DATABASE_PATH
from utils.models import ClassRow


class CourseParser:
    description: str
    current_class: str
    quarter: str

    def __init__(self, quarter):
        # initializing database
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.connection.cursor()

        self.quarter = quarter
        self.current_class, self.description, self.units = '', '', ''

    def parse(self) -> List[ClassRow]:
        print('Beginning course parsing...')

        try:
            print("Parsing %s" % self.quarter)
            return self.parse_data()
        finally:
            print('Finished course parsing.')

    def parse_data(self) -> List[ClassRow]:
        class_store = []
        quarter_path = os.path.join(COURSES_HTML_PATH, self.quarter)
        departments = [file.name for file in os.scandir(quarter_path) if file.is_dir()]
        departments.sort()

        for department in departments:
            print("[Courses] Parsing department %s." % department)
            department_path = os.path.join(quarter_path, department)
            files = os.listdir(department_path)

            # just to sort based on number
            files.sort(key=lambda x: int(re.findall('[0-9]+', x)[0]))
            for file in files:
                class_store.extend(self.parse_file(os.path.join(department_path, file), department))

        return class_store

    def parse_file(self, filepath, department) -> List[ClassRow]:
        ret = []
        with open(filepath) as html:
            # Use lxml for parsing
            soup = bs4.BeautifulSoup(html, 'lxml')
            # Look for table rows
            rows = soup.find_all(name='tr')
            for row in rows:
                ret.extend(self.parse_row(department, row))
        return ret

    """
    Will get info from the HTML and store it into a format that can be manipulated easily. 
    Then it will validate the information and make sure that it is in a usable format.
    """

    def parse_row(self, department, row):
        ret: List[ClassRow]
        ret = []
        course_num = row.find_all(name='td', attrs={'class': 'crsheader'})

        if course_num:
            self.current_class = course_num[1].text
            self.description = course_num[2].text.strip().replace('\n', '').replace('\t', '')

            # Getting units from description, removing from description
            unit_match = re.search(r'(.*)\((.+)Units\)', self.description)
            if unit_match is not None:
                self.description = unit_match.group(1).strip()
                self.units = unit_match.group(2).strip()
            else:
                self.units = "N/A"
            # num slots on the top header
            if len(course_num) == 4:
                ret.append(ClassRow(quarter=self.quarter, department=department,
                                        course_num=None, course_id="START/END OF CLASS"))

        info = row.find_all(name='td',
                            attrs={'class': 'brdr'})

        if info and len(info) > 5:
            copy_dict = {}
            counter = 0

            for i in info:
                if 'colspan' in i.attrs:
                    for j in range(0, int(i.attrs['colspan'])):
                        copy_dict[counter] = i.text.strip()
                        counter += 1
                else:
                    copy_dict[counter] = i.text.strip()
                    counter += 1

            course_num = self.current_class
            course_id = copy_dict[2]
            section_type = copy_dict[3]
            days = copy_dict[5]
            times = copy_dict[6]
            location = copy_dict[7]
            room = copy_dict[8]
            instructor = copy_dict[9]

            info = ClassRow(
                quarter=self.quarter,
                course_id=course_id,
                department=department,
                course_num=course_num,
                section_type=section_type,
                days=days,
                times=times,
                location=location,
                room=room,
                instructor=instructor,
                description=self.description,
                units=self.units
            )

            ret.append(info)
        return ret
