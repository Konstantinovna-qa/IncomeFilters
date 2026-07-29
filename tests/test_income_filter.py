import pytest

from tests.pages.vacancy_search_page import (
    FLY_IN_FLY_OUT,
    HOUR,
    MONTH,
    SERVICE,
    SHIFT,
    VacancySearchPage,
)


def test_income_filter_form_contains_all_salary_periods(driver):
    """Форма дохода показывает все поддерживаемые периоды и основные элементы."""
    # Создаём Page Object, открываем поиск вакансий и форму фильтра дохода.
    page = VacancySearchPage(driver).open().open_income_filter()

    # Проверяем, что в форме доступны все пять периодов расчёта дохода.
    assert page.visible_periods() == [
        MONTH.query_value,  # За месяц.
        SHIFT.query_value,  # За смену.
        HOUR.query_value,  # За час.
        FLY_IN_FLY_OUT.query_value,  # За вахту.
        SERVICE.query_value,  # За услугу.
    ]
    # Проверяем, что в поле минимального дохода можно вводить значение.
    assert driver.find_element(*page.MIN_SALARY_INPUT).is_enabled()
    # Проверяем видимость элемента управления «Указан доход».
    assert driver.find_element(*page.ONLY_WITH_SALARY_CONTROL).is_displayed()
    # Проверяем, что кнопка применения фильтра доступна.
    assert driver.find_element(*page.APPLY_BUTTON).is_enabled()


def test_minimum_monthly_salary_and_only_with_salary_are_applied(driver):
    """Минимальная месячная зарплата и флаг дохода передаются в поиск."""
    # Создаём Page Object, открываем поиск вакансий и форму фильтра дохода.
    page = VacancySearchPage(driver).open().open_income_filter()

    # Настраиваем фильтр и сохраняем параметры сформированного поискового URL.
    query = (
        page.set_minimum_salary(100_000)  # Вводим минимальный доход 100 000 рублей.
        .choose_period(MONTH)  # Выбираем расчёт дохода за месяц.
        .enable_only_with_salary()  # Включаем только вакансии с указанным доходом.
        .apply()  # Применяем настройки фильтра.
        .selected_query()  # Преобразуем параметры текущего URL в словарь.
    )

    # Проверяем передачу введённой суммы без разделителей разрядов.
    assert query["salary"] == ["100000"]
    # Проверяем передачу выбранного периода «за месяц».
    assert query["salary_mode"] == ["MONTH"]
    # Проверяем передачу включённого флажка «Указан доход».
    assert query["label"] == ["with_salary"]


# Запускаем один сценарий для двух периодов: «за час» и «за смену».
@pytest.mark.parametrize("period", [HOUR, SHIFT])
def test_selected_salary_period_is_sent_in_search_request(driver, period):
    """Выбранный период дохода передаётся в параметре salary_mode."""
    # Создаём Page Object, открываем поиск вакансий и форму фильтра дохода.
    page = VacancySearchPage(driver).open().open_income_filter()

    # Настраиваем фильтр и сохраняем параметры сформированного поискового URL.
    query = (
        page.set_minimum_salary(1_000)  # Вводим минимальный доход 1 000 рублей.
        .choose_period(period)  # Выбираем период, переданный параметризацией.
        .apply()  # Применяем настройки фильтра.
        .selected_query()  # Преобразуем параметры текущего URL в словарь.
    )

    # Проверяем передачу введённой суммы.
    assert query["salary"] == ["1000"]
    # Проверяем, что URL содержит период, переданный в текущий запуск теста.
    assert query["salary_mode"] == [period.query_value]
