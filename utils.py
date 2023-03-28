import math
from datetime import datetime, timedelta

import numpy as np
from numpy.linalg import norm


def createHeatmapData(pipe_lat, pipe_long, wind_direction, wind_speed):
    data = []
    iterations = 10
    step = 0.009
    added_points = []
    spread_deg = 13
    wind_direction += spread_deg/2
    data.append([[pipe_lat, pipe_long]])

    for iteration in range(iterations):
        last_points = data[-1].copy()
        new_points = []
        if len(last_points) == 1:
        
            new_points.extend([[last_points[0][0] + step * math.cos(math.radians(wind_direction)),
                                last_points[0][1] + step * math.sin(math.radians(wind_direction))],
                               [last_points[0][0] + step * math.cos(math.radians(wind_direction + spread_deg)),
                                last_points[0][1] + step * math.sin(math.radians(wind_direction + spread_deg))],
                               [last_points[0][0] + step * 0.9 * math.cos(math.radians(wind_direction - spread_deg)),
                                last_points[0][1] + step * 0.9 * math.sin(math.radians(wind_direction - spread_deg))]])
            added_points = new_points.copy()
        else:
            prev_points = last_points.copy()
            
            last_points = added_points.copy()

            new_points.extend(prev_points)
            
            new_points.append([last_points[0][0] + step * math.cos(math.radians(wind_direction + spread_deg)),
                               last_points[0][1] + step * math.sin(math.radians(wind_direction + spread_deg))])
            new_points.extend([[point[0] + step * math.cos(math.radians(wind_direction)),
                               point[1] + step * math.sin(math.radians(wind_direction))] for point in last_points])
            
            new_points.append([last_points[-1][0] + step * 0.9 * math.cos(math.radians(wind_direction - spread_deg)),
                               last_points[-1][1] + step * 0.9 * math.sin(math.radians(wind_direction - spread_deg))])
        
            added_points = new_points.copy()
    
        list = last_points.copy()
        list.extend(new_points)
        data.append(list)
    
    time_index = [(datetime.now() + k * timedelta(minutes=1)).strftime("%m/%d/%Y, %H:%M:%S") for k in
                  range(len(data))]
    
    return data, time_index

def compute_warning_pipe(analyzer_lat, analyzer_long, pipes, wind_direction):
    pipes_coord = [(pipe['latitude'], pipe['longitude']) for pipe in pipes]
    analyzer_coord = (analyzer_lat, analyzer_long)
    analyzer_coord = np.asarray(analyzer_coord)
    endline_coord = (analyzer_coord[0] + 1 * math.cos(math.radians(wind_direction)),
                     analyzer_coord[1] + 1 * math.sin(math.radians(wind_direction)))
    endline_coord = np.asarray(endline_coord)
    
    nearest_pipe = pipes_coord[0]
    shortest_distance = norm(np.cross(endline_coord - analyzer_coord, analyzer_coord - pipes_coord[0])) / norm(endline_coord - analyzer_coord)
    for pipe in pipes_coord:
        pipe = np.asarray(pipe)
        distance = norm(np.cross(endline_coord - analyzer_coord, analyzer_coord - pipe)) / norm(endline_coord - analyzer_coord)
        if distance < shortest_distance:
            shortest_distance = distance
            nearest_pipe = pipe

    warning_pipe = next(item for item in pipes if item['latitude'] == nearest_pipe[0] and item['longitude'] == nearest_pipe[1])
    pipe_id = warning_pipe['measurement'][-1]
    
    return warning_pipe