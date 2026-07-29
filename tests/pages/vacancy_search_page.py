# Откладывает вычисление аннотаций типов, поэтому можно ссылаться на класс в его методах.
from __future__ import annotations

# Импортирует декоратор для создания неизменяемого класса данных.
from dataclasses import dataclass
# Импортирует тип для констант, которые не должны переназначаться.
from typing import Final
# Импортирует функции для разбора параметров URL поисковой страницы.
from urllib.parse import parse_qs, urlparse

# Импортирует исключение Selenium при превышении времени ожидания.
from selenium.common.exceptions import TimeoutException
# Импортирует способы поиска элементов на веб-странице: CSS и XPath.
from selenium.webdriver.common.by import By
# Импортирует тип объекта, управляющего браузером Chrome.
from selenium.webdriver.remote.webdriver import WebDriver
# Импортирует готовые условия Selenium для ожидания элементов.
from selenium.webdriver.support import expected_conditions as ec
# Импортирует класс явного ожидания Selenium.
from selenium.webdriver.support.ui import WebDriverWait


# Создаёт класс данных с автоматически сгенерированным конструктором.
# frozen=True запрещает изменить период после его создания.
@dataclass(frozen=True)
class SalaryPeriod:
    """Период, в котором hh.ru интерпретирует указанную сумму дохода."""

    # Хранит значение, которое hh.ru ожидает получить в параметре salary_mode.
    query_value: str


# Описывает период «за месяц».
MONTH: Final = SalaryPeriod("MONTH")
# Описывает период «за смену».
SHIFT: Final = SalaryPeriod("SHIFT")
# Описывает период «за час».
HOUR: Final = SalaryPeriod("HOUR")
# Описывает период «за вахту».
FLY_IN_FLY_OUT: Final = SalaryPeriod("FLY_IN_FLY_OUT")
# Описывает период «за услугу».
SERVICE: Final = SalaryPeriod("SERVICE")


class VacancySearchPage:
    """Управляет страницей поиска вакансий и формой «Уровень дохода»."""

    # Адрес страницы поиска вакансий, на которой находится тестируемый фильтр.
    URL: Final = "https://hh.ru/search/vacancy"
    # Максимальное время ожидания элементов страницы в секундах.
    WAIT_SECONDS: Final = 15

    # Локатор кнопки-чипа «Уровень дохода», открывающей форму фильтра.
    INCOME_CHIP = (By.CSS_SELECTOR, '[data-qa="search-filter-compensation_per_mode-chip"]')
    # Локатор поля для ввода минимального дохода.
    MIN_SALARY_INPUT = (By.CSS_SELECTOR, '[data-qa="search-filter-compensation-input"]')
    # Локатор скрытого HTML-флажка «Указан доход».
    ONLY_WITH_SALARY = (By.CSS_SELECTOR, '[data-qa="search-filter-value-with_salary"]')
    # Локатор видимой метки флажка, по которой пользователь может кликнуть.
    ONLY_WITH_SALARY_CONTROL = (
        # Выбираем элемент label, который содержит флажок с указанным data-qa.
        By.XPATH,
        '//input[@data-qa="search-filter-value-with_salary"]/ancestor::label',
    )
    # Локатор кнопки «Сохранить», применяющей параметры дохода.
    APPLY_BUTTON = (
        By.CSS_SELECTOR,
        '[data-qa="search-filter-compensation_per_mode-apply-button"]',
    )

    def __init__(self, driver: WebDriver) -> None:
        """Сохраняет драйвер Selenium и создаёт явное ожидание элементов."""
        # Сохраняем переданный браузер для выполнения действий на странице.
        self.driver = driver
        # Создаём объект ожидания с общим тайм-аутом для всех методов класса.
        self.wait = WebDriverWait(driver, self.WAIT_SECONDS)

    def open(self) -> "VacancySearchPage":
        """Открывает страницу поиска и закрывает необязательные стартовые диалоги."""
        # Переходим в браузере на адрес страницы поиска вакансий.
        self.driver.get(self.URL)
        # Закрываем cookie-баннер и подтверждение региона, если они перекрывают страницу.
        self._close_optional_popups()
        # Ждём, пока кнопка фильтра дохода станет доступной для нажатия.
        self.wait.until(ec.element_to_be_clickable(self.INCOME_CHIP))
        # Возвращаем текущий объект, чтобы методы можно было вызывать цепочкой.
        return self

    def open_income_filter(self) -> "VacancySearchPage":
        """Открывает всплывающую форму настройки минимального дохода."""
        # Ждём доступности кнопки фильтра и нажимаем её.
        self.wait.until(ec.element_to_be_clickable(self.INCOME_CHIP)).click()
        # Ждём появления поля суммы: оно подтверждает, что форма открылась.
        self.wait.until(ec.visibility_of_element_located(self.MIN_SALARY_INPUT))
        # Возвращаем текущий объект для цепочки вызовов.
        return self

    def set_minimum_salary(self, amount: int) -> "VacancySearchPage":
        """Вводит минимальный доход без разделителей разрядов."""
        # Находим видимое поле суммы и ждём его появления.
        field = self.wait.until(ec.visibility_of_element_located(self.MIN_SALARY_INPUT))
        # Удаляем значение, если оно было введено ранее.
        field.clear()
        # Преобразуем целое число в строку и вводим её в поле.
        field.send_keys(str(amount))
        # Возвращаем текущий объект для цепочки вызовов.
        return self

    def choose_period(self, period: SalaryPeriod) -> "VacancySearchPage":
        """Выбирает период выплаты: месяц, смена, час, вахта или услуга."""
        # Формируем CSS-локатор radio-кнопки с кодом переданного периода.
        radio = (
            By.CSS_SELECTOR,
            f'[data-qa="search-filter-compensation_mode-value-{period.query_value}"]',
        )
        # Ждём появления radio-кнопки, находим её родительскую метку label и нажимаем её.
        # Нажатие на label надёжнее, чем на скрытый нативный элемент input.
        self.wait.until(ec.presence_of_element_located(radio)).find_element(
            By.XPATH, ".."
        ).click()
        # Возвращаем текущий объект для цепочки вызовов.
        return self

    def enable_only_with_salary(self) -> "VacancySearchPage":
        """Включает показ вакансий, в которых работодатель указал доход."""
        # Ждём появления флажка и сохраняем его, чтобы проверить текущее состояние.
        checkbox = self.wait.until(ec.presence_of_element_located(self.ONLY_WITH_SALARY))
        # Выполняем действие только если флажок ещё не включён.
        if not checkbox.is_selected():
            # Нажимаем на видимую метку флажка, а не на скрытый HTML input.
            self.wait.until(ec.element_to_be_clickable(self.ONLY_WITH_SALARY_CONTROL)).click()
            # Ждём, пока Selenium подтвердит, что флажок стал включённым.
            self.wait.until(lambda driver: checkbox.is_selected())
        # Возвращаем текущий объект для цепочки вызовов.
        return self

    def apply(self) -> "VacancySearchPage":
        """Применяет фильтр и ждёт появления суммы дохода в URL поиска."""
        # Ждём доступности кнопки сохранения и нажимаем её.
        self.wait.until(ec.element_to_be_clickable(self.APPLY_BUTTON)).click()
        # Ждём обновления URL: параметр salary означает, что сумма была применена.
        self.wait.until(lambda driver: "salary=" in driver.current_url)
        # Возвращаем текущий объект для цепочки вызовов.
        return self

    def selected_query(self) -> dict[str, list[str]]:
        """Возвращает параметры текущего поискового URL в виде словаря."""
        # Берём URL браузера, выделяем строку параметров и разбираем её в словарь.
        return parse_qs(urlparse(self.driver.current_url).query)

    def visible_periods(self) -> list[str]:
        """Возвращает коды периодов, доступные пользователю в открытой форме."""
        # Формируем список кодов только для периодов с видимыми метками на странице.
        return [
            # Добавляем в результат код периода, например MONTH или HOUR.
            period.query_value
            # По очереди проверяем все поддерживаемые периоды дохода.
            for period in (MONTH, SHIFT, HOUR, FLY_IN_FLY_OUT, SERVICE)
            # Находим radio-кнопку периода по её устойчивому data-qa-атрибуту.
            if self.driver.find_element(
                By.CSS_SELECTOR,
                f'[data-qa="search-filter-compensation_mode-value-{period.query_value}"]',
            )
            # Переходим к родительской метке label, которую видит пользователь.
            .find_element(By.XPATH, "..")
            # Оставляем период, только если его метка отображается на экране.
            .is_displayed()
        ]

    def _close_optional_popups(self) -> None:
        """Закрывает cookie-баннер и подтверждение региона, если они появились."""
        # Перебираем локаторы двух необязательных диалогов стартовой страницы.
        for locator in (
            # Кнопка закрытия баннера cookie.
            (By.XPATH, '//button[normalize-space()="Понятно"]'),
            # Кнопка подтверждения автоматически определённого региона.
            (By.XPATH, '//button[normalize-space()="Да, верно"]'),
        ):
            try:
                # Даём диалогу до двух секунд на появление и нажимаем его кнопку.
                WebDriverWait(self.driver, 2).until(ec.element_to_be_clickable(locator)).click()
            except TimeoutException:
                # Если диалог не появился, ничего не делаем и проверяем следующий.
                pass
