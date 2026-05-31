from app.constants.median_income import (
    HOUSEHOLD_TYPE_TO_SIZE,
    MEDIAN_INCOME_60_BY_HOUSEHOLD,
)


def test_median_income_60_is_dict_with_all_household_sizes():
    assert isinstance(MEDIAN_INCOME_60_BY_HOUSEHOLD, dict)
    assert set(MEDIAN_INCOME_60_BY_HOUSEHOLD.keys()) == {1, 2, 3, 4, 5, 6}


def test_median_income_60_all_values_positive_int():
    for size, value in MEDIAN_INCOME_60_BY_HOUSEHOLD.items():
        assert isinstance(value, int), f"키 {size}: int여야 함, 실제 {type(value)}"
        assert value > 0, f"키 {size}: 양의 정수여야 함, 실제 {value}"


def test_household_type_to_size_is_dict_with_exactly_four_keys():
    expected_keys = {"1인 가구", "청년 부부", "예비 신혼", "한부모"}
    assert set(HOUSEHOLD_TYPE_TO_SIZE.keys()) == expected_keys
    assert len(HOUSEHOLD_TYPE_TO_SIZE) == 4


def test_household_type_to_size_hanbumo_is_2():
    assert HOUSEHOLD_TYPE_TO_SIZE["한부모"] == 2


def test_household_type_to_size_single_is_1():
    assert HOUSEHOLD_TYPE_TO_SIZE["1인 가구"] == 1
