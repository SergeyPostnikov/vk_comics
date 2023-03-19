import requests
import os
from os.path import join
from urllib.parse import urlparse, unquote
from pathlib import Path
from dotenv import load_dotenv

from random import randint


BASE_DIR = Path(__file__).resolve().parent


def get_filename(url):
    path = urlparse(url).path
    row_name = path.split("/")[-1]
    filename = unquote(row_name)
    return filename


def save_picture(url, params=None):
    response = requests.get(url, params=params)
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
    url, alt = get_comics(num=comics_number)
    path_to_image = save_picture(url=url)
    return path_to_image, alt


def get_wall_upload_server(group_id, access_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    params = {
        'group_id': group_id,
        'access_token': access_token,
        'v': 5.131
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()['response']['upload_url']


def post_photo_on_server(url, path_to_image):
    with open(path_to_image, 'rb') as file:
        files = {
            'photo': file,  
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        resp_dict = response.json()
        server, photo, hash_photo = map(lambda key: resp_dict[key], resp_dict) 
        return server, photo, hash_photo


def add_photo_to_albom(group_id, photo, server, hash_photo, access_token):
    params = {
        'group_id': group_id,
        # 'user_id': user_id,
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


def post_photo_on_wall(group_id, owner_id, massage, photo_id, access_token):
    params = {
        'owner_id': f'-{group_id}',
        'message': massage,
        'from_group': 1,
        'access_token': access_token,
        'attachments': f'photo{owner_id}_{photo_id}',
        'v': 5.131,
    }
    url = 'https://api.vk.com/method/wall.post'
    response = requests.post(url=url, params=params)
    response.raise_for_status()
    return response.json()


def post_comics_on_wall(path_to_image, alt, access_token):
    url = get_wall_upload_server(group_id, access_token=access_token)
    server, photo, hash_photo = post_photo_on_server(url=url, path_to_image=path_to_image)
    resp = add_photo_to_albom(
        group_id=group_id, 
        photo=photo, 
        server=server, 
        hash_photo=hash_photo, 
        access_token=access_token)

    photo_id = resp['response'][0]['id']
    owner_id = resp['response'][0]['owner_id']

    resp = post_photo_on_wall(
        group_id=group_id, 
        photo_id=photo_id,
        owner_id=owner_id, 
        massage=alt, 
        access_token=access_token
        )


def main(access_token, group_id):
    comics_amount = get_comics_amount()
    path_to_image, alt = get_random_comics(comics_amount)

    post_comics_on_wall(
        path_to_image=path_to_image,
        alt=alt,
        access_token=access_token
        )
    
    os.remove(path_to_image)


if __name__ == '__main__':
    load_dotenv()
    access_token = os.environ['VK_ACCESS_KEY']
    group_id = os.environ['VK_XKCD_GROUP_ID']

    main(access_token=access_token, group_id=group_id)
