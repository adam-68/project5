from threading import Thread
from queue import Queue
from selenium import webdriver
import os
import time
import json


def get_chromedriver(use_proxy=False, user_agent=None):
    path = os.path.dirname(os.path.abspath(__file__))
    chrome_options = webdriver.ChromeOptions()
    if use_proxy:
        chrome_options.add_extension("proxy_extension.zip")
    if user_agent:
        chrome_options.add_argument('--user-agent=%s' % user_agent)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']);
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(
        os.path.join(path, 'chromedriver'),
        options=chrome_options)
    driver.get("https://google.com/")
    return driver


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class QueueProxy(Queue, metaclass=Singleton):
    pass


class QueueCookie(Queue, metaclass=Singleton):
    pass


class CookieInput(object):
    def __init__(self, cookie):
        self.queue = QueueCookie()
        self.cookie = cookie

    def run(self):
        self.queue.put(self.cookie)


class ProxyInput(object):

    def __init__(self, proxy):
        self.queue = QueueProxy()
        self.proxy = proxy

    def run(self):
        self.queue.put(self.proxy)


class CookieInterpreter(object):

    def __init__(self):
        self.queue = QueueCookie()

    def get_cookie(self):
        return self.queue.get()

    def is_empty(self):
        return self.queue.empty()


class ProxyInterpreter(object):

    def __init__(self):
        self.queue = QueueProxy()

    def get_proxy(self):
        return self.queue.get()

    def is_empty(self):
        return self.queue.empty()


def cookie_main(queue):
    driver = get_chromedriver(use_proxy=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                                                         " (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36")
    while not queue.is_empty():
        curr_proxy = queue.get_proxy()

        driver.execute_script(f"window.postMessage({{type: 'f', params: '{curr_proxy}'}}, '*');")
        driver.get("https://sklepkoszykarza.pl/")
        cookies_loaded = False
        while not cookies_loaded:
            if "https://sklepkoszykarza.pl/" == driver.current_url:
                time.sleep(1)
            elif "hcaptcha" in str(driver.page_source):
                while "hcaptcha" in driver.page_source:
                    time.sleep(1)
                cookies_loaded = True
            else:
                cookies_loaded = True

        curr_cookies = driver.get_cookies()
        for c in curr_cookies:
            if c["name"] == "cf_clearance":
                add_cookie = CookieInput({curr_proxy: c['value']})
                add_cookie.run()
        driver.delete_all_cookies()
        time.sleep(1)
    driver.quit()


def cookie_add(queue):
    driver = get_chromedriver(use_proxy=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                                                         " (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36")
    while True:
        if not queue.is_empty():
            curr_proxy = queue.get_proxy()

            driver.execute_script(f"window.postMessage({{type: 'f', params: '{curr_proxy}'}}, '*');")
            driver.get("https://sklepkoszykarza.pl/")
            cookies_loaded = False
            while not cookies_loaded:
                if "https://sklepkoszykarza.pl/" == driver.current_url:
                    time.sleep(1)
                elif "hcaptcha" in str(driver.page_source):
                    while "hcaptcha" in driver.page_source:
                        time.sleep(1)
                    cookies_loaded = True
                else:
                    cookies_loaded = True

            curr_cookies = driver.get_cookies()

            add_cookie = CookieInput({curr_proxy: curr_cookies})
            add_cookie.run()
            driver.delete_all_cookies()
        time.sleep(2)


if __name__ == "__main__":
    with open("USER_DATA/proxies.txt", "r") as file:
        proxies = file.read().split('\n')

    for proxy in proxies:
        add_proxy = ProxyInput(proxy)
        add_proxy.run()

    proxy_queue = ProxyInterpreter()

    threads = []

    cookies = {}

    for i in range(1):
        t = Thread(target=cookie_main, args=(proxy_queue, ))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    cookie_queue = CookieInterpreter()
    while not cookie_queue.is_empty():
        cookie = cookie_queue.get_cookie()
        for key, value in cookie.items():
            cookies[key] = value

    with open("USER_DATA/cookies.json", "w") as file:
        json.dump(cookies, file)

# import requests
# import datetime
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By

# site_key = "f9630567-8bfa-4fc9-8ee5-9c91c6276dff"
# captcha_api = "68d7d5fb4f65846f47e34a89945eb18d"


# def get_hcaptcha(form_url, proxy):
#     print(f" Solving hcaptcha...")
#     proxy_list = proxy.split(':')
#     api_proxy = f'{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}'
#     proxy_dict = {
#         "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
#         "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
#     }
#     s = requests.Session()
#     r = s.post('http://2captcha.com/in.php?key={}&method=hcaptcha&sitekey={}&pageurl={}&proxy={}'
#                     .format(captcha_api, site_key, form_url, api_proxy),
#                     proxies=proxy_dict).text
#     print(r)
#     id = r.split("|")[1]
#     captcha_r = s.get(f'https://2captcha.com/res.php?key={captcha_api}&action=get&id={id}',
#                            proxies=proxy_dict).text
#     while "CAPCHA_NOT_READY" in captcha_r:
#         time.sleep(5)
#         captcha_r = s.get(f'https://2captcha.com/res.php?key={captcha_api}&action=get&id={id}',
#                                proxies=proxy_dict).text
#     if "OK" in captcha_r:
#         return captcha_r.split("|")[1]
#     else:
#         print(f" Error getting captcha "
#               f"token. Retrying...")
#         get_hcaptcha(form_url, proxy)
#
#
# def sk(queue):
#     # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36
#     # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36
#     driver = get_chromedriver(use_proxy=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36")
#     while not queue.is_empty():
#         curr_proxy = queue.get_proxy()
#
#         driver.execute_script(f"window.postMessage({{type: 'f', params: '{curr_proxy}'}}, '*');")
#         driver.get("https://sklepkoszykarza.pl/")
#         cookies_loaded = False
#         while not cookies_loaded:
#             if "captcha-bypass" in str(driver.page_source):
#                 print(curr_proxy)
#                 token = get_hcaptcha("https://sklepkoszykarza.pl/", curr_proxy)
#                 # driver.find_element_by_id('challenge-form').click()
#                 print(token)
#                 # time.sleep(5)
#                 driver.execute_script(f"document.getElementsByName('h-captcha-response')[0].innerHTML = '{token}';")
#                 time.sleep(1)
#                 driver.execute_script(f"document.getElementsByName('g-recaptcha-response')[0].innerHTML = '{token}';")
#                 time.sleep(1)
#                 driver.execute_script("document.getElementById('challenge-form').submit();")
#                 if "captcha-bypass" in str(driver.page_source):
#                     time.sleep(1)
#                     driver.execute_script(f"document.getElementsByName('h-captcha-response')[0].innerHTML = '{token}';")
#                     time.sleep(1)
#                     driver.execute_script(f"document.getElementsByName('g-recaptcha-response')[0].innerHTML = '{token}';")
#                     time.sleep(1)
#                     driver.execute_script("document.getElementById('challenge-form').submit();")
#                 cookies_loaded = True
#                 time.sleep(1000)
#             elif "https://sklepkoszykarza.pl/" == driver.current_url:
#                 time.sleep(1)
#             else:
#                 cookies_loaded = True
#
#         curr_cookies = driver.get_cookies()
#         for c in curr_cookies:
#             if c["name"] == "cf_clearance":
#                 add_cookie = CookieInput({curr_proxy: c['value']})
#                 add_cookie.run()
#         driver.delete_all_cookies()
#         time.sleep(1)
#     driver.quit()
#
#
# if __name__ == "__main__":
#     with open("USER_DATA/proxies.txt", "r") as file:
#         proxies = file.read().split('\n')
#
#     for proxy in proxies:
#         add_proxy = ProxyInput(proxy)
#         add_proxy.run()
#
#     proxy_queue = ProxyInterpreter()
#     sk(proxy_queue)

# var hcaptchaa = document.getElementsByName('h-captcha-response')[0];
# var recatpchaa = document.getElementsByName('g-recaptcha-response')[0];
# var form = document.getElementById('challenge-form');
