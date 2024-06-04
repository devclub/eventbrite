#  Created by Denis Zhadan on 22.05.2024 05:45.
import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont


class Poster:
    conf = {}

    def __write_in_box(self, draw, text, box, font, color):
        textbox = draw.textbbox((0, 0), text, font)
        left = ((box[2] - box[0]) - (textbox[2] - textbox[0])) / 2
        top = ((box[3] - box[1]) - (textbox[3] - textbox[1])) / 2
        x = box[0] + left - textbox[0]
        y = box[1] + top - textbox[1]
        draw.text((x, y), text, fill=color, font=font)

    def __write_at(self, draw, xy, text, font, color):
        textbox = draw.textbbox((0, 0), text, font)
        draw.text((xy[0] - textbox[0], xy[1] - textbox[1]), text, fill=color, font=font)

    def _event_date(self, image, draw, date_box, info):
        date_box_border = Image.open(date_box['image'])

        if image.mode != date_box_border.mode:
            image.paste(date_box_border, tuple(date_box['position']))
        else:
            image.paste(date_box_border, tuple(date_box['position']), date_box_border)

        date = datetime.datetime.fromisoformat(info['start_local'])
        day_of_week = date.weekday()
        day_name = self.conf['days'][day_of_week]
        event_date = day_name + ' | ' + date.strftime("%H:%M") + ' | ' + date.strftime("%d.%m.%Y")

        self.__write_in_box(draw, event_date,
                            [
                                date_box['position'][0], date_box['position'][1],
                                date_box['position'][0] + date_box['width'] - 1,
                                date_box['position'][1] + date_box['height'] - 1
                            ],
                            font=ImageFont.truetype(date_box['font']['name'], date_box['font']['size']),
                            color=tuple(date_box['color']))

    def __add_logo(self, image, conf):
        logo = Image.open(conf['image'])
        logo = logo.resize((conf['width'], conf['height']))

        if image.mode != logo.mode:
            image.paste(logo, tuple(conf['position']))
        else:
            image.paste(logo, tuple(conf['position']), logo)

    def __avatar(self, filename, name, title, font_name, font_title, width, height, block_name_height,
                 block_title_height,
                 name_color, title_color, background_color, block_background_color, **kwargs):

        block_height = block_name_height + block_title_height
        background = Image.new('RGBA', (width, height), color=tuple(background_color))
        draw = ImageDraw.Draw(background)

        avatar = Image.open(filename)
        avatar = avatar.resize((width, height))
        background.paste(avatar, (0, 0))

        draw.rectangle([(0, height - block_height), (width - 1, height - 1)], fill=tuple(block_background_color))

        self.__write_in_box(draw, name, [0, height - block_height, width - 1, height - block_title_height - 1],
                            font=font_name, color=tuple(name_color))
        self.__write_in_box(draw, title, [0, height - block_title_height, width, height],
                            font=font_title, color=tuple(title_color))
        return background

    def __add_speakers(self, image, info, conf):
        font_name = ImageFont.truetype(conf['name_font']['name'], conf['name_font']['size'])
        font_title = ImageFont.truetype(conf['title_font']['name'], conf['title_font']['size'])

        for i, speaker in enumerate(info['speaker']):
            avatar = self.__avatar(speaker['image'], speaker['name'], speaker['title'], font_name, font_title, **conf)
            image.paste(avatar, tuple(conf['position'][i]))

    def __add_subjects(self, draw, info, conf):
        font_subject = ImageFont.truetype(conf['font']['name'], conf['font']['size'])
        y_text = conf['position'][1]

        for speaker in info['speaker']:
            lines = textwrap.wrap(conf.get('prefix', '') + speaker['subject'], width=conf['characters_per_line'])
            for line in lines:
                draw.text((conf['position'][0], y_text), line, font=font_subject,
                          fill=tuple(conf['color']))
                y_text += font_subject.getbbox(line)[3]
            y_text += font_subject.getbbox(line)[3]

    def __add_title(self, draw, info, conf):
        font = ImageFont.truetype(conf['font']['name'], conf['font']['size'])
        self.__write_at(draw, conf['position'], info['short_name'], font, tuple(conf['color']))
        textbox = draw.textbbox((0, 0), info['short_name'] + ' ', font)
        self.__write_at(draw, (conf['position'][0] + textbox[2], conf['position'][1]),
                        info['number'], ImageFont.truetype(conf['sub_font']['name'], conf['sub_font']['size']),
                        tuple(conf['sub_color']))

    def __add_address(self, draw, venue, conf):
        font_address = ImageFont.truetype(conf['font']['name'], conf['font']['size'])
        self.__write_at(draw, tuple(conf['place_position']), venue['name'], font_address,
                        tuple(conf['color']))

        address = ", ".join(filter(None, [
            venue['address'].get('address_1'),
            venue['address'].get('address_2'),
            venue['address'].get('city'),
            venue['address'].get('postal_code')
        ]))
        self.__write_at(draw, tuple(conf['position']), address, font_address, tuple(conf['color']))

    def __add_sponsors(self, image, sponsors, max_width, space, left, bottom, color, **kwargs):
        count = len(sponsors['companies'])
        width = (max_width - space * (count - 1)) // count
        height = width

        background = Image.new('RGBA', (max_width, height), color=tuple(color))

        xy = [0, 0]
        for i, company in enumerate(sponsors['companies']):
            logo = Image.open(company['logo'])
            logo = logo.resize((width, height))

            if background.mode != logo.mode:
                background.paste(logo, tuple(xy))
            else:
                background.paste(logo, tuple(xy), logo)

            xy[0] += width + space

        image.paste(background, (left, bottom - background.size[1]))

    def create_png(self, info, sponsors, file_name=None):
        image = Image.open(self.conf['background'])
        draw = ImageDraw.Draw(image)

        # Logo
        self.__add_logo(image, self.conf['logo'])

        # Speakers
        self.__add_speakers(image, info, self.conf['avatar'])

        self.__add_subjects(draw, info, self.conf['subject'])

        # Event date
        self._event_date(image, draw, self.conf['date_box'], info)

        # Title
        self.__add_title(draw, info, self.conf['title'])

        # Address & place
        self.__add_address(draw, info['venue'], self.conf['address'])

        # Sponsors
        self.__add_sponsors(image, sponsors, **self.conf['sponsors'])

        if file_name is not None:
            image.save(file_name)
            return
        else:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            return ('poster.png', img_byte_arr, image.size)
