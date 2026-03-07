import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('OMDB_API_KEY')
BASE_URL = 'http://www.omdbapi.com/'

def search_movies(query):
    params = {
        'apikey': API_KEY,
        's': query,
        'type': 'movie'
    }
    r = requests.get(BASE_URL, params=params)
    data = r.json()
    if data.get('Response') == 'True':
        return data.get('Search', [])
    return []

def get_movie_details(imdb_id):
    params = {
        'apikey': API_KEY,
        'i': imdb_id,
        'plot': 'full'
    }
    r = requests.get(BASE_URL, params=params)
    return r.json()

def get_trending_movies():
    popular = ['Inception', 'Interstellar', 'The Dark Knight',
               'Avengers', 'Pushpa', 'KGF', 'RRR', 'Baahubali']
    movies = []
    for title in popular:
        results = search_movies(title)
        if results:
            movies.append(results[0])
    return movies