from PIL import Image
import random
from PIL import ImageChops, ImageDraw
import argparse
import os
import math


def imcrop(images):
    cropped = []
    width = min([im.width for im in images])
    height = min([im.height for im in images])
    for image in images:
        left = random.randint(0, image.width-width)
        upper = random.randint(0, image.height-height)
        cr = image.crop([left, upper, left+width, upper+height])
        cropped.append(cr)
    return cropped


def iter_slices(images, slice_dim):
    slices = []
    for ref, image in enumerate(images):
        left = 0
        upper = 0
        right = slice_dim[0]
        lower = slice_dim[1]
        while lower <= image.height:
            while right <= image.width:
                c = (left, upper, right, lower)
                slices.append((ref, c))
                left += slice_dim[0]
                right += slice_dim[0]
            upper += slice_dim[1]
            lower += slice_dim[1]
            left = 0
            right = slice_dim[0]
    return slices


def hstitch(images, pixels=100):
    images = imcrop(images)
    slices = iter_slices(images, (images[0].width, pixels))
    slices = random.sample(slices, len(slices)//2)
    newim = Image.new(
        "RGB", (images[0].width, len(slices)*pixels), (100, 255, 255))
    upper = 0
    for slice in slices:
        slice = images[slice[0]].crop(slice[1])
        if random.getrandbits(1) == 1:
            slice = slice.transpose(Image.FLIP_TOP_BOTTOM)
        newim.paste(slice, (0, upper))
        upper += pixels
    return(newim)


def vstitch(images, pixels=100):
    images = imcrop(images)
    slices = iter_slices(images, (pixels, images[0].height))
    slices = random.sample(slices, len(slices)//2)
    newim = Image.new(
        "RGB", (len(slices)*pixels, images[0].height), (100, 255, 255))
    left = 0
    for slice in slices:
        slice = images[slice[0]].crop(slice[1])
        if random.getrandbits(1) == 1:
            slice = slice.transpose(Image.FLIP_LEFT_RIGHT)
        newim.paste(slice, (left, 0))
        left += pixels
    return(newim)


def circstitch(images, pixels=100):
    mask_im = Image.new("L", (pixels*3, pixels*3), 0)
    draw = ImageDraw.Draw(mask_im)
    draw.ellipse((0, 0, pixels*3, pixels*3), fill=255)
    mask_im = mask_im.resize((pixels, pixels), Image.ANTIALIAS)
    c_image = random.choice(images)
    colors = c_image.getcolors(maxcolors=c_image.height*c_image.width)
    slices = iter_slices(images, (pixels, pixels))
    sqr = math.floor(math.sqrt(len(slices)))
    newim = Image.new("RGB", (sqr*pixels, sqr*pixels), max(colors)[1])
    x = 0
    y = 0
    while y < sqr*pixels:
        while x < sqr*pixels:
            if slices != []:
                slice = random.choice(slices)
                slices.remove(slice)
                slice = images[slice[0]].crop(slice[1])
                newim.paste(slice, (x, y), mask_im)
            x += pixels
        x = 0
        y += pixels
    return(newim)


def circmerge(images, pixels=100):
    a = circstitch(images, pixels=pixels)
    b = circstitch(images, pixels=pixels)
    b = shift(b, pixels//2, dir='N')
    b = shift(b, pixels//2, dir='W')
    im = random.choice([ImageChops.darker, ImageChops.lighter])(a, b)
    return(im)


def tristitch(images, pixels=100):
    mask_im = Image.new("L", (pixels, pixels), 0)
    draw = ImageDraw.Draw(mask_im)
    if random.getrandbits(1) == 0:
        draw.polygon([(0, 0), (0, pixels), (pixels, pixels)], fill=255)
    else:
        draw.polygon([(0, pixels), (pixels, 0), (0, 0)], fill=255)
    slices = iter_slices(images, (pixels, pixels))
    x = 0
    y = 0
    sqr = math.floor(math.sqrt(len(slices)))
    newim = Image.new("RGB", (sqr*pixels, sqr*pixels), (255, 255, 255))
    lslices = slices.copy()
    while y < newim.height:
        while x < newim.width:
            if len(slices) > 1:
                c = random.choice(slices)
                slices.remove(c)
                slice = images[c[0]].crop(c[1])
                newim.paste(slice, (x, y), mask_im)
                c = random.choice(lslices)
                lslices.remove(c)
                slice = images[c[0]].crop(c[1])
                newim.paste(slice, (x, y), mask_im.transpose(Image.ROTATE_180))
            x += pixels
        x = 0
        y += pixels
    return(newim)


def equistitch(images, pixels=100):
    altitude = round(0.5 * math.sqrt(3) * pixels)
    mask_im = Image.new("L", (pixels*3, altitude*3), 0)
    draw = ImageDraw.Draw(mask_im)
    draw.polygon(
        [(0, 0), (pixels*3, 0), (round(pixels/2)*3, altitude*3)],
        fill=255)
    mask_im = mask_im.resize((pixels, altitude), Image.ANTIALIAS)
    slices = iter_slices(images, (pixels, altitude))
    sqr = math.floor(math.sqrt(math.floor(len(slices)/2)))-1
    new_height = sqr*altitude
    new_width = sqr*pixels
    newim = Image.new("RGB", (new_width, new_height), (100, 255, 255))
    x = 0 - math.floor(pixels/2)
    y = 0
    while y < new_height:
        while x < new_width:
            if slices != []:
                if x == new_width - math.floor(pixels/2):
                    newim.paste(edge, (x, y), mask_im)
                else:
                    c = random.choice(slices)
                    slice = images[c[0]].crop(c[1])
                    if x == 0 - math.floor(pixels/2):
                        edge = slice
                    slices.remove(c)
                    if x == new_width - math.floor(pixels/2):
                        newim.paste(edge, (x, y), mask_im)
                    newim.paste(slice, (x, y), mask_im)
                    mask_im = mask_im.transpose(Image.ROTATE_180)
            x += math.floor(pixels/2)
        x = 0 - math.floor(pixels/2)
        y += altitude
    return(newim)


def v_equistitch(images, pixels=100):
    width = round(0.5 * math.sqrt(3) * pixels)
    mask_im = Image.new("L", (width*3, pixels*3), 0)
    draw = ImageDraw.Draw(mask_im)
    draw.polygon(
        [(0, 0), (width*3, round(pixels/2)*3), (0, pixels*3)],
        fill=255)
    mask_im = mask_im.resize((width, pixels), Image.ANTIALIAS)
    slices = iter_slices(images, (width, pixels))
    sqr = math.floor(math.sqrt(math.floor(len(slices)/2)))-1
    print(sqr)
    new_height = sqr*pixels
    new_width = sqr*width
    newim = Image.new("RGB", (new_width, new_height), (100, 255, 255))
    y = 0 - math.floor(pixels/2)
    x = 0
    while x < new_width:
        while y < new_height:
            if slices != []:
                if y == new_height - math.floor(pixels/2):
                    newim.paste(edge, (x, y), mask_im)
                else:
                    c = random.choice(slices)
                    slice = images[c[0]].crop(c[1])
                    if y == 0 - math.floor(pixels/2):
                        edge = slice
                    slices.remove(c)
                    if y == new_height - math.floor(pixels/2):
                        newim.paste(edge, (x, y), mask_im)
                    newim.paste(slice, (x, y), mask_im)
                    mask_im = mask_im.transpose(Image.ROTATE_180)
            y += math.floor(pixels/2)
        y = 0 - math.floor(pixels/2)
        x += width
    return(newim)


def gridstitch(images, pixels=100):
    if random.getrandbits(1) == 0:
        im = vstitch(images, pixels=pixels)
        imtwo = vstitch(images, pixels=pixels)
        im = hstitch([im, imtwo], pixels=pixels)
    else:
        im = hstitch(images, pixels=pixels)
        imtwo = hstitch(images, pixels=pixels)
        im = vstitch([im, imtwo], pixels=pixels)
    return(im)


def gridimpose(images, pixels=100):
    image = gridstitch(images, pixels=pixels)
    im = gridstitch(images, pixels=pixels)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    if image.mode != 'RGB':
        image = image.convert('RGB')
    if random.getrandbits(1) == 0:
        im = ImageChops.darker(image, im)
    else:
        im = ImageChops.lighter(image, im)
    return(im)


def vimpose(images, pixels=100):
    image = vstitch(images, pixels=pixels)
    im = random.choice([hstitch, vstitch])(images, pixels=pixels)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    if image.mode != 'RGB':
        image = image.convert('RGB')
    im = random.choice([ImageChops.darker, ImageChops.lighter])(image, im)
    return(im)


def himpose(images, pixels=100):
    image = hstitch(images, pixels=pixels)
    im = random.choice([hstitch, vstitch])(images, pixels=pixels)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    if image.mode != 'RGB':
        image = image.convert('RGB')
    im = random.choice([ImageChops.darker, ImageChops.lighter])(image, im)
    return(im)


def shift(im, pixels, dir='N'):
    if dir == 'N':
        coords = (0, 0-pixels)
        offset = (0, im.height-pixels)
    elif dir == 'S':
        coords = (0, pixels)
        offset = (0, (0-im.height)+pixels)
    elif dir == 'E':
        coords = (pixels, 0)
        offset = ((0-im.width)+pixels, 0)
    elif dir == 'W':
        coords = (0-pixels, 0)
        offset = (im.width-pixels, 0)
    newimage = Image.new('RGB', im.size)
    newimage.paste(im, coords)
    newimage.paste(im, offset)
    return newimage


def cgiffify(images, fpath, nframes, p):
    im = circstitch(images, pixels=p)
    frames = []
    pixels = im.height//nframes
    for x in range(0, im.height-pixels, pixels):
        frame = Image.new('RGB', im.size)
        left = 0
        dir = 'N'
        while left < im.width:
            if dir == 'N':
                dir = 'S'
            else:
                dir = 'N'
            i = im.crop([left, 0, left+p, im.height])
            i = shift(i, x, dir=dir)
            frame.paste(i, (left, 0))
            left += p
        frames.append(frame)
    im.save(fpath, save_all=True, append_images=frames, loop=10)


def hgiffify(image, fpath, nframes, p):
    frames = []
    pixels = image.height//nframes
    for x in range(0, image.height-pixels, pixels):
        frame = Image.new('RGB', image.size)
        left = 0
        dir = 'N'
        while left < image.width:
            if dir == 'N':
                dir = 'S'
            else:
                dir = 'N'
            i = image.crop([left, 0, left+p, image.height])
            i = shift(i, x, dir=dir)
            frame.paste(i, (left, 0))
            left += p
        frames.append(frame)
    image.save(fpath, save_all=True, append_images=frames, loop=10)


def vgiffify(image, fpath, nframes, p):
    frames = []
    pixels = image.height//nframes
    for x in range(0, image.height-pixels, pixels):
        frame = Image.new('RGB', image.size)
        upper = 0
        dir = 'E'
        while upper < image.height:
            if dir == 'E':
                dir = 'W'
            else:
                dir = 'E'
            i = image.crop([0, upper, image.width, upper-p])
            i = shift(i, x, dir=dir)
            frame.paste(i, (0, upper))
            upper += p
        frames.append(frame)
    image.save(fpath, save_all=True, append_images=frames, loop=10)


def getimage(files, minh=0, minw=0):
    file = None
    while file is None:
        try:
            im = Image.open(random.choice(files))
            if im.height >= minh and im.width >= minw:
                file = im
        except Exception as e:
            print(e)
    if file.mode != 'RGB':
        file = file.convert('RGB')
    return file


funcs = {
    'gridimpose': gridimpose, 'vimpose': vimpose, 'himpose': himpose,
    'tristitch': tristitch, 'vstitch': vstitch, 'hstitch': hstitch,
    'gridsstitch': gridstitch, 'circmerge': circmerge,
    'circstitch': circstitch, 'equi': equistitch, 'vequi': v_equistitch}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='collage some pictures')
    parser.add_argument(
        'input', metavar='i', type=str, help='input directory')
    parser.add_argument(
        'output', metavar='0', type=str, help='output directory')
    parser.add_argument(
        '--number', '-n', type=int, default=10,
        help='number of collages to create')
    parser.add_argument(
        '--function', '-f', nargs='+', choices=funcs.keys(),
        default=funcs.keys(), help='functions to use')
    parser.add_argument(
        '--min', type=int,
        default=50, help='minimum pixel slice')
    parser.add_argument(
        '--max', type=int,
        default=100, help='maximum pixel slice')
    parser.add_argument(
        '--minheight', type=int,
        default=0, help='minimum height of source image')
    parser.add_argument(
        '--minwidth', type=int,
        default=0, help='maximum height of source image')

    args = parser.parse_args()
    functions = [funcs[func] for func in args.function]
    i_exts = ['.jpg', 'jpeg', '.png', '.tif', '.tiff', '.gif']
    files = [
        os.path.join(args.input, file) for file in os.listdir(args.input)
        if os.path.splitext(file)[1] in i_exts]
    for i in range(args.number):
        pixels = random.randint(args.min, args.max)
        im1 = getimage(files, minh=args.minheight, minw=args.minwidth)
        im2 = getimage(files, minh=args.minheight, minw=args.minwidth)
        coll = random.choice(functions)([im1, im2], pixels=pixels)
        fname = os.path.join(args.output, f'collage_{i}.jpg')
        print('Saving ', fname)
        coll.save(fname)
