"""Unit tests for dependency-free geometry helpers."""
from geospatial import geometry


SQUARE = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]


def test_point_in_ring_inside_and_outside():
    assert geometry.point_in_ring((0.5, 0.5), SQUARE)
    assert not geometry.point_in_ring((1.5, 0.5), SQUARE)
    assert not geometry.point_in_ring((-0.1, 0.5), SQUARE)


def test_segments_intersect():
    assert geometry.segments_intersect((0, 0), (2, 2), (0, 2), (2, 0))
    assert not geometry.segments_intersect((0, 0), (1, 0), (0, 1), (1, 1))


def test_line_intersects_ring():
    crossing = [(0.5, -1.0), (0.5, 2.0)]
    outside = [(2.0, 2.0), (3.0, 3.0)]
    assert geometry.line_intersects_ring(crossing, SQUARE)
    assert not geometry.line_intersects_ring(outside, SQUARE)


def test_area_positive():
    assert geometry.shoelace_area_km2(SQUARE, center_lat=28.0) > 0
