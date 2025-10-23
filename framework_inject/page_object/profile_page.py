import random

from framework_inject.base.base_page import BasePage
from framework_inject.constants import DEFAULT_WAIT_TIME_SEC, SECOND
from framework_inject.utils.time_util import wait_time, wait_random_time


class ProfilePage(BasePage):
    def __init__(self, logger=__file__, id=0):
        super().__init__(logger, id=id)
        self.SELECTORS = {
            "MESSAGE_BUTTON": "//div[contains(@class, 'profile-outer-card')]/section//button[contains(text(), 'Message')]",
            "DIALOG_IFRAME": "//div[@role='dialog']//iframe",
            "PLACEHOLDER_TEXT": '//*[@id="__layout"]//p[@data-placeholder]',
            "INPUT_DIV": "//div[@contenteditable]",
            "SEND_MESSAGE_BUTTON": '//button[@data-cy="send-message"]'
        }

    def open_profile_page(self, profile_url):
        self.goto(profile_url)

    def open_messanger(self):
        self.wait_for_element(self.SELECTORS["MESSAGE_BUTTON"])
        self.click(self.SELECTORS["MESSAGE_BUTTON"])

    def write_and_send_message(self, message):
        self.wait_for_element(self.SELECTORS["DIALOG_IFRAME"], time=SECOND * 15)
        iframe = self.get_iframe(self.SELECTORS["DIALOG_IFRAME"])
        self.wait_for_element(self.SELECTORS["PLACEHOLDER_TEXT"], frame=iframe)
        self.click_and_fill_text(self.SELECTORS["PLACEHOLDER_TEXT"], message, frame=iframe)

    def confirm_send_message(self):
        self.click_enter()

    def prepare_and_write_message(self, text):
        if self.wait_for_element_conditional(self.SELECTORS["MESSAGE_CONTAINER_NO_BUTTON"], time=2000):
            self.click(self.SELECTORS["MESSAGE_CONTAINER_NO_BUTTON"])
        self.wait_for_element(self.SELECTORS["MESSAGE_CONTAINER_TEXTAREA"])
        self.click_and_fill_text(self.SELECTORS["MESSAGE_CONTAINER_TEXTAREA"], text)

    def send_message(self):
        self.click(self.SELECTORS["SEND_MESSAGE_BUTTON"])
        self.wait_for_element(self.SELECTORS["MESSAGE_SENT_CONFIRMATION"])