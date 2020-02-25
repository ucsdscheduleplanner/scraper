import os
import sqlite3

from selenium.webdriver.support.select import Select

from settings import DATABASE_PATH, DATABASE_DIR, DEPARTMENT_URL
from utils.scraper_util import get_browser


class DepartmentScraper:
    INFO_MAX_INDEX = 4

    def __init__(self, quarter):
        # Start up the browser
        self.browser = get_browser()
        self.quarter = quarter

        # Add an implicit wait so that the department options load
        self.browser.implicitly_wait(15)

        # Establish database connection
        os.makedirs(DATABASE_DIR, exist_ok=True)
        self.database = sqlite3.connect(DATABASE_PATH)
        self.database.row_factory = sqlite3.Row
        self.cursor = self.database.cursor()

    def create_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS DEPARTMENT')
        self.cursor.execute('CREATE TABLE IF NOT EXISTS DEPARTMENT (QUARTER TEXT, DEPT_CODE TEXT)')

    def scrape(self):
        print("Beginning department scraping.")
        self.create_table()

        print("Scraping departments for %s" % self.quarter)
        self.search()
        departments = self.get_departments()
        self.insert_departments(departments)
        print("Finished scraping departments for %s" % self.quarter)

        self.close()
        print("Finished department scraping.")

    def search(self):
        self.browser.get(DEPARTMENT_URL)
        select = Select(self.browser.find_element_by_id('selectedTerm'))
        select.select_by_value(self.quarter)

    def get_departments(self):
        ret = []
        departments = self.browser.find_element_by_id('selectedSubjects') \
            .find_elements_by_tag_name('option')
        for department in departments:
            department = department.text
            # Get first four elements
            department = department[:DepartmentScraper.INFO_MAX_INDEX]
            # Making sure department is in the correct format
            ret.append(self.normalize_department(department))

        return ret

    def insert_departments(self, departments):
        for department in departments:
            self.cursor.execute('INSERT INTO DEPARTMENT(QUARTER, DEPT_CODE) VALUES(?, ?)', (self.quarter, department))

    def normalize_department(self, department):
        return department.strip()

    def close(self):
        self.database.commit()
        self.database.close()
        self.browser.close()
