import flickrapi
import random
import requests
from io import BytesIO
from datetime import datetime
from pathlib import Path
from PIL import Image
import collage
import tweepy
from tokens import CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET
OUTDIR = Path(r"C:\Users\lglanville\collage_bot\collages")

urls = [
    "https://www.flickr.com/photos/biodivlibrary/",
    "https://www.flickr.com/photos/national_library_of_australia_commons/",
    "https://www.flickr.com/photos/statelibraryofvictoria_collections/",
    "https://www.flickr.com/people/statelibraryofnsw/",
    "https://www.flickr.com/photos/britishlibrary/",
    "https://www.flickr.com/photos/powerhouse_museum/",
    "https://www.flickr.com/photos/nypl/",
    "https://www.flickr.com/photos/library_of_congress/",
    "https://www.flickr.com/photos/lac-bac/",
    "https://www.flickr.com/photos/lselibrary/",
    "https://www.flickr.com/photos/nationallibrarynz/",
    "https://www.flickr.com/photos/tepapa/",
    "https://www.flickr.com/photos/medicalmuseum/",
    "https://www.flickr.com/photos/twm_news/"
    ]


def get_photo(flickr, url):
    results = None
    while results is None:
        f = flickr.urls.lookupUser(url=url)
        ident = f[0].get('id')
        r = flickr.people.getPublicPhotos(user_id=ident)
        page = random.randint(1, int(r[0].get('pages')))
        try:
            results = flickr.people.getPublicPhotos(user_id=ident, page=page)
        except flickrapi.exceptions.FlickrError as e:
            print('unable to find photos', ident)
    choice = random.choice(results[0])
    return choice.get('id')


def get_image(flickr, photo):
    s = flickr.photos.getsizes(photo_id=photo)
    url = s[0][-1].get('source')
    r = requests.get(url)
    b = BytesIO(r.content)
    im = Image.open(b)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    return im


def grab_photo(flickr):
    photo = get_photo(flickr, random.choice(urls))
    i = flickr.photos.getInfo(photo_id=photo)
    url = i[0].find('urls')
    url = url.find("url[@type='photopage']").text
    image = get_image(flickr, photo)
    return (image, url)


def post(flickr, twitter):
    imone = None
    imtwo = None
    while imone is None:
        imone = grab_photo(flickr)
    while imtwo is None:
        imtwo = grab_photo(flickr)
    if 0.5 < imone[0].height*imone[0].width/imtwo[0].height*imtwo[0].width <1.5:
        images = collage.imcrop([imone[0], imtwo[0]])
    else:
        images = [imone[0], imtwo[0]]
    dim = max([images[0].width, images[0].height, images[1].width, images[1].height])
    pixels = dim//random.randint(10, 40)
    funcs = [
        collage.gridimpose, collage.vimpose, collage.himpose,
        collage.vstitch, collage.hstitch, collage.gridstitch,
        collage.circstitch, collage.circmerge, collage.tristitch,
        collage.equistitch, collage.v_equistitch]
    coll = random.choice(funcs)(images, pixels=pixels)
    status = imone[1]+'\n'+imtwo[1]
    coll.save(OUTDIR / f'{datetime.now().isoformat()}.jpg'.replace(':', '-'))
    with BytesIO() as output:
        coll.save(output, format="JPEG")
        twitter.update_with_media(
            'collage.jpeg', status=status, file=output)


if __name__ == '__main__':
    flickr_keys = {
    "key": "25478d32d04d4a7f2f91d0532f8a2997",
    "secret": "ff24b2ebab277447"}

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    twitter = tweepy.API(auth)
    flickr = flickrapi.FlickrAPI(flickr_keys['key'], flickr_keys['secret'])
    post(flickr, twitter)
