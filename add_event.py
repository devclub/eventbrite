#  Created by Denis Zhadan on 25.04.2024 00:59.
import json
import sys
from Eventbrite import Eventbrite
from Poster import Poster


def read_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


if __name__ == "__main__":
    eventbrite = Eventbrite()
    poster = Poster()
    for filename in sys.argv[1:]:
        if filename.endswith('.json'):
            info = read_from_json(filename)
            speakers = len(info['speaker'])
            poster.conf = read_from_json(f'config/speaker{speakers}.json')
            sponsors = read_from_json('config/sponsors.json')
            image = poster.create_png(info, sponsors)
            event = eventbrite.create_event(info, image)
