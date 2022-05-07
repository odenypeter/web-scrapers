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


site_url = "https://csgo.gamersclub.gg/"
bannered_users_url = "https://csgo.gamersclub.gg/banidos"
login_page_url = """
https://steamcommunity.com/openid/login?
openid.ns=http://specs.openid.net/auth/2.0
&openid.mode=checkid_setup
&openid.return_to=https://csgo.gamersclub.gg/auth/callback?
redirect=/&openid.realm=https://csgo.gamersclub.gg/
&openid.identity=http://specs.openid.net/auth/2.0/identifier_select
&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"""


# login page credentials
username = 'geminiheg'
password = 'Gamer@2022'
action = "https://steamcommunity.com/openid/login"


def initialize_selenium(use_wire=False):
    # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36
    options = webdriver.ChromeOptions()
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--incognito')
    options.add_argument("--window-size=1100,1000")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_argument('--headless')
    # driver = webdriver.Chrome("/Users/odenypeter/Desktop/pi", options=options)
    if use_wire:
        driver = wire_driver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver


def download_file(link):
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

    driver.find_element(By.ID, "steamAccountName").send_keys(username)
    driver.find_element(By.ID, "steamPassword").send_keys(password)
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
            # driver.execute_script("arguments[0].scrollIntoView(true);", download_btn)
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


def virtual_click(driver, click_object, UseRandom=True):
    try:
        size = click_object.size
    except StaleElementReferenceException:
        return False

    sizeList = list(size.values())
    height = int(sizeList[0]) - 1
    width = int(sizeList[1]) - 1
    if UseRandom == True:
        try:
            height_rand = random.randint(1, height)
        except ValueError:
            height_rand = 1
        try:
            width_rand = random.randint(1, width)
        except ValueError:
            width_rand = 1
    if UseRandom == False:
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


def get_match_details(web_driver):
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
    # launch login
    driver.get(login_page_url)

    driver.find_element(By.ID, "steamAccountName").send_keys(username)
    driver.find_element(By.ID, "steamPassword").send_keys(password)
    login_btn = driver.find_element(By.ID, "imageLogin")
    virtual_click(driver, login_btn)
    time.sleep(2)
    return driver


def scrap_data(driver):
    time.sleep(5)
    driver = login(driver)
    driver.get(bannered_users_url)

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
            for url in urls[:10]:
                driver.get(url)

                time.sleep(5)

                results = get_match_details(driver)
                if results:
                    result_data.append(results)
        print('result data::', json.dumps(result_data, indent=4))

def copy_data(result_data):
    rclone_drive = 'gdrive'

    for item in result_data:
        file_url = item.get('demo_url')
        ban_type = item.get('ban_type')
        count_type = item.get('count_type')
        steam_id = item.get('steam_id_64')

        file_extension = file_url.split('/').pop().split('.').pop()
        dest_file_name = f"/ GamerClub-Cheaters/{ban_type}/{count_type}/{steam_id}.dem.{file_extension}"

        util.copy_file_by_url(file_url, f"{rclone_drive}:{dest_file_name}")


# main_driver = initialize_selenium()
# scrap_data(main_driver)
# main_driver.close()

# copy files
rclone_location = '/Users/anne/.config/rclone/rclone.conf'
util = RcloneUtil(rclone_location)
result_data = [
    {
        "ban_type": "TOS",
        "steam_id_64": "76561198048279039",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2022-05-06__1440__1__15891474__de_vertigo__timealakzan__vs__timepuig.zip"
    },
    {
        "ban_type": "TOS",
        "steam_id_64": "76561198796352111",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2022-04-22__0240__1__15758966__de_mirage__timeperfumebond__vs__timefloking420.zip"
    },
    {
        "ban_type": "TOS",
        "steam_id_64": "76561199104932496",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2022-05-06__1416__1__15891349__de_mirage__timep3tt__vs__timetomasperosio.zip"
    },
    {
        "ban_type": "TOS",
        "steam_id_64": "76561199260618529",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2022-05-01__0243__1__15842162__de_inferno__timeclip1__vs__timexerekinha.zip"
    },
    {
        "ban_type": "VAC",
        "steam_id_64": "76561198411699300",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2021-10-09__1807__1__13732395__de_mirage__timetwitchtvheelfps__vs__timetulin.zip"
    },
    {
        "ban_type": "VAC",
        "steam_id_64": "76561198256677453",
        "count_type": "m",
        "demo_url": "https://prod-demo-parser-gc-demos.s3.amazonaws.com/2022-05-05__0144__1__15880848__de_overpass__timenripoll02__vs__timepresenchiprofessor.zip"
    }
]
copy_data(result_data) # we can copy per item instead

# print (util.get_files_from_remote('gdrive:'))