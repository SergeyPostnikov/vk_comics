import requests
import os
from os.path import splitext, join
from urllib.parse import urlparse, unquote
from hashlib import blake2b
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def get_filename(url):
    path = urlparse(url).path
    row_name = path.split("/")[-1]
    filename = unquote(row_name)
    hashed_name = blake2b(digest_size=5)
    hashed_name.update(bytes(filename, encoding='utf-8'))
    return f'{hashed_name.hexdigest()}{filename}'


def save_picture(url, directory, params=None):
    response = requests.get(url, params=params)
    response.raise_for_status()
    os.makedirs(directory, exist_ok=True)

    with open(join(BASE_DIR, 'images', get_filename(url)), 'wb') as file:
        file.write(response.content)


def get_img_url(num):
    url = f'https://xkcd.com/{num}/info.0.json'
    response = requests.get(url)
    return response.json().get('img')


if __name__ == '__main__':
    url = get_img_url(353)
    save_picture(url=url, directory='images')
