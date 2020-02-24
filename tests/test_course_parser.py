import os

from sd_parser.course_parser import CourseParser, ClassRow
from tests.test_settings import RESOURCE_DIR


def test_basic_page():
    parser = CourseParser()
    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_CSE.html"), "CSE")

    cse100 = [c for c in classes if c.course_num == "100" and c.section_type == "DI"]
    # There are two CSE 100 classes
    assert len(cse100) == 2

    first, second = cse100[0], cse100[1]
    assert isinstance(first, ClassRow) and isinstance(second, ClassRow)
    assert first.section_id is None and second.section_id is None

    assert second.course_id == "995097"

    assert first.department == "CSE"
    assert first.course_id == "995095"
    assert first.course_num == "100"
    assert first.instructor == "Cao, Yingjun"
    assert first.section_type == "DI"
    assert first.days == "M"
    assert first.times == "5:00p-5:50p"
    assert first.location == "SOLIS"
    assert first.room == "107"


def test_page_all_same_department():
    parser = CourseParser()
    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_CSE.html"), "CSE")
    cse_classes = [c for c in classes if c.department == "CSE"]

    assert len(classes) == len(cse_classes)


def test_phys_page_no_course_num():
    parser = CourseParser()
    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_PHYS.html"), "PHYS")

    phys_le = [c for c in classes if c.course_num == "2A" and c.section_type == "LE"]
    # There are two CSE 100 classes
    assert len(phys_le) == 2

    first, second = phys_le[0], phys_le[1]
    assert isinstance(first, ClassRow) and isinstance(second, ClassRow)
    assert first.course_id is '' and second.course_id is ''

    assert first.days == "MWF"
    assert first.times == "12:00p-12:50p"

    assert second.days == "F"
    assert second.times == "8:00a-8:50a"


def test_phys_page_many_discussions():
    parser = CourseParser()
    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_PHYS.html"), "PHYS")

    phys_di = [c for c in classes if c.course_num == "2A" and c.section_type == "DI"]
    # There are two CSE 100 classes
    assert len(phys_di) == 12

    for i in range(12):
        cls = phys_di[i]
        assert cls.course_id == "9934{:02d}".format(i + 9)
        assert cls.units == "4"


def test_units_assigned():
    parser = CourseParser()
    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_PHYS.html"), "PHYS")
    phys = [c for c in classes if c.course_num == "1C"]

    for cls in phys:
        assert cls.units == "3"

    classes = parser.parse_file(os.path.join(RESOURCE_DIR, "WI20_AIP.html"), "AIP")
    aip = [c for c in classes if c.course_num == "197"]

    for cls in aip:
        assert cls.units == "2/12 by 2"
