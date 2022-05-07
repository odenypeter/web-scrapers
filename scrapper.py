import random
import json
import datetime
import time
from dateutil.relativedelta import relativedelta

from seleniumwire import webdriver as wire_driver
from seleniumwire.utils import decode

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    MoveTargetOutOfBoundsException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rclone_util import RcloneUtil

# page urls
SITE_URL = "https://csgo.gamersclub.gg/"
BANNED_USERS_URL = "https://csgo.gamersclub.gg/banidos"
LOGIN_PAGE_URL = """
https://steamcommunity.com/openid/login?
openid.ns=http://specs.openid.net/auth/2.0
&openid.mode=checkid_setup
&openid.return_to=https://csgo.gamersclub.gg/auth/callback?
redirect=/&openid.realm=https://csgo.gamersclub.gg/
&openid.identity=http://specs.openid.net/auth/2.0/identifier_select
&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"""


# login page credentials
USERNAME = 'username'
PASSWORD = 'password'

# copy files
RCLONE_CONF_LOCATION = 'PATH_TO_RCLONE_CONFIG'
RCLONE_REMOTE_FOLDER = 'RCLONE_REMOTE_FOLDER'

# initialize rclone util
rclone_util = RcloneUtil(RCLONE_CONF_LOCATION)


def initialize_selenium(use_wire=False):
    """
    set selenium instance
    :param use_wire: True if using seleniumwire
    :return: driver instance
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1100,1000")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--headless')
    if use_wire:
        driver = wire_driver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def download_file(link):
    """
    download demo file
    :param link:
    :return:
    """
    url_parts = link.split('/')
    new_link = f'{url_parts[-3]}/{url_parts[-2]}/{url_parts[-1]}'
    updated_login_page_url = f"""
https://steamcommunity.com/openid/login?
openid.ns=http://specs.openid.net/auth/2.0
&openid.mode=checkid_setup
&openid.return_to=https://csgo.gamersclub.gg/auth/callback?
redirect=/{new_link}&openid.realm=https://csgo.gamersclub.gg/
&openid.identity=http://specs.openid.net/auth/2.0/identifier_select
&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"""

    file_data = None
    # launch login
    driver = initialize_selenium(True)
    driver.get(updated_login_page_url)
    time.sleep(5)

    driver.find_element(By.ID, "steamAccountName").send_keys(USERNAME)
    driver.find_element(By.ID, "steamPassword").send_keys(PASSWORD)
    btn = driver.find_element(By.ID, "imageLogin")
    virtual_click(driver, btn)

    time.sleep(2)

    try:
        error_404 = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div[2]/h1'))
        )

        if error_404 and error_404.text.strip() == '404':
            return None
        pass
    except (TimeoutException, NoSuchElementException):
        pass

    try:
        modal_close = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ChangelogModal__close'))
        )

        if modal_close:
            modal_close.click()
    except TimeoutException:
        pass

    time.sleep(3)
    try:
        download_btn = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[2]/div[12]/div/div/section/div[3]/div/div[2]/div[2]/div[4]/a')
            )
        )

        if download_btn:
            download_btn.click()
            time.sleep(7)
            for request in driver.requests:
                response = request.response
                if request.response:
                    if 'demoDownload' in request.url:
                        body = decode(response.body, response.headers.get('Content-Encoding', 'identity'))
                        if body:
                            resp_str = body.decode('utf-8')
                            file_data = json.loads(resp_str)
    except TimeoutException:
        pass

    driver.quit()
    return file_data


def virtual_click(driver, click_object, use_random=True):
    """
    emulate user click of login btn
    :param driver:
    :param click_object:
    :param use_random:
    :return:
    """
    try:
        size = click_object.size
    except StaleElementReferenceException:
        return False

    size_list = list(size.values())
    height = int(size_list[0]) - 1
    width = int(size_list[1]) - 1
    if use_random:
        try:
            height_rand = random.randint(1, height)
        except ValueError:
            height_rand = 1
        try:
            width_rand = random.randint(1, width)
        except ValueError:
            width_rand = 1
    if not use_random:
        height_rand = height
        width_rand = width
    action = webdriver.common.action_chains.ActionChains(driver)
    try:
        action.move_to_element_with_offset(click_object, width_rand, height_rand)
    except StaleElementReferenceException:
        return False
    action.click()
    try:
        action.perform()
    except MoveTargetOutOfBoundsException:
        print("MoveTargetOutOfBoundsException with action.perform()")
        return False
    except StaleElementReferenceException:
        print("StaleElementReferenceException with action.perform()")
        return False
    return True


def get_ban_period_in_years(date_from, date_to) -> int:
    """
    get user banned period in years
    :param date_from:
    :param date_to:
    :return:
    """
    if date_from and date_to:
        date_from_str = date_from.split(' ')[0].split('/')
        date_to_str = date_to.split(' ')[0].split('/')
        from_datetime = datetime.datetime(
            int(date_from_str[2]),
            int(date_from_str[1]),
            int(date_from_str[0])
        )
        to_datetime = datetime.datetime(
            int(date_to_str[2]),
            int(date_to_str[1]),
            int(date_to_str[0])
        )
        difference = relativedelta(to_datetime, from_datetime)
        return difference.years


def get_pages(driver):
    """
    Get all banned users pages
    :param driver:
    :return:
    """
    pages = (
        driver.find_element(By.CLASS_NAME, 'content-pagination')
        .find_elements(By.TAG_NAME, 'a')
    )
    page_links = []
    for item in pages:
        page_links.append(
            item.get_attribute('href')
        )
    return page_links


def get_match_details(web_driver):
    """
    extract match details
    :param web_driver:
    :return:
    """
    # get latest match
    try:
        latest_match_link = web_driver.find_element(By.CLASS_NAME, 'StatsBoxMatch__SeeMatch').get_attribute('href')
    except (TypeError, NoSuchElementException):
        latest_match_link = None

    if latest_match_link:
        response_data = dict()

        # get match count
        match_summary_card = web_driver.find_element(By.CLASS_NAME, 'gc-card-history-content')
        match_count_str = match_summary_card.find_element(By.TAG_NAME, 'p').text

        if match_count_str:
            match_count = int(
                match_count_str.lower()
                .replace('matches', '')
                .replace('match', '')
                .strip()
            )

            if match_count:
                # get ban types
                try:
                    ban_type_cont = web_driver.find_element(
                        By.XPATH,
                        '/html/body/div[2]/div[12]/div/div/div[12]/div[2]/div[2]/div/div[1]/div'
                    )
                except NoSuchElementException:
                    ban_type_cont = web_driver.find_element(
                        By.XPATH,
                        '/html/body/div[2]/div[12]/div/div/div[13]/div[2]/div[2]/div/div[1]/div'
                    )

                if ban_type_cont:
                    ban_type = ban_type_cont.find_element(By.TAG_NAME, 'strong').text
                    if ban_type.strip().upper() == 'MEMBER BANNED AT GAMERS CLUB':
                        ban_dates = ban_type_cont.find_elements(By.TAG_NAME, 'strong')
                        try:
                            date_from = ban_dates[1].text.strip()
                            date_to = ban_dates[2].text.strip()

                            difference = get_ban_period_in_years(date_from, date_to)

                            if difference:
                                response_data.update(dict(ban_type='TOS'))

                        except IndexError:
                            pass
                    else:
                        response_data.update(dict(ban_type=ban_type.strip()))

                    if 'ban_type' in response_data:
                        # get steam id 64
                        profile_cont = web_driver.find_element(By.CLASS_NAME, 'gc-list')
                        if profile_cont:
                            steam_id_64 = (
                                profile_cont.find_elements(By.TAG_NAME, 'li')[3]
                                .find_element(By.TAG_NAME, 'p').text
                            )
                            response_data.update(dict(steam_id_64=steam_id_64.strip()))
                        response_data.update(dict(count_type='m' if match_count > 1 else 's'))
                        game_demo = download_file(latest_match_link)
                        if game_demo:
                            response_data.update(dict(demo_url=game_demo.get('demo')))
                            return response_data

    return None


def login(driver):
    """
    login
    :param driver:
    :return:
    """
    # launch login
    driver.get(LOGIN_PAGE_URL)

    driver.find_element(By.ID, "steamAccountName").send_keys(USERNAME)
    driver.find_element(By.ID, "steamPassword").send_keys(PASSWORD)
    login_btn = driver.find_element(By.ID, "imageLogin")
    virtual_click(driver, login_btn)
    time.sleep(2)
    return driver


def scrap_data_by_page(driver):
    """
    scrap banned user data per page
    :param driver:
    :return:
    """
    table = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'ban-table'))
    )

    table_items = (
        table
        .find_element(By.TAG_NAME, 'tbody')
        .find_elements(By.TAG_NAME,'tr')
    )

    if table_items:
        urls = []

        for element in table_items:
            table_data = element.find_elements(By.TAG_NAME, 'td')
            profile_link = (
                table_data[0]
                .find_element(By.TAG_NAME, 'a')
                .get_attribute('href')
            )
            urls.append(profile_link)
        result_data = []
        if urls:
            for url in urls:
                driver.get(url)

                time.sleep(5)

                results = get_match_details(driver)
                if results:
                    result_data.append(results)
        return result_data
    return None


def scrap_data(driver, all_pages=False):
    """
    entry method
    :param driver:
    :param all_pages:
    :return:
    """
    time.sleep(5)
    driver = login(driver)
    driver.get(BANNED_USERS_URL)
    all_data = []
    if all_pages:
        pages = get_pages(driver)
    else:
        pages = None

    data = scrap_data_by_page(driver)
    if data:
        all_data += data

    if pages:
        # get pages
        if pages:
            for page in pages:
                driver.get(page)
                data = scrap_data_by_page(driver)
                all_data += data

    if all_data:
        copy_data(all_data)


def copy_data(data):
    """
    copy data with RClone
    :param data:
    :return:
    """
    existing_files = []
    for ban in ['TOS', 'VAC']:
        for count in ['m', 's']:
            files = rclone_util.get_files_from_remote(f'{RCLONE_REMOTE_FOLDER}/GamerClub-Cheaters/{ban}/{count}/')
            if files:
                existing_files += files

    for item in data:

        # get existing files
        file_url = item.get('demo_url')
        ban_type = item.get('ban_type')
        count_type = item.get('count_type')
        steam_id = item.get('steam_id_64')

        # check if file exists:
        file_exists = any(steam_id in item for item in existing_files)
        if not file_exists:
            file_extension = file_url.split('.').pop()
            dest_file_name = f'/GamerClub-Cheaters/{ban_type}/{count_type}/{steam_id}.dem.{file_extension}'
            rclone_util.copy_file_by_url(file_url, f'{RCLONE_REMOTE_FOLDER}{dest_file_name}')


main_driver = initialize_selenium()
# pass false to disable scrapping of all pages
scrap_data(main_driver, True)
main_driver.close()


