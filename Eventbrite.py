#  Created by Denis Zhadan on 18.05.2024 20:03.

from datetime import datetime, timezone, timedelta
import os
import requests


class Eventbrite:
    def __convert_to_utc(self, local_time_str, local_tz_str):
        local_time = datetime.strptime(local_time_str, "%Y-%m-%dT%H:%M:%S")

        # ToDo list of timezones
        if local_tz_str == "Europe/Tallinn":
            local_time = local_time.replace(tzinfo=timezone(timedelta(hours=3)))

        utc_time = local_time.astimezone(timezone.utc)
        return utc_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _get_headers(self, type='application/json'):
        token = os.getenv('EVENTBRITE_API_TOKEN')
        headers = {
            'Authorization': 'Bearer ' + token
        }
        if type is not None:
            headers['Content-Type'] = type
        return headers

    def _post(self, url, headers, json=None, data=None, **kwargs):
        response = requests.post(url, headers=headers, json=json, data=data, **kwargs)

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise Exception(response.text)

    def _get(self, url, params=None, **kwargs):
        response = requests.get(url, params=params, **kwargs)

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise Exception(response.text)

    def _create_draft(self, name, timezone, start, end, currency, capacity):
        data = {
            'event': {
                'name': {
                    'html': name
                },
                'start': {
                    'timezone': timezone,
                    'utc': self.__convert_to_utc(start, timezone)
                },
                'end': {
                    'timezone': timezone,
                    'utc': self.__convert_to_utc(end, timezone)
                },
                'currency': currency,
                'capacity': capacity
            }
        }

        # API Eventbrite & ORGANIZATION_ID
        organization_id = os.getenv('EVENTBRITE_ORGANIZATION_ID')
        return self._post(f'https://www.eventbriteapi.com/v3/organizations/{organization_id}/events/',
                          self._get_headers(), json=data)

    def _add_venue(self, name, address1, address2, city, region, postal_code, country_code):
        data = {
            "venue": {
                "name": name,
                "address": {
                    "address_1": address1,
                    "address_2": address2,
                    "city": city,
                    "region": region,
                    "postal_code": postal_code,
                    "country": country_code
                }
            }
        }

        # API Eventbrite & ORGANIZATION_ID
        organization_id = os.getenv('EVENTBRITE_ORGANIZATION_ID')
        return self._post(f'https://www.eventbriteapi.com/v3/organizations/{organization_id}/venues/',
                          self._get_headers(), json=data)

    def __truncate_string(self, value, max_length):
        if len(value) <= max_length:
            return value

        three_dots = '...'
        three_dots_len = len(three_dots)

        if max_length <= three_dots_len:
            return value[:max_length]

        space_index = value.rfind(' ', 0, max_length - three_dots_len + 1)
        if space_index == -1:
            return value[:max_length - three_dots_len] + three_dots

        return value[:space_index] + three_dots

    def _update_info(self, event_id, listed, shareable, venue_id, event_logo_id, summary):
        data = {
            'event': {
                'listed': listed,
                'shareable': shareable,
                'venue_id': venue_id,
                'logo': {
                    'id': event_logo_id
                },
                'summary': self.__truncate_string(summary, 140)
                # A summary up to 140 characters that describes the most important details of your event.
            }
        }

        return self._post(f'https://www.eventbriteapi.com/v3/events/{event_id}/',
                          self._get_headers(), json=data)

    def _add_tickets(self, event_id, name, quantity_total, cost, free, minimum_quantity, maximum_quantity, sales_end):
        data = {
            'ticket_class': {
                'name': name,
                'quantity_total': quantity_total,
                'cost': cost,
                'free': free,
                'minimum_quantity': minimum_quantity,
                'maximum_quantity': maximum_quantity,
                "sales_start": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sales_end": sales_end
            }
        }

        return self._post(f'https://www.eventbriteapi.com/v3/events/{event_id}/ticket_classes/',
                          self._get_headers(), json=data)

    def _upload_event_logo(self, event_logo):
        width, height = event_logo[-1]
        event_logo = event_logo[:-1]

        MEDIA_UPLOAD_URL = 'https://www.eventbriteapi.com/v3/media/upload/'
        params = {
            "type": "image-event-logo"
        }
        data = self._get(MEDIA_UPLOAD_URL, params=params, headers=self._get_headers(None))

        post_args = data['upload_data']
        response_cdn = requests.post(data['upload_url'], data=post_args,
                                     files={data['file_parameter_name']: event_logo}
                                     )

        image_data = {
            'upload_token': data['upload_token'],
            'crop_mask': {'top_left': {'y': 1, 'x': 1}, 'width': width, 'height': height}
        }
        return self._post(MEDIA_UPLOAD_URL, headers=self._get_headers(), json=image_data)

    def _publish(self, event_id):
        return self._post(f'https://www.eventbriteapi.com/v3/events/{event_id}/publish/',
                          self._get_headers(), json={})

    def send_to_telegram(self, text):
        token = os.getenv('TELEGRAM_API_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        data = {
            'chat_id': chat_id,
            'text': text
        }

        response = requests.post(f'https://api.telegram.org/bot{token}/sendMessage', data=data)
        return response.json()

    def _add_content_text(self, event_id, version_number, info):

        content_text = ''
        for speaker in info['speaker']:
            content_text += f'<b>{speaker['name']}</b><br/>{speaker['title']}<br/><b>{speaker['subject']}</b><br/>{speaker['description']}<br/><br/>'

        data = {
            'access_type': 'public',
            'modules': [{
                'type': 'text',
                'data': {
                    'body': {
                        'type': 'text',
                        'text': content_text,
                        'alignment': 'left'
                    }
                }
            }],
            'publish': True,
            'purpose': 'listing'
        }

        result = self._post(f'https://www.eventbriteapi.com/v3/events/{event_id}/structured_content/{version_number}/',
                            self._get_headers(), json=data)
        return result

    def _add_question(self, event_id, data):
        return self._post(f'https://www.eventbriteapi.com/v3/events/{event_id}/questions/', self._get_headers(),
                          json=data)

    def create_event(self, info, event_logo):
        event = self._create_draft(info['name'],
                                   info['timezone'],
                                   info['start_local'],
                                   info['end_local'],
                                   info['currency'],
                                   info['capacity'])
        event_url = event['url']

        venue = self._add_venue(info['venue']['name'],
                                info['venue']['address']['address_1'],
                                info['venue']['address'].get('address_2', ''),
                                info['venue']['address']['city'],
                                info['venue']['address'].get('region', ''),
                                info['venue']['address'].get('postal_code', ''),
                                info['venue']['address'].get('country', 'EE'))

        poster = self._upload_event_logo(event_logo)
        self._update_info(event['id'],
                          info['listed'],
                          info['shareable'],
                          venue['id'],
                          poster['id'],
                          info['summary']
                          )

        ticket = self._add_tickets(event['id'],
                                   info['ticket']['name'],
                                   info['ticket']['quantity_total'],
                                   info['ticket']['cost'],
                                   info['ticket']['free'],
                                   info['ticket']['minimum_quantity'],
                                   info['ticket']['maximum_quantity'],
                                   self.__convert_to_utc(info['start_local'], info['timezone']))

        content_result = self._add_content_text(event['id'], 1, info)

        for question in info['questions']:
            question_result = self._add_question(event['id'], {'question': question})

        result = self._publish(event['id'])

        if result['published']:
            self.send_to_telegram(event_url)

        return result['published']
