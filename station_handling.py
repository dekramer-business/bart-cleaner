from collections import deque

station_names = [
    "Downtown Berkeley", "Ashby", "MacArthur", "19th St Oakland", "12th St Oakland", 
    "West Oakland", "Embarcadero", "Montgomery St", "Powell St", "Civic Center/UN Plaza", 
    "16th St Mission", "24th St Mission", "Antioch", "Pittsburg Center", "Transfer Stop", 
    "Pittsburg/Bay Point", "North Concord/Martinez", "Concord", "Pleasant Hill/Contra Costa Centre", 
    "Walnut Creek", "Lafayette", "Orinda", "Rockridge"
]

station_colors = {
    # Red Line stations
    "Downtown Berkeley": "red",
    "Ashby": "red",
    "MacArthur": "red",
    "19th St Oakland": "red",
    "12th St Oakland": "red",
    "West Oakland": "red",
    "Embarcadero": "red",
    "Montgomery St": "red",
    "Powell St": "red",
    "Civic Center/UN Plaza": "red",
    "16th St Mission": "red",
    "24th St Mission": "red",
    
    # Yellow Line stations
    "Antioch": "yellow",
    "Pittsburg Center": "yellow",
    "Transfer Stop": "yellow",
    "Pittsburg/Bay Point": "yellow",
    "North Concord/Martinez": "yellow",
    "Concord": "yellow",
    "Pleasant Hill/Contra Costa Centre": "yellow",
    "Walnut Creek": "yellow",
    "Lafayette": "yellow",
    "Orinda": "yellow",
    "Rockridge": "yellow",
    "MacArthur": "yellow"  # Shared with Red Line
}

# List of adjacent stations as pairs (Uptown-Downtown) for both red and yellow lines
adjacent_stations = [
    # Red Line (or others if specified)
    ("Downtown Berkeley", "Ashby"),
    ("Ashby", "MacArthur"),
    ("MacArthur", "19th St Oakland"),
    ("19th St Oakland", "12th St Oakland"),
    ("12th St Oakland", "West Oakland"),
    ("West Oakland", "Embarcadero"),
    ("Embarcadero", "Montgomery St"),
    ("Montgomery St", "Powell St"),
    ("Powell St", "Civic Center/UN Plaza"),
    ("Civic Center/UN Plaza", "16th St Mission"),
    ("16th St Mission", "24th St Mission"),

    # Yellow Line (or others if specified)
    ("Antioch", "Pittsburg Center"),
    ("Pittsburg Center", "Transfer Stop"),
    ("Transfer Stop", "Pittsburg/Bay Point"),
    ("Pittsburg/Bay Point", "North Concord/Martinez"),
    ("North Concord/Martinez", "Concord"),
    ("Concord", "Pleasant Hill/Contra Costa Centre"),
    ("Pleasant Hill/Contra Costa Centre", "Walnut Creek"),
    ("Walnut Creek", "Lafayette"),
    ("Lafayette", "Orinda"),
    ("Orinda", "Rockridge"),
    ("Rockridge", "MacArthur")
]

# copied straight from chatGPT
def get_adjacent_station_pair(station1, station2):
    """
    Given two station names, checks if they are adjacent (for both red and yellow line stations)
    and returns the standardized "UptownStationName-DowntownStationName" format, with uptown stations always first.
    
    :param station1: The first station name.
    :param station2: The second station name.
    :return: A string in the format "UptownStationName-DowntownStationName" or None if not adjacent.
    """
    
    # Check if the pair exists in the list
    if (station1, station2) in adjacent_stations:
        return f"{station1}-{station2}"
    elif (station2, station1) in adjacent_stations:
        return f"{station2}-{station1}"
    
    # Return None if not adjacent
    return None

# copied straight from chat
def get_station_route(start_end_station_tuple):
    """
    Given two station names, returns a route that connects them using adjacent stations.
    The route is a list of station pairs in the format ["first station", "first station-second station", ..., "last station"].
    
    :param start_station: The starting station name.
    :param end_station: The destination station name.
    :return: A list of route segments, where each segment is formatted as "first station-second station".
    """
    # Create adjacency list
    (start_station, end_station) = start_end_station_tuple

    adjacency_list = {}
    for station1, station2 in adjacent_stations:
        if station1 not in adjacency_list:
            adjacency_list[station1] = []
        if station2 not in adjacency_list:
            adjacency_list[station2] = []
        adjacency_list[station1].append(station2)
        adjacency_list[station2].append(station1)
    
    # BFS setup
    queue = deque([(start_station, [])])  # Queue holds (current_station, path_taken_so_far)
    visited = set()  # To track visited stations

    # BFS to find the shortest path
    while queue:
        current_station, path = queue.popleft()
        
        # If we reached the destination
        if current_station == end_station:
            # Append the final station
            route = path + [current_station]
            # Format the path in the required "station1-station2" format
            route_segments = []
            for i in range(len(route) - 1):
                segment = get_adjacent_station_pair(route[i], route[i+1])
                route_segments.append(segment)
            return [route[0]] + route_segments + [route[-1]]
    
        # Mark the station as visited
        if current_station not in visited:
            visited.add(current_station)
            
            # Enqueue all adjacent stations that haven't been visited
            for neighbor in adjacency_list.get(current_station, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_station]))
    
    return ["No route found"]