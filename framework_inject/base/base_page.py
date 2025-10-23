"""Framework: https://github.com/eshut/Framework-Python"""

import datetime
import os
import random
from abc import ABC
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Frame, Locator

from framework_inject.browser import RunBrowser
from framework_inject.constants import DEFAULT_WAIT_TIME_MS, LOG_TIME_STRUCTURE
from framework_inject.logger.logger import Logger
from framework_inject.base.context import Context


class BasePage(ABC, Logger):
    def __init__(self, logger=__file__, port=None, id=0):
        super().__init__(logger)
        self.port = port
        self.context = Context()
        self.context["I"] = self
        self.run_browser = RunBrowser(port=port, id=id)
        self.page = self.run_browser.page
        self.browser = self.run_browser.browser
        self.browser_context = self.run_browser.context

    def clear(self):
        self.page = self.run_browser.browser.contexts[0].new_page()

    def goto(self, url):
        self.page.goto(url)

    def set_auth_token(self, token: str) -> None:
        """
        Set an authorization token in localStorage and refresh the page.
        """
        self.logger.debug("Set an authorization token")
        self.page.evaluate(f"window.localStorage.setItem('token', '{token}');")
        self.page.reload()

    def get_cookies(self) -> List[Dict[str, Any]]:
        """
        Get the cookies from the browser context.
        """
        return self.page.context.cookies()

    def get_element(self, selector: str, frame: Optional[Frame] | Optional[Locator] = None, prev_elem=None,
                    time=DEFAULT_WAIT_TIME_MS) \
            -> Locator:
        """
        Get a single element on the page or in a specific frame.

        Args:
            selector (str): The selector for the element.
            frame (Frame, optional): The specific frame to search in. Defaults to the main page.

        Returns:
            Optional[ElementHandle]: The element if found, None otherwise.
        """
        target = frame or self.page

        try:
            if prev_elem:
                element = prev_elem.locator(selector)
                return element
            elif self.wait_for_element_conditional(selector, frame=frame, time=time):
                element = target.locator(selector)
                return element
            return None
        except Exception as e:
            self.logger.debug(f"Error getting element from '{selector}': {str(e)}")
            return None

    def get_elements_list(self, selector: str, element: Optional[Any] = None, frame: Optional[Frame] = None):
        """
        Get a list of elements on the page, in a specific frame, or within a given element.

        Args:
            selector (str): The selector for the elements.
            element (Optional[ElementHandle], optional): The parent element to search within. Defaults to None (page level).
            frame (Frame, optional): The specific frame to search in. Defaults to the main page.

        Returns:
            List[ElementHandle]: A list of elements matching the selector.
        """
        target = frame or self.page
        parent = element or target

        try:
            # Wait for the element (or the frame/parent element) and query the list
            # parent.locator("//div[contains(@class, 'blackjackCardsStack__card')]").all()

            if self.wait_for_element_conditional(selector, frame=frame):
                elements = parent.locator(selector).all()
                return elements
            return []
        except Exception as e:
            self.logger.debug(f"Error getting elements list from '{selector}': {str(e)}")
            return []

    def wait_for_element(self, selector: str, time: int | float = DEFAULT_WAIT_TIME_MS, frame: Optional[Frame] = None,
                         prev_elem: Optional[Locator] = None, state=None):
        """
        Wait for an element to appear on the page or in a specific frame.
        """
        target = frame or self.page
        if prev_elem:
            if not prev_elem.locator(selector).first.is_visible():
                Exception("No such Element")
        else:
            target.wait_for_selector(selector, timeout=time, state=state)

    def wait_for_element_conditional(self, selector: str,
                                     time: int | float = DEFAULT_WAIT_TIME_MS,
                                     frame: Optional[Frame] = None,
                                     state=None,
                                     prev_elem: Optional[Locator] = None) -> bool:
        """
        Wait for an element to appear on the page or in a specific frame, conditionally based on a previous element.

        Args:
            selector (str): The selector of the target element to wait for.
            time (int | float): Timeout in milliseconds.
            frame (Optional[Frame]): Frame to look for the selector, if applicable.
            state: The state of the element to wait for ('attached', 'visible', etc.).
            prev_elem (Optional[Locator]): Previously located element to check first.

        Returns:
            bool: True if the element appears within the timeout, False otherwise.
        """
        target = frame or self.page
        try:
            if prev_elem:
                result = prev_elem.locator(selector).is_visible()
                return result
            target.wait_for_selector(selector, timeout=time, state=state)
            return True
        except Exception as e:
            self.logger.debug(f"Exception: {e}")
            return False

    def get_element_attribute(self, selector: str, attr: str, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None) -> Optional[str]:
        """
        Retrieve the 'msg' attribute of an element on the page or within a specific frame.

        Args:
            selector (str): The selector for the element.
            frame (Frame, optional): The specific frame to search in. Defaults to the main page.
            prev_elem (Locator, optional): Parent element to search within.

        Returns:
            Optional[str]: The 'msg' attribute value if found, None otherwise.
        """
        target = frame or self.page
        try:
            if prev_elem:
                element = prev_elem.locator(selector)
            else:
                element = target.locator(selector)
            if self.wait_for_element_conditional(selector, frame=frame):
                # get attribute 'msg'
                attr_value = element.get_attribute(attr)
                return attr_value
            else:
                self.logger.debug(f"Element not found or timed out for selector: {selector}")
                return None
        except Exception as e:
            self.logger.debug(f"Error retrieving 'msg' attribute from element '{selector}': {str(e)}")
            return None


    def get_iframe(self, iframe_selector: str, parent_frame: Optional[Frame] = None) -> Frame:
        """
        Returns the iframe element (handles both top-level and nested iframes).
        """
        target = parent_frame or self.page
        iframe_element = target.wait_for_selector(iframe_selector)
        return iframe_element.content_frame()

    def get_nested_iframe(self, selectors: list) -> Frame:
        """
        Traverses nested iframes and returns the innermost Frame.
        """
        current_frame = None
        for selector in selectors:
            current_frame = self.get_iframe(selector, parent_frame=current_frame)
        return current_frame

    def connect_selectors(self, selectors: list, frame: Optional[Frame] = None):
        target = frame or self.page
        for selector in selectors:
            target = target.locator(selector)
        return target

    def click(self, selector: str, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None):
        """
        Click an element on the page or in a specific frame.
        """
        target = prev_elem or frame or self.page
        self.wait_for_element(selector, frame=frame, prev_elem=prev_elem)
        target.click(selector)

    def force_click(self, locator: str, frame: Optional[Frame] = None) -> bool:
        """
        Forces a click on the element by evaluating JavaScript if necessary.

        Args:
            locator (str): The selector for the element to click.
            frame (Frame, optional): The specific frame to perform the click in. Defaults to the main page.

        Returns:
            bool: True if the click is successful, False otherwise.
        """
        target = frame or self.page

        try:
            if self.wait_for_element_conditional(locator, frame=frame):
                element = target.query_selector(locator)
                if element:
                    self.logger.debug(f"Trying to JS (force) click on element: {locator}")

                    # Check if element is interactable (visible and enabled)
                    is_visible = element.is_visible()
                    is_enabled = element.is_enabled()

                    if not is_visible or not is_enabled:
                        self.logger.debug(
                            f"Element found but not interactable (visible: {is_visible}, enabled: {is_enabled}): {locator}")
                        return False

                    # Try force-clicking using JavaScript
                    target.evaluate("element => element.click()", element)
                    self.logger.debug(f"Successfully clicked element: {locator}")
                    return True
                else:
                    self.logger.debug(f"Element not found for locator: {locator}")
                    return False
            else:
                self.logger.debug(f"Element not found or timed out for locator: {locator}")
                return False
        except Exception as e:
            self.logger.debug(f"Unexpected error during force click: {str(e)}")
            return False

    def scroll_and_click(self, selector: str, frame: Optional[Frame] = None):
        """Scrolls to an element and clicks it."""
        self.scroll_page(selector, frame)
        self.move_and_click(selector, frame)

    def scroll_page(self, selector: str, frame: Optional[Frame] = None):
        """Scrolls to the element using JavaScript."""
        if frame:
            # frame.evaluate(f"document.querySelector('{selector}').scrollIntoView()")
            frame.locator(selector).first.scroll_into_view_if_needed()
        else:
            self.page.locator(selector).first.scroll_into_view_if_needed()
            # self.page.evaluate(f"document.querySelector('{selector}').scrollIntoView()")

    def scroll_page_to_end(self):
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def move_and_click(self, selector: str, frame: Optional[Frame] = None):
        self.move_mouse_to(selector, frame)
        self.click(selector, frame)

    def fill_text(self, selector: str, text: str, frame: Optional[Frame] = None):
        """
        Fill a text field on the page or in a specific frame.
        """
        target = frame or self.page
        self.wait_for_element(selector, frame=frame)
        target.fill(selector, text)

    def fill_text_slowly(self, selector: str, text: str, frame: Optional[Frame] = None):
        """
        Fill a text field on the page or in a specific frame, typing slowly like a human.
        """
        target = frame or self.page
        self.wait_for_element(selector, frame=frame)

        target.click(selector)  # Ensure the field is focused
        for char in text:
            target.press(selector, char)
            self.page.wait_for_timeout(random.uniform(50, 150))


    def move_mouse_to(self, selector: str, frame: Optional[Frame] = None):
        """
        Move the mouse pointer to an element on the page or in a specific frame.
        """
        target = frame or self.page
        self.wait_for_element(selector, frame=frame)
        element = target.locator(selector)
        bounding_box = element.bounding_box()
        if bounding_box:
            x = bounding_box["x"] + bounding_box["width"] / 2
            y = bounding_box["y"] + bounding_box["height"] / 2
            self.page.mouse.move(x, y)

    def click_and_fill_text(self, selector: str, text: str, frame: Optional[Frame] = None):
        self.move_mouse_to(selector, frame)
        self.click(selector, frame)
        self.fill_text(selector, text, frame)

    def capture_full_page_screenshot(self, folder: str = "logs/screenshots", file_name: Optional[str] = None,
                                     tag: Optional[str] = None):
        """
        Capture a screenshot of the entire page and save it to a specified folder.

        Args:
            folder (str): The folder where the screenshot will be saved. Defaults to the current directory.
            file_name (Optional[str]): The name of the screenshot file. If not provided, a timestamped name will be used.
        """
        # Ensure the folder exists
        os.makedirs(folder, exist_ok=True)

        # Generate a timestamped filename if none is provided
        if not tag:
            tag = "screenshot"
        if not file_name:
            timestamp = datetime.datetime.now().strftime(f"{LOG_TIME_STRUCTURE}-{tag}.png")
            file_name = timestamp
        elif not file_name.endswith(".png"):
            file_name += ".png"

        # Construct the full path
        file_path = os.path.join(folder, file_name)

        try:
            self.page.screenshot(path=file_path, full_page=True)
            self.logger.debug(f"Full page screenshot saved to {file_path}")
        except Exception as e:
            self.logger.debug(f"Error capturing full page screenshot: {str(e)}")

    def capture_element_screenshot(self, selector: str, folder: str = "logs/screenshots", file_name: Optional[str] = None,
                                   tag: Optional[str] = None, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None):
        """
        Capture a screenshot of a specific element on the page and save it to a specified folder.

        Args:
            element_selector (str): The CSS selector of the element to capture.
            folder (str): The folder where the screenshot will be saved. Defaults to "logs/screenshots".
            file_name (Optional[str]): The name of the screenshot file. If not provided, a timestamped name will be used.
            tag (Optional[str]): A tag to include in the file name.
        """
        os.makedirs(folder, exist_ok=True)
        if not tag:
            tag = "element_screenshot"
        if not file_name:
            timestamp = datetime.datetime.now().strftime(f"{LOG_TIME_STRUCTURE}-{tag}.png")
            file_name = timestamp
        elif not file_name.endswith(".png"):
            file_name += ".png"
        file_path = os.path.join(folder, file_name)
        try:
            element = self.get_element(selector, frame=frame, prev_elem=prev_elem).first
            if not element:
                raise ValueError(f"Element with selector '{selector}' not found.")
            element.screenshot(path=file_path)
            self.logger.info(f"Element screenshot saved to {file_path}")
        except Exception as e:
            self.logger.info(f"Error capturing element screenshot: {str(e)}")

    def get_element_text(self, selector: str, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None) -> \
    Optional[str]:
        """
        Retrieve the text content of an element on the page or within a specific frame.

        Args:
            selector (str): The selector for the element.
            frame (Frame, optional): The specific frame to search in. Defaults to the main page.
            prev_elem (Locator, optional): Parent element to search within.

        Returns:
            Optional[str]: The text content of the element if found, None otherwise.
        """
        target = frame or self.page
        try:
            if prev_elem:
                element = prev_elem.locator(selector)
            else:
                element = target.locator(selector)
            if self.wait_for_element_conditional(selector, frame=frame):
                return element.inner_text().strip()
            else:
                self.logger.debug(f"Element not found or timed out for selector: {selector}")
                return None
        except Exception as e:
            self.logger.debug(f"Error retrieving text from element '{selector}': {str(e)}")
            return None

    def remove_element_from_dom(self, selector: str, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None):
        target = prev_elem or frame or self.page
        self.logger.debug(f"Removing DOM element: {selector}")
        target.evaluate(f"""document.querySelector('{selector}').style.display = 'none';""")

    def restore_element_from_dom(self, selector: str, frame: Optional[Frame] = None, prev_elem: Optional[Locator] = None):
        target = prev_elem or frame or self.page
        self.logger.debug(f"Restoring DOM element: {selector}")
        target.evaluate(f"""document.querySelector('{selector}').style.display = '';""")

    def intercept_request_data_json(self, request_path, timeout=DEFAULT_WAIT_TIME_MS):
        try:
            with self.page.expect_request(request_path, timeout=timeout) as request_info:
                request = request_info.value
                return request.post_data_json
        except Exception as e:
            raise Exception(f"No response captured for {request_path}: {e}")

    def get_current_scroll_position(self):
        """Get the current vertical scroll position."""
        return self.page.evaluate("window.scrollY")

    def get_closest_element(self, locator_selector):
        """Find the element closest to the current scroll position."""
        current_scroll = self.get_current_scroll_position()

        elements = self.page.query_selector_all(locator_selector)
        closest_element = None
        closest_distance = float('inf')

        for element in elements:
            bounding_box = element.bounding_box()

            if bounding_box:
                element_top = bounding_box['y']
                distance = abs(element_top - current_scroll)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_element = element

        return closest_element

    def click_enter(self, selector: Optional[str] = None, frame: Optional[Frame] = None, delay: Optional[int] = None):
        """
        Press the Enter key on the page or on a specific element.

        Args:
            selector (Optional[str]): The selector for the element to focus before pressing Enter.
                                      If None, presses Enter on the active element.
            frame (Optional[Frame]): Specific frame context, if applicable.
            delay (Optional[int]): Optional delay in milliseconds after pressing Enter.
        """
        target = frame or self.page
        try:
            if selector:
                # Ensure the element exists and is focused
                self.wait_for_element(selector, frame=frame)
                target.click(selector)
                self.logger.debug(f"Focused element {selector} before pressing Enter")

            # Press Enter
            target.keyboard.press("Enter")
            self.logger.debug("Pressed Enter key")

            if delay:
                self.page.wait_for_timeout(delay)
        except Exception as e:
            self.logger.debug(f"Error pressing Enter: {str(e)}")
