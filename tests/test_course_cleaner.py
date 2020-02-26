import os
from typing import List, Dict

from sd_cleaner.course_cleaner import CourseCleaner
from sd_parser.course_parser import CourseParser
from tests.test_settings import TEST_RESOURCE_DIR
from utils.models import ClassRow

quarter = "TEST20"
parser = CourseParser(quarter)
cleaner = CourseCleaner(quarter)


def test_normal_clean():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "WI20_CSE.html"), "CSE")
    classes = cleaner.process_department("CSE", classes)
    cse = set([c.course_num for c in classes])
    assert len(cse) == 7


def test_normal_clean_data():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "WI20_CSE.html"), "CSE")
    classes = cleaner.process_department("CSE", classes)
    cse = [c for c in classes if c.course_num == "100"]
    check_classes(
        [{"days": "M", "section_type": "LE", "instructor": "Cao, Yingjun"}, {"days": "M", "section_type": "DI"},
         {"days": "W", "section_type": "LE"}, {"days": "F", "section_type": "LE"}], cse)


def test_continue_with_bad_date_format():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "SP20_CSE_bad_date_format.html"), "CSE")

    classes = cleaner.process_department("CSE", classes)
    assert len([c for c in classes if c.course_num == "276D"]) != 0


def test_clean_physics():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "WI20_PHYS.html"), "PHYS")

    classes = cleaner.process_department("PHYS", classes)

    phys = [c for c in classes if c.course_num == "2A" and c.section_id == "PHYS2A$0"]
    assert len(phys) != 0

    check_classes([{"days": "M"}, {"days": "W", "times": "12:00-12:50"}, {"days": "F", "times": "12:00-12:50"},
                   {"days": "F", "times": "08:00-08:50"}, {"days": "Tu"}], phys)


def test_clean_physics_final():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "SP20_PHYS.html"), "PHYS")

    classes = cleaner.process_department("PHYS", classes)

    phys = [c for c in classes if c.course_num == "1A"]
    assert len(phys) == 4

    check_classes([{"course_id": "4733", "days": "W", "times": "15:00-17:59"}], phys)


def test_cancelled_classes():
    classes = parser.parse_file(os.path.join(TEST_RESOURCE_DIR, "SP20_MUS_cancelled.html"), "MUS")

    classes = cleaner.process_department("MUS", classes)

    mus = [c for c in classes if c.course_num == "107"]
    assert len(mus) == 0


def check_classes(match_data: List[Dict[str, str]], classes: List[ClassRow]):
    ret = True
    for d in match_data:
        found = False
        for cls in classes:
            match = len(d.keys()) != 0
            for key in d.keys():
                if hasattr(cls, key) and not getattr(cls, key) == d[key]:
                    match = False
            if match:
                found = True
                break
        ret = ret and found
        if not found:
            print(classes)
    assert ret is True
