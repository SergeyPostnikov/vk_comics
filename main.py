import requests
import os
from os.path import join
from urllib.parse import urlparse, unquote
from pathlib import Path
from dotenv import load_dotenv

from random import randint


BASE_DIR = Path(__file__).resolve().parent


class VKError(Exception):
    pass


def vk_error_raise(response_json):
    if response_json.get('error'):
        raise VKError(response_json['error']['error_msg'])


def get_filename(url):
    path = urlparse(url).path
    row_name = path.split("/")[-1]
    filename = unquote(row_name)
    return filename


def save_picture(url):
    response = requests.get(url)
    response.raise_for_status()
    filename = get_filename(url)
    path_to_image = join(BASE_DIR, filename)

    with open(path_to_image, 'wb') as file:
        file.write(response.content)

    return path_to_image


def get_comics_amount():
    url = 'https://xkcd.com/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def get_comics(num):
    url = f'https://xkcd.com/{num}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    comics = response.json()
    url = comics['img']
    alt = comics['alt']
    return url, alt


def get_random_comics(comics_amount):
    comics_number = randint(1, comics_amount)
    url, alt = get_comics(comics_number)
    path_to_image = save_picture(url)
    return path_to_image, alt


def get_wall_upload_server(group_id, access_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': 5.131
    }
    response = requests.get(url, params)
    response.raise_for_status()
    response_json = response.json()
    vk_error_raise(response_json)
    return response_json['response']['upload_url']


def upload_photo_on_server(url, path_to_image):
    with open(path_to_image, 'rb') as file:
        files = {
            'photo': file,  
        }
        response = requests.post(url, files=files)
    response.raise_for_status()
    resp = response.json()
    vk_error_raise(resp)
    server, photo, hash_photo = map(lambda key: resp[key], resp) 
    return server, photo, hash_photo


def add_photo_to_album(group_id, photo, server, hash_photo, access_token):
    params = {
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': hash_photo,
        'access_token': access_token,
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    response = requests.post(url, params)
    response.raise_for_status()
    response_json = response.json()
    vk_error_raise(response_json)
    return response_json


def post_photo_on_wall(group_id, owner_id, photo_id, access_token, massage,):
    params = {
        'owner_id': f'-{group_id}',
        'message': massage,
        'from_group': 1,
        'access_token': access_token,
        'attachments': f'photo{owner_id}_{photo_id}',
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/wall.post'
    response = requests.post(url, params)
    response.raise_for_status()
    response_json = response.json()
    vk_error_raise(response_json)
    return response_json


def post_comics_on_wall(path_to_image, alt, access_token, 
                        owner_id, photo_id, group_id):
    url = 'https://api.vk.com/method/wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'message': alt,
        'from_group': 1,
        'access_token': access_token,
        'attachments': f'photo{owner_id}_{photo_id}',
        'v': 5.131,
    }
    response = requests.post(url, params)
    response.raise_for_status()
    response_json = response.json()
    vk_error_raise(response_json)
    return response_json


def main(): 
    load_dotenv()
    access_token = os.environ['VK_ACCESS_KEY']
    group_id = os.environ['VK_XKCD_GROUP_ID']

    comics_amount = get_comics_amount()
    try:
        url = get_wall_upload_server(group_id, access_token)
        path_to_image, alt = get_random_comics(comics_amount)
        server, photo, hash_photo = upload_photo_on_server(url, path_to_image)
        resp = add_photo_to_album(
            group_id, photo, server, hash_photo, access_token
            )

        photo_id = resp['response'][0]['id']
        owner_id = resp['response'][0]['owner_id']

        post_comics_on_wall(
            path_to_image, alt, access_token, owner_id, photo_id, group_id
        )
    except requests.exceptions.RequestException as err:
        print('Проблемы с соединением:', err)
    finally:
        os.remove(path_to_image)


if __name__ == '__main__':
    main()
