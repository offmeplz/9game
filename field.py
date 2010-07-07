#!/usr/bin/env python
#vim:fileencoding=utf-8

from collections import deque
from heapq import heappush, heappop

class Direction(object):
    def __init__(self, distance, next_vertex):
        self.distance = distance
        self.next_vertex = next_vertex
        self.next_waypoint = None

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
        for edge in graph.in_edges(curpoint):
            if edge.score != 1:
                raise ValueError, "Not all of edges has score=1"
            npoint = edge.begin
            if npoint not in field:
                field[npoint] = Direction(curdistance + 1, curpoint)
                queue.append(npoint)
            else:
                assert field[npoint].distance <= curdistance + 1
    return field

def build_dir_field(graph, exits):
    priority_queue = []
    field = {}
    for e in exits:
        field[e] = Direction(0, None)
        heappush(priority_queue, (0, e))

    while priority_queue:
        curdist, curpoint = heappop(priority_queue)
        for edge in graph.in_edges(curpoint):
            npoint = edge.begin
            edgedist = edge.score
            ndist = curdist + edgedist
            if npoint not in field or field[npoint].distance > ndist:
                field[npoint] = Direction(ndist, curpoint)
                heappush(priority_queue, (ndist, npoint))
    return field
