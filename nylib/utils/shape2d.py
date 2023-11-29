import math

import glm

pi2 = math.pi * 2
pi_2 = math.pi / 2


def is_rad_in_range(rad: float, start_rad: float, end_rad: float):
    start_rad_ = start_rad % pi2
    end_rad_ = end_rad - (start_rad - start_rad_)
    rad %= pi2
    if start_rad_ < end_rad_:
        return start_rad_ <= rad <= end_rad_
    else:
        return rad >= start_rad_ or rad <= end_rad_


def is_point_in_circle(point: glm.vec2, center: glm.vec2, radius: float):
    return glm.distance(point, center) <= radius


def is_point_in_rect(point: glm.vec2, rect_points: list[glm.vec2] | tuple[glm.vec2, ...]):
    assert len(rect_points) == 4
    p1, p2, p3, p4 = rect_points
    if glm.dot(point - p4, p4 - p1) > 0: return False
    if glm.dot(point - p1, p1 - p2) > 0: return False
    if glm.dot(point - p2, p2 - p3) > 0: return False
    if glm.dot(point - p3, p3 - p4) > 0: return False
    return True


def is_point_in_sector(point: glm.vec2, center: glm.vec2, radius: float, start_rad: float, end_rad: float):
    return is_point_in_circle(point, center, radius) and is_rad_in_range(glm.atan(*(point - center)), start_rad, end_rad)


def is_point_on_line(point: glm.vec2, line_start: glm.vec2, line_end: glm.vec2):
    v_se = line_end - line_start
    line_len = glm.length(v_se)
    return 0 <= glm.dot(point - line_start, v_se) / line_len <= line_len


def is_point_in_poly(point: glm.vec2, polygon_points: list[glm.vec2] | tuple[glm.vec2, ...]):
    if len(polygon_points) < 3: return False
    cnt = 0
    for i in range(len(polygon_points)):
        p1 = polygon_points[i]
        p2 = polygon_points[(i + 1) % len(polygon_points)]
        if is_point_on_line(point, p1, p2): return True
        if p1.y == p2.y: continue
        if min(p1.y, p2.y) <= point.y <= max(p1.y, p2.y) and point.x <= max(p1.x, p2.x):
            if p1.x == p2.x:
                cnt += 1
            elif (point.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x >= point.x:
                cnt += 1
    return cnt % 2 == 1


def is_circle_intersect_line(
        circle_center: glm.vec2, circle_radius: float,
        line_start: glm.vec2, line_end: glm.vec2
):
    if is_point_in_circle(line_start, circle_center, circle_radius): return True
    if is_point_in_circle(line_end, circle_center, circle_radius): return True

    v_se = line_end - line_start
    line_len = glm.length(v_se)
    proj_len = glm.dot(circle_center - line_start, v_se) / line_len
    return 0 <= proj_len <= line_len


def is_circle_intersect_circle(center1: glm.vec2, radius1: float, center2: glm.vec2, radius2: float):
    return glm.distance(center1, center2) <= radius1 + radius2


def is_circle_intersect_sector(
        circle_center: glm.vec2, circle_radius: float,
        sector_center: glm.vec2, sector_radius: float, sector_start_rad: float, sector_end_rad: float
):
    if not is_circle_intersect_circle(circle_center, circle_radius, sector_center, sector_radius): return False
    if is_rad_in_range(glm.atan(*(circle_center - sector_center)), sector_start_rad, sector_end_rad): return True
    sector_start = sector_center + glm.vec2(math.cos(sector_start_rad), math.sin(sector_start_rad)) * sector_radius
    if is_circle_intersect_line(circle_center, circle_radius, sector_center, sector_start): return True
    sector_end = sector_center + glm.vec2(math.cos(sector_end_rad), math.sin(sector_end_rad)) * sector_radius
    if is_circle_intersect_line(circle_center, circle_radius, sector_center, sector_end): return True
    return False


def is_circle_intersect_rect(
        circle_center: glm.vec2, circle_radius: float,
        rect_points: list[glm.vec2] | tuple[glm.vec2, ...]
):
    assert len(rect_points) == 4
    return is_point_in_rect(circle_center, rect_points) or any(is_point_in_circle(p, circle_center, circle_radius) for p in rect_points)
