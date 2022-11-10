# imports
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import json
import googlemaps
import os

# globals
MAX_HITS = None
app = FastAPI()
GM = googlemaps.Client(key="AIzaSyC6YLATu4aS3x0B91uHqxtjad-PeQ6XupU")
dict_for_count_searches = dict([])


class Distance(BaseModel):
    source: str
    destination: str
    distance: str


def set_name_of_city(city: str) -> str:
    """

    :param city: Get string of city to set
    :return: The string without space and only small letters
    """
    return city.replace(" ", "").lower()


def add_distance_to_db(source: str, destination: str, the_distance: str):
    """

    :param source:  City number 1 to calculate distance
    :param destination: City number 2 to calculate distance
    :param the_distance: The distance between 2 cities
    The function add a new distance to the local db
    """
    source = set_name_of_city(source)
    destination = set_name_of_city(destination)
    dict_for_count_searches[source + destination] = 1
    dict_for_count_searches[destination + source] = 0
    if source > destination:
        the_source = destination
        the_destination = source
    else:
        the_source = source
        the_destination = destination

    new_distance = {
        "source": the_source,
        "destination": the_destination,
        "distance": the_distance,

    }
    my_distances.append(new_distance)
    with open('cities.json', 'w') as f:
        json.dump(my_distances, f, indent=len(my_distances))


def update_max_hints(source: str, destination: str, distance: str):
    """
    Compare sum of searching between current max and new option
    :param source:
    :param destination:
    :param distance:
    """

    new_distance ={
        "source": source,
        "destination": destination,
        "distance": distance

    }

    global MAX_HITS
    if not MAX_HITS:
        MAX_HITS = new_distance
        return
    if source + destination in dict_for_count_searches:
        if dict_for_count_searches[MAX_HITS['source'] + MAX_HITS['destination']] < \
                dict_for_count_searches[source + destination]:
            MAX_HITS = new_distance
    return


def found_distance(city_1: str, city_2: str):
    """

    :param city_1:
    :param city_2:
    :return: The distance between 2 cities
    """
    distance = GM.distance_matrix(city_1, city_2)['rows'][0]['elements'][0]
    if distance['status'] == 'OK':
        return True, distance['distance']['text']
    return False, "not results"


@app.get('/', status_code=200)
def start():
    data = "Welcome to Geolocation Server!"
    return Response(content=data, media_type="application/json", )


@app.get('/hello', status_code=200)
def hello():
    return Response(content="", media_type="application/json")


@app.get('/distance', status_code=200)
def get_distance(source: str, destination: str):
    """

    :param source: City number 1 to calculate distance
    :param destination: City number 2 to calculate distance
    :return: The distance between 2 cities
    """
    source = set_name_of_city(source)
    destination = set_name_of_city(destination)
    if source < destination:
        in_place = True
    else:
        source, destination = destination, source
        in_place = False

    if source + destination in dict_for_count_searches or destination + source in dict_for_count_searches:
        for distance in my_distances:
            if distance['source'] == source and distance['destination'] == destination:
                # Add 1 to count of searching
                if in_place:
                    dict_for_count_searches[source + destination] += 1
                    update_max_hints(source, destination, distance['distance'])
                else:
                    dict_for_count_searches[destination + source] += 1
                    update_max_hints(destination, source, distance['distance'])
                # if this searching is more than previous max, set the max
                return {"distance": distance['distance']}

    # If the distance was not stored in db before, find it and store in the local db
    valid, new_distance = found_distance(source, destination)
    if valid:
        add_distance_to_db(source, destination, new_distance)
        update_max_hints(source, destination, new_distance)
    else:
        return HTTPException(status_code=500, detail="No Results.")
    return {"distance": new_distance}



@app.get('/health', status_code=200)
def check_health():
    """
    :return: The status of the connection to the DB
    """
    try:
        with open('cities.json', 'r') as fp:
            cities = json.load(fp)
        if len(cities) == 0:
            return HTTPException(status_code=500, detail="The Local DB is Empty")
        return Response(content="", media_type="application/json")
    except IOError:
        return HTTPException(status_code=500, detail="No Connection to The DB")



@app.get('/popularsearch', status_code=200)
def check_popular():
    """
    :return: The most popular search and number of hits for that search
    """

    if not MAX_HITS:
        return HTTPException(status_code=500, detail="No searching")


    source = MAX_HITS['source']
    destination = MAX_HITS['destination']
    return {"source": source, "destination": destination, "hits": dict_for_count_searches[source + destination]}


@app.post('/distance', status_code=201)
def change_distance(my_distance: Distance):
    """

    :param my_distance: 2 cities and the distance between them, in order to edit the old distance
    :return:
    """
    source = set_name_of_city(my_distance.source)
    destination = set_name_of_city(my_distance.destination)
    the_distance = my_distance.distance
    place_of_search = 0
    if source > destination:
        source, destination = destination, source
        place_of_search = 1

    new_distance = {
        "source": source,
        "destination": destination,
        "distance": the_distance,

    }
    if source + destination in dict_for_count_searches:
        for distance in my_distances:
            if distance['source'] == source and distance['destination'] == destination:
                my_distances.remove(distance)
                my_distances.append(new_distance)
        # Apply changes to the DB
        with open('cities.json', 'w') as f:
            json.dump(my_distances, f, indent=len(my_distances))

    else:
        my_distances.append(new_distance)
        # Apply changes to the DB
        with open('cities.json', 'w') as f:
            json.dump(my_distances, f, indent=len(my_distances))
        dict_for_count_searches[source + destination] = [0, 0]
    the_hits = dict_for_count_searches[source + destination][place_of_search]
    return {"source": source, "destination": destination, "hits": the_hits}


# Beginning
if os.stat("cities.json").st_size == 0:
    with open('cities.json', 'w') as f:
        f.write("[]")
with open('cities.json', 'r') as f:
    my_distances = json.load(f)
