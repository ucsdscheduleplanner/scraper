from typing import List

from selenium.webdriver.support.select import Select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import DEPARTMENT_URL, SQLITE_STR
from utils.models import Department
from utils.scraper_util import get_browser


class DepartmentScraper:
    INFO_MAX_INDEX = 4

    def __init__(self, quarter):
        # Start up the browser
        self.browser = get_browser()
        self.quarter = quarter
        self.engine = create_engine(SQLITE_STR)
        self.session = sessionmaker(bind=self.engine)()

        # Add an implicit wait so that the department options load
        self.browser.implicitly_wait(15)

    def scrape(self):
        print("Beginning department scraping.")
        print("Scraping departments for %s" % self.quarter)

        self.search()
        self.create_tables()
        departments = self.get_departments()
        self.session.add_all(departments)
        self.close()

        print("Finished scraping departments for %s" % self.quarter)
        print("Finished department scraping.")

    def create_tables(self):
        Department.__table__.create(self.engine, checkfirst=True)
        self.session.query(Department).filter(Department.quarter == self.quarter).delete()

    def search(self):
        self.browser.get(DEPARTMENT_URL)
        select = Select(self.browser.find_element_by_id('selectedTerm'))
        select.select_by_value(self.quarter)

    def get_departments(self) -> List[Department]:
        ret: List[Department]
        ret = []
        departments = self.browser.find_element_by_id('selectedSubjects') \
            .find_elements_by_tag_name('option')
        for department in departments:
            department = department.text
            # Get first four characters
            department = department[:DepartmentScraper.INFO_MAX_INDEX]
            # Making sure department is in the correct format
            ret.append(self.normalize_department(department))

        return ret

    def normalize_department(self, department) -> Department:
        return Department(quarter=self.quarter, dept_code=department.strip())

    def close(self):
        self.session.commit()
        self.browser.close()
