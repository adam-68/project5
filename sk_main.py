from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from discord_webhook import DiscordEmbed, DiscordWebhook
from cookie_gen import *
import json
import requests
import cloudscraper
import time
import datetime
import re


class Sk:
    def __init__(self, task, profile, cf):
        self.task = task
        self.profile = profile
        self.s = cloudscraper.Session()
        self.product_url = self.task['product_url']
        self.product_image_url = ""
        self.site_key = "f9630567-8bfa-4fc9-8ee5-9c91c6276dff"
        self.captcha_api = "68d7d5fb4f65846f47e34a89945eb18d"
        self.token = ""
        self.title = ""
        self.cart_url = ""
        self.size = ""
        self.checkout_token = ""
        self.referer = ""
        if self.task['bypass'] == "enable":
            self.bypass_stage = "configuring"
        else:
            self.bypass_stage = "disable"
        self.error_num = 0
        self.cf = cf

    def login(self):
        if self.cf == "y" and "cf_clearance" not in self.s.cookies.get_dict().keys():
            load_cookie = ProxyInput(self.task['proxy'])
            load_cookie.run()
            wait_for_cookie = CookieInterpreter()
            while wait_for_cookie.is_empty():
                time.sleep(1)
            curr_cookie = wait_for_cookie.get_cookie()
            while self.task['proxy'] not in curr_cookie.keys():
                return_cookie = CookieInput(curr_cookie)
                return_cookie.run()
                curr_cookie = wait_for_cookie.get_cookie()

            for cookie in curr_cookie[self.task['proxy']]:
                if cookie['name'] == "cf_clearance":
                    self.s.cookies.set(cookie['name'], cookie['value'])

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Host": "sklepkoszykarza.pl",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }

        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Logging in...")
            main_page = self.s.get("https://sklepkoszykarza.pl/", headers=headers, proxies=self.task['proxy_dict'],
                                   timeout=10)
            self.token = re.search(r'_token(.*?)>', main_page.content.decode('utf-8')).group()[29:-2]
            login_data = f"_token={self.token}&email={self.profile['email']}&password={self.profile['password']}"
            login_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "navigate",
                "cache-control": "max-age=0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
                          "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Sec-Fetch-Dest": "document",
                "content-length": str(len(login_data)),
                "content-type": "application/x-www-form-urlencoded",
                "Sec-Fetch-User": "?1",
                "Host": "sklepkoszykarza.pl",
                "origin": "https://sklepkoszykarza.pl",
                "referer": "https://sklepkoszykarza.pl/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
            }
            log_in = self.s.post("https://sklepkoszykarza.pl/signin", headers=login_headers, data=login_data,
                                 proxies=self.task['proxy_dict'], timeout=10)
            while "Witaj" not in log_in.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 5:
                    self.error_num = 0
                    self.login()
                    return
                time.sleep(1)
                log_in = self.s.post("https://sklepkoszykarza.pl/signin", headers=login_headers, data=login_data,
                                     proxies=self.task['proxy_dict'], timeout=5)
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Logging in: Timeout. Retrying...")
            self.login()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Logging in: Connection Error. Retrying...")
            self.login()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Logging in: {error}. Retrying...")
            self.login()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Logging in: Request Error. Retrying...")
            self.login()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Logging in: {error}. Retrying...")
            self.login()
            return

        self.load_bypass_page()
        return

    def load_bypass_page(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,"
                      "*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Host": "sklepkoszykarza.pl",
            "Referer": "https://sklepkoszykarza.pl/user/data",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Loading bypass...")
            bypass_products = self.s.get("https://sklepkoszykarza.pl/products/akcesoria/category,4/item,24/sort,2?",
                                         headers=headers, proxies=self.task['proxy_dict'], timeout=15)
            self.product_url = BeautifulSoup(bypass_products.content.decode('utf-8'),
                                             'html.parser').find('div', {'class': "product"}).find('a')['href']
            headers['Referer'] = "https://sklepkoszykarza.pl/products/akcesoria/category,4/item,24/sort,2?"
            bypass_product_page = self.s.get(self.product_url, headers=headers, proxies=self.task['proxy_dict'],
                                             timeout=15)
            self.size = re.search(r'data-mapsize="(.*?)"', bypass_product_page.content.decode('utf-8')).group().split('"')[-2]
            cart_add_info = re.search(r'<form method="POST" action="(.*?)" accept-charset="UTF-8" name="product__add" '
                                      r'class="product__add"><input name="_token" type="hidden" value="(.*?)">',
                                      bypass_product_page.content.decode('utf-8')).group().split('"')
            self.cart_url = cart_add_info[3]
            self.token = cart_add_info[-2]
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Bypass page: Timeout. Retrying...")
            self.load_bypass_page()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Bypass page: Connection Error. Retrying...")
            self.load_bypass_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Bypass page: {error}. Retrying...")
            self.load_bypass_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Bypass page: Request error. Retrying...")
            self.load_bypass_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Bypass page: {error}. Retrying...")
            self.load_bypass_page()
            return

        self.basket_add()
        return

    def load_product_page(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Host": "sklepkoszykarza.pl",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} '
                  f'[TASK {self.task["id"]}] Waiting for product...')
            if self.referer:
                headers['Referer'] = self.referer
                headers['Sec-Fetch-Site'] = "same-origin"
            self.product_url = self.task['product_url']
            product_page = self.s.get(self.product_url, headers=headers, proxies=self.task["proxy_dict"],
                                      timeout=15)

            while 'class="product__add"' and self.task['sku'].upper() not in product_page.content.decode('utf-8'):
                time.sleep(.2)
                headers['Sec-Fetch-Site'] = "same-origin"
                headers['Referer'] = self.product_url
                try:
                    product_page = self.s.get(self.product_url, headers=headers, proxies=self.task["proxy_dict"],
                                              timeout=12)
                    if "Please turn JavaScript on and reload the page." in product_page.content.decode('utf-8') and self.cf == "y":
                        print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} '
                              f'[TASK {self.task["id"]}] Generating cookie...')
                        load_cookie = ProxyInput(self.task['proxy'])
                        load_cookie.run()
                        wait_for_cookie = CookieInterpreter()
                        while wait_for_cookie.is_empty():
                            time.sleep(1)
                        curr_cookie = wait_for_cookie.get_cookie()
                        while self.task['proxy'] not in curr_cookie.keys():
                            return_cookie = CookieInput(curr_cookie)
                            return_cookie.run()
                            curr_cookie = wait_for_cookie.get_cookie()
                        self.s.cookies.set("cf_clearance", curr_cookie[self.task['proxy']])
                        print(f'{datetime.datetime.now().strftime("[%H:%M:%S:%f]")} '
                              f'[TASK {self.task["id"]}] Waiting for product...')
                except requests.exceptions.ConnectionError:
                    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                          f"[TASK {self.task['id']}] Product page: Connection Error. Retrying...")
                except requests.exceptions.HTTPError as error:
                    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                          f"[TASK {self.task['id']}] Product page: {error}. Retrying...")
                except requests.exceptions.RequestException:
                    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                          f"[TASK {self.task['id']}] Product page: Request Error. Retrying...")
                except requests.exceptions.Timeout:
                    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                          f"[TASK {self.task['id']}] Product page: Timeout. Retrying...")
                except Exception as error:
                    print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                          f"[TASK {self.task['id']}] Product page: {error}. Retrying...")

            cart_add_info = re.search(r'<form method="POST" action="(.*?)" accept-charset="UTF-8" name="product__add" '
                                      r'class="product__add"><input name="_token" type="hidden" value="(.*?)">',
                                      product_page.content.decode('utf-8')).group().split('"')
            sizes = re.findall(r'data-size="(.*?)"', product_page.content.decode('utf-8'))
            self.cart_url = cart_add_info[3]
            self.token = cart_add_info[-2]
            self.product_image_url = re.search(
                rf'https://blob\.sxv\.pl/shops/media(.*?){self.task["sku"]}(.*?)\.jpg',
                product_page.content.decode('utf-8')).group()
            self.title = re.search(r"<title>(.*?)</title>", product_page.content.decode('utf-8')).group()[7:-8].split("|")[0]

            if self.task['size'] in sizes:
                self.size = self.task['size']
            elif self.task['size'] not in sizes and len(sizes) > 0:
                self.size = sizes[0]
            elif len(sizes) == 0:
                print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                      f"[TASK {self.task['id']}] Sold out. Waiting for restock...")
                self.load_product_page()
                return
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Product page: Timeout. Retrying...")
            self.load_product_page()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Product page: Connection Error. Retrying...")
            self.load_product_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Product page: {error}. Retrying...")
            self.load_product_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Product page: Request Error. Retrying...")
            self.load_product_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Product page: {error}. Retrying...")
            self.load_product_page()
            return

        self.basket_add()
        return

    def basket_add(self):
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Adding to basket...")
        data = f"_token={self.token}&size={self.size}"
        headers = {
            "Host": "sklepkoszykarza.pl",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://sklepkoszykarza.pl",
            "Cache-Control": "max-age=0",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data)),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Referer": self.product_url,
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            carting = self.s.post(self.cart_url, headers=headers, data=data,
                                  proxies=self.task["proxy_dict"], timeout=6)
            while "koszyk jest pusty" in carting.content.decode('utf-8') or "Zamów" not in carting.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 5:
                    self.error_num = 0
                    self.referer = self.product_url
                    if self.bypass_stage == "configuring":
                        self.load_bypass_page()
                    else:
                        self.load_product_page()
                    return
                time.sleep(.1)
                carting = self.s.post(self.cart_url, headers=headers, data=data,
                                      proxies=self.task["proxy_dict"], timeout=6)
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Added to basket.")
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Carting: Timeout. Retrying...")
            self.basket_add()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Carting: Connection Error. Retrying...")
            self.basket_add()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Carting: Request Error. Retrying...")
            self.basket_add()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Carting: {error}. Retrying...")
            self.basket_add()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Carting: {error}. Retrying...")
            self.error_num += 1
            if self.error_num > 5:
                self.error_num = 0
                if self.bypass_stage == "configuring":
                    self.load_bypass_page()
                else:
                    self.load_product_page()
            else:
                self.basket_add()
            return

        if self.bypass_stage == "configured":
            self.sum_order()
        elif self.bypass_stage == "configuring" or "disabled":
            self.load_address_page()
        return

    def load_address_page(self):
        headers = {
            "Host": "sklepkoszykarza.pl",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Referer": "https://sklepkoszykarza.pl/login",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Loading address page...")
            address_page = self.s.get("https://sklepkoszykarza.pl/order/anonymous", headers=headers,
                                      proxies=self.task['proxy_dict'], timeout=6)
            while "Wybierz metodę dostawy" not in address_page.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 5:
                    self.error_num = 0
                    self.referer = "https://sklepkoszykarza.pl/order"
                    if self.bypass_stage == "configuring":
                        self.load_bypass_page()
                    else:
                        self.load_product_page()
                    return
                time.sleep(.1)
                address_page = self.s.get("https://sklepkoszykarza.pl/order/anonymous", headers=headers,
                                          proxies=self.task['proxy_dict'], timeout=6)

            self.token = re.search(r'_token(.*?)>', address_page.content.decode('utf-8')).group()[29:-2]
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address page: Timeout. Retrying...")
            self.load_address_page()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address page: Connection Error. Retrying...")
            self.load_address_page()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address page: Request Error. Retrying...")
            self.load_address_page()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address page: {error}. Retrying...")
            self.load_address_page()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address page: {error}. Retrying...")
            self.error_num += 1
            if self.error_num > 5:
                self.error_num = 0
                if self.bypass_stage == "configuring":
                    self.load_bypass_page()
                else:
                    self.load_product_page()
            else:
                self.load_address_page()
            return
        self.send_address()
        return

    def send_address(self):
        data = f"_token={self.token}&addressValue_select=251774&" \
               f"addressValue%5Bfirstname%5D={self.profile['first_name']}&" \
               f"addressValue%5Blastname%5D={self.profile['last_name']}&" \
               f"addressValue%5Baddress%5D={self.profile['street']}+{self.profile['house_number']}&" \
               f"addressValue%5Bbusiness%5D=&addressValue%5Bpostcode%5D={self.profile['post_code']}&" \
               f"addressValue%5Bcity%5D={self.profile['city']}&addressValue%5BCountry_id%5D=PL&" \
               f"addressValue%5BStates_id%5D=&addressValue%5Bphone%5D=%2B48{self.profile['phone']}&" \
               f"phone_country=pl&addressValue%5Bcompany%5D=&addressValue%5BNIP%5D=&" \
               f"unregistered=&invoiceValue_select=&invoiceValue%5Bcompany%5D=&" \
               f"invoiceValue%5BNIP%5D=&" \
               f"invoiceValue%5Baddress%5D={self.profile['street']}+{self.profile['house_number']}&" \
               f"invoiceValue%5Bpostcode%5D={self.profile['post_code']}&" \
               f"invoiceValue%5Bcity%5D={self.profile['city']}&" \
               f"invoiceValue%5BCountry_id%5D=PL&agree=1"

        # data = f"_token={self.token}&addressValue%5Bfirstname%5D={self.profile['first_name']}&" \
        #        f"addressValue%5Blastname%5D={self.profile['last_name']}&" \
        #        f"addressValue%5Baddress%5D={self.profile['street']}+" \
        #        f"{self.profile['house_number']}&" \
        #        f"addressValue%5Bbusiness%5D=&addressValue%5Bpostcode%5D={self.profile['post_code']}&" \
        #        f"addressValue%5Bcity%5D={self.profile['city']}&addressValue%5BCountry_id%5D=PL&" \
        #        f"addressValue%5BStates_id%5D=&addressValue%5Bphone%5D=%2B48{self.profile['phone']}&" \
        #        f"phone_country=pl&addressValue%5Bcompany%5D=&addressValue%5BNIP%5D=&" \
        #        f"email={self.profile['email']}&isRegistered=0&unregistered=1&" \
        #        f"invoiceValue_select=&invoiceValue%5Bcompany%5D=&invoiceValue%5BNIP%5D=&" \
        #        f"invoiceValue%5Baddress%5D={self.profile['street']}+" \
        #        f"{self.profile['house_number']}&" \
        #        f"invoiceValue%5Bpostcode%5D={self.profile['post_code']}&" \
        #        f"invoiceValue%5Bcity%5D={self.profile['city']}&invoiceValue%5BCountry_id%5D=PL&agree=1"

        headers = {
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                          " Chrome/83.0.4103.61 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://sklepkoszykarza.pl",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://sklepkoszykarza.pl/order",
            "Host": "sklepkoszykarza.pl",
            "Connection": "keep-alive",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Content-Length": str(len(data)),
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Filling address...")
            address_post = self.s.post("https://sklepkoszykarza.pl/order", headers=headers, data=data,
                                       proxies=self.task['proxy_dict'], timeout=6)

            while "Przejdź do podsumowania" not in address_post.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 10:
                    self.error_num = 0
                    self.referer = "https://sklepkoszykarza.pl/order/delivery"
                    if self.bypass_stage == "configuring":
                        self.load_bypass_page()
                    else:
                        self.load_product_page()
                    return
                elif self.error_num > 5:
                    self.load_address_page()
                    return

                time.sleep(.1)
                address_post = self.s.post("https://sklepkoszykarza.pl/order", headers=headers, data=data,
                                           proxies=self.task['proxy_dict'], timeout=6)
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address form: Timeout. Retrying...")
            self.send_address()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address form: Connection Error. Retrying...")
            self.send_address()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address form: Request Error. Retrying...")
            self.send_address()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address form: {error}. Retrying...")
            self.send_address()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Address form: {error}. Retrying...")
            self.error_num += 1
            if self.error_num > 10:
                if self.bypass_stage == "configuring":
                    self.load_bypass_page()
                else:
                    self.load_product_page()
            elif self.error_num > 5:
                self.load_address_page()
            else:
                self.send_address()
            return

        self.send_payment_data()
        return

    def send_payment_data(self):
        # Pobranie
        # data = f"_token={self.token}&Delivery_form_id=1_2&Payment_id=1&" \
        #        f"input_summary_city=Nie+Wybrano&input_summary_post_code=Nie+Wybrano&" \
        #        f"input_summary_street=Nie+Wybrano&input_summary_province=Nie+Wybrano&" \
        #        f"InPost_machineName=&InPost_machineAddress=&parcelshop=&" \
        #        f"parcelshop_address=&city_search=&personal_collection%5Bshop%5D=&" \
        #        f"personal_collection%5Baddress%5D="
        # Blik
        data = f"_token={self.token}&Delivery_form_id=1_1&Payment_id=9&" \
               f"input_summary_city=Nie+Wybrano&input_summary_post_code=Nie+Wybrano&" \
               f"input_summary_street=Nie+Wybrano&input_summary_province=Nie+Wybrano&" \
               f"InPost_machineName=&InPost_machineAddress=&parcelshop=&" \
               f"parcelshop_address=&city_search=&personal_collection%5Bshop%5D=&" \
               f"personal_collection%5Baddress%5D="

        headers = {
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(data)),
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://sklepkoszykarza.pl",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Referer": "https://sklepkoszykarza.pl/order/delivery",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Host": "sklepkoszykarza.pl",
            "Connection": "keep-alive",
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Filling payment...")
            send_payment_req = self.s.post("https://sklepkoszykarza.pl/order/delivery", headers=headers,
                                           data=data, proxies=self.task['proxy_dict'], timeout=6)
            while "Zamawiam i płacę" not in send_payment_req.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 8:
                    self.error_num = 0
                    self.referer = "https://sklepkoszykarza.pl/order/confirm"
                    if self.bypass_stage == "configuring":
                        self.load_bypass_page()
                    else:
                        self.load_product_page()
                    return
                time.sleep(.1)
                send_payment_req = self.s.post("https://sklepkoszykarza.pl/order/delivery", headers=headers,
                                               data=data, proxies=self.task['proxy_dict'], timeout=6)
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Payment form: Timeout. Retrying...")
            self.send_payment_data()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Payment form: Connection Error. Retrying...")
            self.send_payment_data()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Payment form: Request Error. Retrying...")
            self.send_payment_data()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Payment form: {error}. Retrying...")
            self.send_payment_data()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Payment form: {error}. Retrying...")
            self.error_num += 1
            if self.error_num > 5:
                if self.bypass_stage == "configuring":
                    self.load_bypass_page()
                else:
                    self.load_product_page()
            else:
                self.send_payment_data()
            return
        self.checkout_token = self.token
        if self.bypass_stage == "configuring":
            self.remove_bypass_item()
        elif self.bypass_stage == "disabled":
            self.sum_order()
        return

    def remove_bypass_item(self):
        headers = {
            "Host": "sklepkoszykarza.pl",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.61 Safari/537.36",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
                  f"Emptying cart...")
            cart_page = self.s.get("https://sklepkoszykarza.pl/basket", headers=headers, proxies=self.task['proxy_dict'],
                                   timeout=5)
            empty_cart_url = re.search(r'https://sklepkoszykarza\.pl/basket/delete/(.*?)"', cart_page.content.decode('utf-8')).group()[:-1]
            headers['Referer'] = "https://sklepkoszykarza.pl/basket"
            empty_cart = self.s.get(empty_cart_url, headers=headers, proxies=self.task['proxy_dict'], timeout=5)

            while "koszyk jest pusty" not in empty_cart.content.decode('utf-8'):
                time.sleep(.5)
                empty_cart = self.s.get(empty_cart_url, headers=headers, proxies=self.task['proxy_dict'], timeout=5)
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Emptying cart: Timeout. Retrying...")
            self.remove_bypass_item()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Emptying cart: Connection Error. Retrying...")
            self.remove_bypass_item()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Emptying cart: Request Error. Retrying...")
            self.remove_bypass_item()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Emptying cart: {error}. Retrying...")
            self.remove_bypass_item()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Emptying cart: {error}. Retrying...")
            self.remove_bypass_item()
            return
        #
        self.referer = "https://sklepkoszykarza.pl/basket"
        self.bypass_stage = "configured"
        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] "
              f"Bypass loaded.")
        self.load_product_page()
        return

    def sum_order(self):
        data = f"_token={self.checkout_token}"
        headers = {
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://sklepkoszykarza.pl",
            "Cache-Control": "max-age=0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Referer": "https://sklepkoszykarza.pl/order/confirm",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "pl-PL,pl;q=0.9,en-XA;q=0.8,en;q=0.7,en-US;q=0.6,de;q=0.5",
            "Content-Length": str(len(data)),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
            "Host": "sklepkoszykarza.pl",
        }
        try:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} [TASK {self.task['id']}] Checking out...")
            order_id_page = self.s.post("https://sklepkoszykarza.pl/order/confirm", headers=headers,
                                        data=data, proxies=self.task["proxy_dict"], timeout=15)
            while "Dziękujemy za złożenie zamówienia" not in order_id_page.content.decode('utf-8'):
                self.error_num += 1
                if self.error_num > 15:
                    self.error_num = 0
                    self.referer = "https://sklepkoszykarza.pl/order/confirm"
                    self.load_product_page()
                    return
                time.sleep(.1)
                order_id_page = self.s.post("https://sklepkoszykarza.pl/order/confirm", headers=headers,
                                            data=data, proxies=self.task["proxy_dict"], timeout=15)
        except requests.exceptions.Timeout:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Checkout: Timeout. Retrying...")
            self.sum_order()
            return
        except requests.exceptions.ConnectionError:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Checkout: Connection Error. Retrying...")
            self.sum_order()
            return
        except requests.exceptions.RequestException:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Checkout: Request Error. Retrying...")
            self.sum_order()
            return
        except requests.exceptions.HTTPError as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Checkout: {error}. Retrying...")
            self.sum_order()
            return
        except Exception as error:
            print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
                  f"[TASK {self.task['id']}] Checkout: {error}. Retrying...")
            self.error_num += 1
            if self.error_num > 5:
                self.load_address_page()
            else:
                self.sum_order()
            return

        print(f"{datetime.datetime.now().strftime('[%H:%M:%S:%f]')} "
              f"[TASK {self.task['id']}] Successful checkout. Email: {self.profile['email'].replace('%40', '@')}")
        self.webhook()
        return

    def webhook(self):
        webhook = DiscordWebhook(
            url=self.task['webhook_url'],
            username="Brick Bot")
        embed = DiscordEmbed(title='Successfully checked out a product.', color=242424)
        embed.set_footer(text='via Brick Bot',
                         icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/"
                                  "Internet_Explorer_9_icon.svg/384px-Internet_Explorer_9_icon.svg.png")
        embed.set_timestamp()
        embed.add_embed_field(name='Product', value=self.title)
        embed.add_embed_field(name='Size', value=self.task['size'])
        embed.set_thumbnail(url=self.product_image_url)
        embed.add_embed_field(name='Email', value=self.profile["email"].replace("%40", "@"))
        embed.add_embed_field(name='Payment Type', value='On Delivery')
        webhook.add_embed(embed)
        response = webhook.execute()


def main(task, profile, enable_cf_bypass):
    new_instance = Sk(task, profile, enable_cf_bypass)
    new_instance.login()


if __name__ == "__main__":
    with open("USER_DATA/tasks.json", "r") as f1, \
            open("USER_DATA/proxies.txt", "r") as f2, \
            open("USER_DATA/profiles.json", "r") as f3:
        tasks = json.load(f1)
        proxies = f2.read().split("\n")
        profiles = json.load(f3)
    threads = []
    is_cf_on = input("Is cloudflare on? (y/n)")

    proxy_queue = ProxyInterpreter()

    main_threads = []

    for i in range(1):
        proxy_list = proxies[i].split(":")
        proxy_dict = {
            "http": f"http://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}",
            "https": f"https://{proxy_list[2]}:{proxy_list[3]}@{proxy_list[0]}:{proxy_list[1]}"
        }
        tasks[i]["proxy_dict"] = proxy_dict
        tasks[i]["proxy"] = proxies[i]
        t = Thread(target=main, args=(tasks[i], profiles[i], is_cf_on))
        t.start()
        main_threads.append(t)

    cookie_gen = Thread(target=cookie_add, args=(proxy_queue,))
    cookie_gen.start()
    main_threads.append(cookie_gen)

    for t in main_threads:
        t.join()

