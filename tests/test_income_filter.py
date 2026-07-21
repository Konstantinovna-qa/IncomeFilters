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
    page = VacancySearchPage(driver).open().open_income_filter()

    assert page.visible_periods() == [
        MONTH.query_value,
        SHIFT.query_value,
        HOUR.query_value,
        FLY_IN_FLY_OUT.query_value,
        SERVICE.query_value,
    ]
    assert driver.find_element(*page.MIN_SALARY_INPUT).is_enabled()
    assert driver.find_element(*page.ONLY_WITH_SALARY_CONTROL).is_displayed()
    assert driver.find_element(*page.APPLY_BUTTON).is_enabled()


def test_minimum_monthly_salary_and_only_with_salary_are_applied(driver):
    """Минимальная месячная зарплата и флаг дохода передаются в поиск."""
    page = VacancySearchPage(driver).open().open_income_filter()

    query = (
        page.set_minimum_salary(100_000)
        .choose_period(MONTH)
        .enable_only_with_salary()
        .apply()
        .selected_query()
    )

    assert query["salary"] == ["100000"]
    assert query["salary_mode"] == ["MONTH"]
    assert query["label"] == ["with_salary"]


@pytest.mark.parametrize("period", [HOUR, SHIFT])
def test_selected_salary_period_is_sent_in_search_request(driver, period):
    """Выбранный период дохода передаётся в параметре salary_mode."""
    page = VacancySearchPage(driver).open().open_income_filter()

    query = page.set_minimum_salary(1_000).choose_period(period).apply().selected_query()

    assert query["salary"] == ["1000"]
    assert query["salary_mode"] == [period.query_value]
