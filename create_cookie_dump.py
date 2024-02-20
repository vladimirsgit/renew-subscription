from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from main import init_driver
import config
import pickle
import ctypes
import sys  # used for returning exit codes


def accept_cookies(driver):
    allow_cookies = driver.find_element(By.ID, 'CybotCookiebotDialogBodyButtonAccept')
    allow_cookies.click()


def save_cookies_file(driver):
    with open('cookies.pkl', 'wb') as cookies_file:
        pickle.dump(driver.get_cookies(), cookies_file)


def handle_login(driver):
    to_login_form_button = driver.find_element(By.LINK_TEXT, 'Login')
    to_login_form_button.click()

    form_fields = driver.find_elements(By.CLASS_NAME, 'form-control')
    form_fields[0].send_keys(config.USERNAME)
    form_fields[1].send_keys(config.PASSWORD)

    press_login = driver.find_element(By.CLASS_NAME, 'btn-primary')
    press_login.click()


def main():
    # create a gui to announce the user that the cookies expired and he's needed to take action
    my_response = ctypes.windll.user32.MessageBoxW(0,
                                                   'Hello! Unfortunately, you need to enter your mc server credentials again. A text file with your credentials will open if you press ok.',
                                                   'ACTION NEEDED', 1)
    if my_response != 1:
        sys.exit(1)

    driver = init_driver()

    try:
        accept_cookies(driver)
    except:
        ctypes.windll.user32.MessageBoxW(0, 'Error when trying to accept cookies', 'Rerun manually', 0)
        sys.exit(1)

    try:
        handle_login(driver)
    except:
        ctypes.windll.user32.MessageBoxW(0, 'Error when trying to handle login', 'Rerun manually', 0)
        sys.exit(1)

    try:
        continue_button = WebDriverWait(driver, 500).until(EC.visibility_of_element_located((By.ID, 'continue')))
        save_cookies_file(driver)
    except:
        ctypes.windll.user32.MessageBoxW(0, 'Error when trying to save cookies/continue button not found', 'Rerun manually', 0)
        sys.exit(1)
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
