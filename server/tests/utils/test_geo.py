import pytest
from app.utils.geo import haversine_km


def test_same_coordinate_returns_zero():
    result = haversine_km(37.5663, 126.9779, 37.5663, 126.9779)
    assert result == 0.0


def test_seoul_city_hall_to_gangnam_station():
    result = haversine_km(37.5663, 126.9779, 37.4979, 127.0276)
    assert abs(result - 8.5) <= 0.5


def test_symmetry():
    a_lat, a_lng = 37.5663, 126.9779
    b_lat, b_lng = 37.4979, 127.0276
    assert haversine_km(a_lat, a_lng, b_lat, b_lng) == haversine_km(b_lat, b_lng, a_lat, a_lng)
