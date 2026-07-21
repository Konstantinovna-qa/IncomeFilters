from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from urllib.parse import parse_qs, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@dataclass(frozen=True)
class SalaryPeriod:
    """Период, в котором hh.ru интерпретирует указанную сумму дохода."""

    query_value: str


MONTH: Final = SalaryPeriod("MONTH")
SHIFT: Final = SalaryPeriod("SHIFT")
HOUR: Final = SalaryPeriod("HOUR")
FLY_IN_FLY_OUT: Final = SalaryPeriod("FLY_IN_FLY_OUT")
SERVICE: Final = SalaryPeriod("SERVICE")


class VacancySearchPage:
    """Управляет страницей поиска вакансий и формой «Уровень дохода»."""

    URL: Final = "https://hh.ru/search/vacancy"
    WAIT_SECONDS: Final = 15

    INCOME_CHIP = (By.CSS_SELECTOR, '[data-qa="search-filter-compensation_per_mode-chip"]')
    MIN_SALARY_INPUT = (By.CSS_SELECTOR, '[data-qa="search-filter-compensation-input"]')
    ONLY_WITH_SALARY = (By.CSS_SELECTOR, '[data-qa="search-filter-value-with_salary"]')
    ONLY_WITH_SALARY_CONTROL = (
        By.XPATH,
        '//input[@data-qa="search-filter-value-with_salary"]/ancestor::label',
    )
    APPLY_BUTTON = (
        By.CSS_SELECTOR,
        '[data-qa="search-filter-compensation_per_mode-apply-button"]',
    )

    def __init__(self, driver: WebDriver) -> None:
        """Сохраняет драйвер Selenium и создаёт явное ожидание элементов."""
        self.driver = driver
        self.wait = WebDriverWait(driver, self.WAIT_SECONDS)

    def open(self) -> "VacancySearchPage":
        """Открывает страницу поиска и закрывает необязательные стартовые диалоги."""
        self.driver.get(self.URL)
        self._close_optional_popups()
        self.wait.until(ec.element_to_be_clickable(self.INCOME_CHIP))
        return self

    def open_income_filter(self) -> "VacancySearchPage":
        """Открывает всплывающую форму настройки минимального дохода."""
        self.wait.until(ec.element_to_be_clickable(self.INCOME_CHIP)).click()
        self.wait.until(ec.visibility_of_element_located(self.MIN_SALARY_INPUT))
        return self

    def set_minimum_salary(self, amount: int) -> "VacancySearchPage":
        """Вводит минимальный доход без разделителей разрядов."""
        field = self.wait.until(ec.visibility_of_element_located(self.MIN_SALARY_INPUT))
        field.clear()
        field.send_keys(str(amount))
        return self

    def choose_period(self, period: SalaryPeriod) -> "VacancySearchPage":
        """Выбирает период выплаты: месяц, смена, час, вахта или услуга."""
        radio = (
            By.CSS_SELECTOR,
            f'[data-qa="search-filter-compensation_mode-value-{period.query_value}"]',
        )
        self.wait.until(ec.presence_of_element_located(radio)).find_element(
            By.XPATH, ".."
        ).click()
        return self

    def enable_only_with_salary(self) -> "VacancySearchPage":
        """Включает показ вакансий, в которых работодатель указал доход."""
        checkbox = self.wait.until(ec.presence_of_element_located(self.ONLY_WITH_SALARY))
        if not checkbox.is_selected():
            self.wait.until(ec.element_to_be_clickable(self.ONLY_WITH_SALARY_CONTROL)).click()
            self.wait.until(lambda driver: checkbox.is_selected())
        return self

    def apply(self) -> "VacancySearchPage":
        """Применяет фильтр и ждёт появления суммы дохода в URL поиска."""
        self.wait.until(ec.element_to_be_clickable(self.APPLY_BUTTON)).click()
        self.wait.until(lambda driver: "salary=" in driver.current_url)
        return self

    def selected_query(self) -> dict[str, list[str]]:
        """Возвращает параметры текущего поискового URL в виде словаря."""
        return parse_qs(urlparse(self.driver.current_url).query)

    def visible_periods(self) -> list[str]:
        """Возвращает коды периодов, доступные пользователю в открытой форме."""
        return [
            period.query_value
            for period in (MONTH, SHIFT, HOUR, FLY_IN_FLY_OUT, SERVICE)
            if self.driver.find_element(
                By.CSS_SELECTOR,
                f'[data-qa="search-filter-compensation_mode-value-{period.query_value}"]',
            )
            .find_element(By.XPATH, "..")
            .is_displayed()
        ]

    def _close_optional_popups(self) -> None:
        """Закрывает cookie-баннер и подтверждение региона, если они появились."""
        for locator in (
            (By.XPATH, '//button[normalize-space()="Понятно"]'),
            (By.XPATH, '//button[normalize-space()="Да, верно"]'),
        ):
            try:
                WebDriverWait(self.driver, 2).until(ec.element_to_be_clickable(locator)).click()
            except TimeoutException:
                pass
