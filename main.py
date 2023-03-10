import requests
import os
from os.path import splitext, join
from urllib.parse import urlparse, unquote
from hashlib import blake2b
from pathlib import Path

from pprint import pprint
from dotenv import load_dotenv

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


def get_comment(num):
    url = f'https://xkcd.com/{num}/info.0.json'
    response = requests.get(url)
    return response.json().get('alt')


def get_groups(user_id, access_token):
    url = 'https://api.vk.com/method/groups.get'
    headers = {}
    params = {
        'user_id': user_id,
        'access_token': access_token,
        'v': 5.131
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json()


def get_wall_upload_server(group_id, access_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': 5.131
    }
    response = requests.get(url, params=params)
    return response.json()


def post_photo(url, path_to_image):
    with open(path_to_image, 'rb') as file:
        files = {
            'photo': file,  
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        return response.json()


def add_photo_to_albom(group_id, photo, server, hash_photo, access_token):
    params = {
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': hash_photo,
        'access_token': access_token,
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url=url, params=params)
    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    # url = get_img_url(353)
    # save_picture(url=url, directory='images')
    # print(get_comment(353))

    load_dotenv()
    access_token = os.environ['VK_BOT_ACCESS_KEY']
    user_id = os.environ['VK_USER_ID']

    group_id = os.environ['VK_XKCD_GROUP_ID']
    url = get_wall_upload_server(group_id, access_token=access_token).get('response').get('upload_url')
    resp = post_photo(url=url, path_to_image='./images/35e508cb6cpython.png')
    server, photo, hash_photo = map(lambda key: resp[key], resp)
    resp = add_photo_to_albom(group_id, photo, server, hash_photo, access_token)
    pprint(resp)
