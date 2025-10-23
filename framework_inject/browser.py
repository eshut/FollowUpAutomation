"""Framework: https://github.com/eshut/Framework-Python"""

import http
import os

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from framework_inject.utils.json_util import JsonUtil

from framework_inject.constants import DEFAULT_BROWSER_DEBUGGER_ADDRESS, DEFAULT_BROWSER_DEBUGGER_PORT, \
    REMOTE_ZENROWS_BROWSER
from framework_inject.constants import DEFAULT_VIEWPORT_SIZE, PLAYWRIGHT_PAGE_DEFAULT_TIMEOUT_MS, BROWSERS, \
    CHROME_BROWSER, FIREFOX_BROWSER, REMOTE_CHROME_BROWSER, REMOTE_FIREFOX_BROWSER, PLAYWRIGHT_DEFAULT_LOCALE
from framework_inject.logger.logger import Logger

load_dotenv()
log_level = os.getenv("LOG_LEVEL")
localization = os.getenv("LOCALIZATION")
browser = os.getenv("BROWSER")
save_dir = os.getenv("SAVE_DIR")
firefox_location = os.getenv("FIREFOX_LOCATION")
ZEN_ROWS_URL = os.getenv("ZEN_ROWS_URL")


class DriverWebSocket(Logger):
    def __init__(self, host=DEFAULT_BROWSER_DEBUGGER_ADDRESS, port=None, logger=__file__):
        if port is None:
            cdp_address = f"{host}:{DEFAULT_BROWSER_DEBUGGER_PORT}"
        else:
            cdp_address = f"{host}:{port}"
        super().__init__(logger)
        self.debugger_address = f"{cdp_address}/json/version"

    def get_websocket_debugger_url(self):
        try:
            response = requests.get(self.debugger_address)
        except:
            return False

        if response.status_code == http.HTTPStatus.OK:
            data = response.json()
            web_socket_debugger_url = data.get("webSocketDebuggerUrl")

            if web_socket_debugger_url:
                return web_socket_debugger_url
            else:
                self.logger.error("WebSocketDebuggerUrl not found.")
        else:
            self.logger.error(f"Failed to fetch debugger version. Status code: {response.status_code}")


class ChromeBrowser(Logger):
    def __init__(self, logger=__file__, port=None):
        super().__init__(logger)
        self.driver_ws_url = DriverWebSocket(port=port).get_websocket_debugger_url()
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None

    def run_browser(self, chrome_profile, proxy=None):
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(headless=False, proxy=proxy,
        user_data_dir=chrome_profile,
        viewport={"width": 1366, "height": 768},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998 Safari/537.36"
        )
        self.context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",  # Do Not Track
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://google.com"
        })
        self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.context.route('**/*', lambda route, request: route.abort() if
            request.resource_type in ['image', 'media', 'font', 'stylesheet'] else route.continue_()) # BLOCK IMAGES

        self.page = self.context.new_page()
        self.page.set_viewport_size({"width": 1366, "height": 768})
        self.page.set_default_timeout(PLAYWRIGHT_PAGE_DEFAULT_TIMEOUT_MS)
        return self.browser, self.page, self.context, self.close_browser

    def run_remote_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(self.driver_ws_url)
        self.context = self.browser.contexts[0]
        self.context.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",  # Do Not Track
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://google.com"
        })
        self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        # self.context.route('**/*', lambda route, request: route.abort() if
        #     request.resource_type in ['image', 'media', 'font', 'stylesheet'] else route.continue_()) # BLOCK IMAGES

        self.page = self.context.new_page()
        self.page.set_viewport_size({"width": 1366, "height": 768})
        return self.browser, self.page, self.context

    def run_zenrows_remote_browser(self):
        self.playwright = sync_playwright().start()
        self.driver_ws_url = ZEN_ROWS_URL
        self.browser = self.playwright.chromium.connect_over_cdp(self.driver_ws_url)
        context = self.browser.contexts[0]
        self.page = context.new_page()
        return self.browser, self.page

    def recreate_context_with_high_resolution(self, context, viewport, device_scale_factor):
        """
        Recreates the browser context with high resolution settings.

        Args:
            context: The existing browser context.
            viewport (dict): The viewport settings for width and height.
            device_scale_factor (int): The scale factor for the device.

        Returns:
            A new high-resolution context.
        """
        # Get the current page origin (if it exists)
        origin = self.page.url if hasattr(self, 'page') and self.page else None

        # Close the old context
        context.close()

        # Create a new context with high resolution
        new_context = self.browser.new_context(
            viewport=viewport,
            device_scale_factor=device_scale_factor
        )

        # Create a new page in the new context
        new_page = new_context.new_page()

        # Navigate to origin only if it is valid
        if origin and origin.startswith(("http://", "https://")):
            new_page.goto(origin)
        else:
            self.logger.warning(f"Invalid or unsupported origin URL: {origin}")

        return new_context

    def close_browser(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


class FireFoxBrowser:
    def __init__(self):
        self.driver_ws_url = DriverWebSocket().get_websocket_debugger_url()
        self.playwright = None
        self.browser = None
        self.page = None

    def run_browser(self, locale=PLAYWRIGHT_DEFAULT_LOCALE):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=False)
        context = self.browser.new_context(locale=locale)
        self.page = context.new_page()
        self.page.set_default_timeout(PLAYWRIGHT_PAGE_DEFAULT_TIMEOUT_MS)
        self.page.set_viewport_size(DEFAULT_VIEWPORT_SIZE)
        return self.browser, self.page

    def run_remote_browser(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect_over_cdp(self.driver_ws_url)
        context = self.browser.contexts[0]
        self.page = context.new_page()
        return self.browser, self.page

    def close_browser(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def clear(cls):
        if cls in cls._instances:
            del cls._instances[cls]


class BrowserFactory(Logger):
    def __init__(self, logger=__file__, id=0):
        super().__init__(logger)
        self.json_util = JsonUtil()
        # self.accounts = self.json_util.load_file("accounts.json")['accounts'][id]

    def get_browser(self, browsertype, port=None):
        try:
            if browsertype == BROWSERS.index(FIREFOX_BROWSER):
                browser, page = FireFoxBrowser().run_browser(localization)
                return browser, page
            elif browsertype == BROWSERS.index(CHROME_BROWSER):
                # user_data_dir = os.path.expanduser("~/" + self.accounts['chrome_profile'])
                browser, page, context, close_browser = ChromeBrowser().run_browser(chrome_profile="~/~/chrome_profiles/AutomationLikeCrazy")
                return browser, page, context, close_browser
            elif browsertype == BROWSERS.index(REMOTE_FIREFOX_BROWSER):
                browser, page = FireFoxBrowser().run_remote_browser()
                return browser, page
            elif browsertype == BROWSERS.index(REMOTE_CHROME_BROWSER):
                browser, page, context = ChromeBrowser(port=port).run_remote_browser()
                return browser, page, context, None
            elif browsertype == BROWSERS.index(REMOTE_ZENROWS_BROWSER):
                browser, page = ChromeBrowser().run_zenrows_remote_browser()
                return browser, page
            raise AssertionError("Browser not found")
        except AssertionError as _e:
            self.logger.error(_e)


class RunBrowser(metaclass=Singleton):
    def __init__(self, port=None, id=0):
        if browser in BROWSERS:
            browser_index = BROWSERS.index(browser)
            self.browser, self.page, self.context, self.close_browser_BF = BrowserFactory(id=id).get_browser(browser_index, port=port)
        else:
            raise Exception("No Such Browser")

    def update_page(self, new_page):
        """Method to update the page globally."""
        self.page = new_page

    def close_browser(self):
        """Method to close the browser and clear singleton instance."""
        self.close_browser_BF()
        RunBrowser.clear()

