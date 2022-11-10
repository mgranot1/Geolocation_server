
# imports
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
import json
import googlemaps
import os

# globals
MAX_HITS = None
app = FastAPI()
GM = googlemaps.Client(key="AIzaSyC6YLATu4aS3x0B91uHqxtjad-PeQ6XupU")


class Distance(BaseModel):
    source: str
    destination: str
    distance: str
    hits_1: Optional[int] = None  # num of 'source - destination' searching
    hits_2: Optional[int] = None  # num of 'destination - source' searching


def set_name_of_city(city: str) -> str:
    """

    :param city: Get string of city to set
    :return: The string without space and only small letters
    """
    return city.replace(" ", "").lower()


def add_distance_to_db(source: str, destination: str, the_distance: str):
    """

    :param the_source:  City number 1 to calculate distance
    :param the_destination: City number 2 to calculate distance
    :param the_distance: The distance between 2 cities
    The function add a new distance to the local db
    """
    source = set_name_of_city(source)
    destination = set_name_of_city(destination)
    hit_1 = 0
    hit_2 = 0
    if source > destination:
        the_source = destination
        the_destination = source
        hit_2 = 1
    else:
        the_source = source
        the_destination = destination
        hit_1 = 1

    new_distance = {
        "source": the_source,
        "destination": the_destination,
        "distance": the_distance,
        "hits_1": hit_1,
        "hits_2": hit_2
    }

    my_distances.append(new_distance)
    with open('cities.json', 'w') as f:
        json.dump(my_distances, f, indent=len(my_distances))
    return new_distance


def update_max_hints(distance:Distance,hits:str):
    global MAX_HITS
    if not MAX_HITS or distance[hits] > MAX_HITS[hits]:
        MAX_HITS = distance

def found_distance(city_1: str, city_2: str):
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
        hits = 'hits_1'
    else:
        source, destination = destination, source
        hits = 'hits_2'
    for distance in my_distances:
        if distance['source'] == source and distance['destination'] == destination:
            # Add 1 to count of searching
            distance[hits] += 1
            with open('cities.json', 'w') as f:
                json.dump(my_distances, f, indent=len(my_distances))
            # if this searching is more than previous max, set the max
            update_max_hints(distance,hits)
            return {"distance": distance['distance']}
    # If the distance was not stored in db before, find it and store in the local db
    valid, new_distance = found_distance(source, destination)
    if valid:
        update_max_hints(add_distance_to_db(source, destination, new_distance),hits)
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

    # hits_1 is the stored order, hit_2 is the reverse order
    if MAX_HITS['hits_2'] > MAX_HITS['hits_1']:
        return {"source": MAX_HITS['destination'], "destination": MAX_HITS['source'], "hits": MAX_HITS['hits_2']}
    else:
        return {"source": MAX_HITS['source'], "destination": MAX_HITS['destination'], "hits": MAX_HITS['hits_1']}


@app.post('/distance', status_code=201)
def change_distance(my_distance: Distance):
    """

    :param my_distance: 2 cities and the distance between them, in order to edit the old distance
    :return:
    """
    source = set_name_of_city(my_distance.source)
    destination = set_name_of_city(my_distance.destination)
    the_distance = my_distance.distance
    if source > destination:
        source, destination = destination, source

    exist_in_local_db = False
    new_distance = {
        "source": source,
        "destination": destination,
        "distance": the_distance,
        "hits_1": 0,
        "hits_2": 0
    }

    for distance in my_distances:
        if distance['source'] == source and distance['destination'] == destination:
            exist_in_local_db = True
            new_distance['hits_1'] = distance['hits_1']
            new_distance['hits_2'] = distance['hits_2']
            my_distances.remove(distance)
            my_distances.append(new_distance)
    # Apply changes to the DB
    with open('cities.json', 'w') as f:
        json.dump(my_distances, f, indent=len(my_distances))
    if not exist_in_local_db:
        my_distances.append(new_distance)
        # Apply changes to the DB
        with open('cities.json', 'w') as f:
            json.dump(my_distances, f, indent=len(my_distances))
    return {"source": source, "destination": destination, "hits": the_distance}


# Beginning
if os.stat("cities.json").st_size == 0:
    with open('cities.json', 'w') as f:
        f.write("[]")
with open('cities.json', 'r') as f:
    my_distances = json.load(f)
