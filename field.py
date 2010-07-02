#!/usr/bin/env python
#vim:fileencoding=utf-8

from collections import deque

class Direction(object):
    def __init__(self, distance, nelement):
        self.distance = distance
        self.nelement = nelement

class Edge(object):
    def __init__(self, begin, end, score):
        self.begin = begin
        self.end = end
        self.score = score

def build_right_angle_dir_field(graph, exits):
    queue = deque()
    field = {}
    for e in exits:
        field[e] = Direction(0, None)
        queue.append(e)
    while queue:
        curpoint = queue.popleft()
        curdistance = field[curpoint].distance
        for edge in graph.in_edges(pos):
            if edge.score != 1:
                raise ValueError, "Not all of edges has score=1"
            npoint = edge.begin
            if npoint not in field:
                field[npoint] = Direction(curdistance + 1, curpoint)
                queue.append(npoint)
            else:
                assert field[npoint].distance <= curdistance
    return field
