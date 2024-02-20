from datetime import datetime
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # used for explicit waiting time
from selenium.webdriver.firefox.options import Options as FirefoxOptions  # used for setting up --headless mode
import pickle  # used for cookie handling
import os  # used for file paths and such
import subprocess  # used for calling another process
import time

err_msg = 'FAILED TO RENEW SUBSCRIPTION - '
time_form_selector = 'form-control-static'
manage_server_selector = 'btn-success'
start_server_selector = 'btn-success'


def init_driver(headless=False):
    driver_path = os.path.join(os.getcwd(), 'geckodriver.exe')
    service = Service(executable_path=driver_path)
    options = FirefoxOptions()
    # if headless:
    #     options.add_argument('--headless')
    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    driver.get("https://scalacube.com")
    return driver


def check_cookies(driver):
    while True:
        # opening the cookies file and adding them to the driver
        with open("cookies.pkl", "rb") as cookies_file:
            cookies = pickle.load(cookies_file)
            for cookie in cookies:
                driver.add_cookie(cookie)

        # we refresh the page, to see if the cookies persisted (if they expired we won't have them anymore)
        driver.refresh()
        cookies = driver.get_cookies()
        # if the auth.user cookie is not available after refresh, it means that it expired
        auth_user_cookie = list(filter(lambda cookie: cookie['name'] == 'auth.user', cookies))
        if len(auth_user_cookie) == 0:
            # if it expired, we create new cookies and try again
            handle_cookie_creation(driver)
            continue
        else:
            # if the cookies are valid, it means we can return
            return


def handle_cookie_creation(driver):
    create_cookie_script = subprocess.Popen(['py', os.path.join(os.getcwd(), 'create_cookie_dump.py')])
    status_code = create_cookie_script.wait()
    if status_code == 1:
        driver.quit()
        raise Exception('Cookie creation script returned error')


def renew(driver):
    element = driver.find_element(By.CLASS_NAME, 'btn-primary')
    element.click()
    append_to_log_file('SUCCEEDED IN RENEWAL')
    time.sleep(10)



def check_time_for_renewal(driver):
    # there will be 3 elements in that form, and the date and time will be in the 3rd element
    form = driver.find_elements(By.CLASS_NAME, time_form_selector)
    # if it's not displayed, it means we have green light for renewal
    if not form[2].is_displayed():
        return

    while form[2].text == '' and form[2].is_displayed():
        # it might have a delay because it needs to fetch it from the scala cube server, so we let it try again after 0.2 secs
        time.sleep(0.2)
        form = driver.find_elements(By.CLASS_NAME, time_form_selector)
    # format the date to create a datetime object
    time_data = form[2].text.split(',')
    time_data = list(map(lambda data: data.strip(), time_data))
    time_data = ' '.join(time_data)  # it will look like this: 18:15 February 09 2024
    # we create the time object
    time_when_ok_to_renew_object = datetime.strptime(time_data, '%H:%M %B %d %Y')
    if datetime.now() < time_when_ok_to_renew_object:
        append_to_log_file(
            'Too early, wait until ' + datetime.strftime(time_when_ok_to_renew_object, '%d-%m-%Y, %H:%M:%S'))
    # we wait if the script tried earlier than needed
    while datetime.now() < time_when_ok_to_renew_object:
        time.sleep(0.5)


def open_server(driver):
    manage_server_button = driver.find_element(By.CLASS_NAME, manage_server_selector)
    manage_server_button.click()
    while manage_server_button is None:
        try:
            manage_server_button = driver.find_element(By.CLASS_NAME, manage_server_selector)
            if manage_server_button:
                break
        except NoSuchElementException as e:
            driver.refresh()
            continue

    start_server_button = driver.find_element(By.CLASS_NAME, start_server_selector)
    # we make sure that the server needs to be started
    if start_server_button is not None:
        start_server_button.click()
    else:
        return
    # after pressing start, it prompts us to confirm and press again
    turn_on_button = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'button.btn')))
    turn_on_button.click()
    append_to_log_file('SERVER STARTED')


def append_to_log_file(message=''):
    timestamp = datetime.now().strftime('%d-%m-%Y, %H:%M:%S.%f - ')
    with open('logs.txt', 'a') as log_file:
        log_file.write('\n' + timestamp + message)


def main():
    try:
        append_to_log_file('SCRIPT STARTED')
        # first we init the driver, then we check if we have the necessary cookies
        driver = init_driver(True)
        check_cookies(driver)

        # after cookie handling, we go to the renewal page
        url_to_access = 'https://scalacube.com/cp#/bill/node/3282553/testRenew'
        driver.get(url_to_access)
        # we make sure that the script is not trying to renew earlier than its supposed
        check_time_for_renewal(driver)
        renew(driver)
        # we go to the server managing page url
        driver.get(url_to_access[:-10])  # new url will be the old one without /testRenew

        # we open the server after renewal if needed
        open_server(driver)
    except Exception as e:
        append_to_log_file(err_msg + str(e))
        exit(1)

    append_to_log_file('SCRIPT FINISHED')
    driver.quit()


if __name__ == "__main__":
    main()
