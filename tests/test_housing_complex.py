import pytest
from loguru import logger
from typing import Tuple, Set

from housing_complex.complex_factory import ComplexFactory
from house_graph.house import House

TEST_ITERATIONS = 5
HOUSE_SPACING = 50.0
COLLISION_TOLERANCE = 0.01


def get_node_key(node):
    f = node.features
    return (round(f.get("x", 0), 6), round(f.get("y", 0), 6), round(f.get("z", 0), 6))


def get_house_bbox(house: House):
    if not house.nodes:
        return (0, 0, 0, 0, 0, 0)
    xs = [n.features.get("x", 0) for n in house.nodes]
    ys = [n.features.get("y", 0) for n in house.nodes]
    zs = [n.features.get("z", 0) for n in house.nodes]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def houses_overlap(bbox1, bbox2) -> bool:
    min1x, max1x, min1y, max1y, min1z, max1z = bbox1
    min2x, max2x, min2y, max2y, min2z, max2z = bbox2
    return not (
        max1x + COLLISION_TOLERANCE < min2x or
        max2x + COLLISION_TOLERANCE < min1x or
        max1y + COLLISION_TOLERANCE < min2y or
        max2y + COLLISION_TOLERANCE < min1y or
        max1z + COLLISION_TOLERANCE < min2z or
        max2z + COLLISION_TOLERANCE < min1z
    )


def check_complex_collisions(complex_obj, iteration: int):
    all_positions: Set[Tuple] = set()
    house_bboxes = []

    for h_idx, house in enumerate(complex_obj.houses):
        bbox = get_house_bbox(house)
        house_bboxes.append((h_idx, bbox))

        for node in house.nodes:
            key = get_node_key(node)
            if key in all_positions:
                raise ValueError(f"COLLISION (iteration {iteration}): Node position {key} already exists!")
            all_positions.add(key)

    for i in range(len(house_bboxes)):
        for j in range(i + 1, len(house_bboxes)):
            h1_idx, bbox1 = house_bboxes[i]
            h2_idx, bbox2 = house_bboxes[j]
            if houses_overlap(bbox1, bbox2):
                logger.warning(f"OVERLAP (iteration {iteration}): House {h1_idx} and House {h2_idx}")


@pytest.mark.parametrize("houses_x,houses_y", [(1,1), (2,2), (3,2), (4,3), (5,3)])
def test_complex_generation_no_collisions(houses_x: int, houses_y: int):
    collisions_found = 0
    logger.info(f"Testing grid {houses_x}x{houses_y} — {TEST_ITERATIONS} iterations")

    for i in range(TEST_ITERATIONS):
        try:
            complex_obj = ComplexFactory.build(houses_x=houses_x, houses_y=houses_y)
            check_complex_collisions(complex_obj, i)
        except Exception as e:
            collisions_found += 1
            logger.error(f"Collision in iteration {i}: {e}")

    if collisions_found > 0:
        pytest.fail(f"Found {collisions_found} collisions!")
    else:
        logger.success(f"✓ No collisions for {houses_x}x{houses_y} grid")