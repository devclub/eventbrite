#  Created by Denis Zhadan on 04.06.2024 08:18.
import json
from Poster import Poster


def read_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


info = read_from_json('events/event_1.json')
poster = Poster()
speakers = len(info['speaker'])
poster.conf = read_from_json(f'config/speaker{speakers}.json')
sponsors = read_from_json('config/sponsors.json')
poster.create_png(info, sponsors, 'poster_preview.png')
