import logging
import re

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from exception import InvalidTerm
from semester import Semester

logging.basicConfig(filename='debug.log', level=logging.DEBUG)

COURSE_TITLE_REGEX = r"(?P<t>\A.+) - \d{5} - (?P<s>[A-Z]{2,4}) (?P<c>[0-9A-Z]{4,5})"
NAME_REGEX = r"(?P<first>[^ ]+) (?P<middle>.+) (?P<last>[^ ]+)"
NAME_NO_MIDDLE_REGEX = r"(?P<first>[^ ]+) (?P<last>[^ ]+)"

with open('raw_data', 'r') as file:
    RAW_DATA = file.read()


def scrape_courses(year: str, semester: Semester) -> set:
    data = RAW_DATA.format(year=year, semester=semester)
    logging.debug(f"data = {data}")
    response = requests.post('https://sis-ssb-prod.uga.edu/PROD/bwckschd.p_get_crse_unsec',
                             data=data)

    if response.status_code != 200:
        _msg = f'{response.status_code} returned for {data}'
        logging.warning(_msg)
        return set()

    soup: BeautifulSoup = BeautifulSoup(response.text, 'html.parser')
    if soup.find(text='Not a valid term') is not None:
        raise InvalidTerm(f"{year}{semester} is not a valid term string")

    caption = soup.caption
    assert isinstance(caption, Tag)

    parent = caption.parent
    assert isinstance(parent, Tag)

    table = parent.find_all('tr', recursive=False)

    courses = set()
    for i in range(0, len(table) - 1, 2):
        title_tr, body_tr = table[i], table[i + 1]
        assert isinstance(title_tr, Tag)
        assert isinstance(body_tr, Tag)

        a = title_tr.find('a')
        assert isinstance(a, Tag)

        title_raw = a.text

        match = re.search(COURSE_TITLE_REGEX, title_raw)
        if match is None:
            _msg = f'match is None\n{title_raw}'
            return courses

        title, subject, course_no = match.group('t', 's', 'c')

        mailtos = body_tr.select('a[href^=mailto]')
        for mailto in mailtos:
            assert isinstance(mailto, Tag)
            instructor = mailto['target']
            assert isinstance(instructor, str)

            first = middle = last = ""
            match = re.search(NAME_REGEX, instructor)
            if match:
                first, middle, last = match.group('first', 'middle', 'last')
            else:
                match = re.search(NAME_NO_MIDDLE_REGEX, instructor)
                if not match:
                    _msg = f'Could not parse the fullname of: {instructor}'
                    logging.debug(_msg)
                    continue
                first, last = match.group('first', 'last')

            email = mailto['href'][7:]  # remove 'mailto:'
            courses.add((subject, course_no, title,
                        email, first, middle, last))
    return courses


if __name__ == '__main__':
    from semester import FALL, SPRING, SUMMER
    with open('2021SPRING', 'w') as file:
        file.write('subject,,course_no,,title,,email,,first,,middle,,last')
        for course in scrape_courses('2021', SPRING):
            file.write('\n' + ',,'.join(course))

    with open('2021SUMMER', 'w') as file:
        file.write('subject,,course_no,,title,,email,,first,,middle,,last')
        for course in scrape_courses('2021', SUMMER):
            file.write('\n' + ',,'.join(course))

    with open('2021FALL', 'w') as file:
        file.write('subject,,course_no,,title,,email,,first,,middle,,last')
        for course in scrape_courses('2021', FALL):
            file.write('\n' + ',,'.join(course))
