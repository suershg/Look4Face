from django.shortcuts import render, redirect
from django.conf import settings
from PIL import Image
from align.detector import detect_faces
from align.align_trans import get_reference_facial_points, warp_and_crop_face
import numpy as np
import logging
import os
import datetime
logging.basicConfig(filename="look4face.log", level=logging.INFO)
MEDIA_PATH = settings.MEDIA_ROOT
CROPS_PATH = 'crops'
reference = get_reference_facial_points(default_square = True)


def main(request):
    """Displays the main page
    
    Arguments:
        request {[type]} -- [description]
    """
    # logger = logging.getLogger('main')
    # ОТОБРАЖАЕМ СТРАНИЦУ
    if request.method == 'GET':
        # try:
        context = {
            'title': 'Look4Face',
            }
        return render(request, 'index.html', context)
        # except Exception as e:
        #     logger.error(f'GET-request, {str(e)}')
        #     return redirect('Main Page')

    # ЗАГРУЗИЛИ НОВУЮ ФОТКУ
    elif request.method == 'POST':
        # INITIAL SEARCH
        if request.POST.get('refine') == "False":
            image = request.FILES.get('photo')
            image_type = image.name.split('.')[-1] #png/jpg/jpeg
            now = datetime.datetime.now()
            image_path = f'{now.day}{now.month}{now.year}_{now.hour}:{now.minute}:{now.second}.{image_type}'
            full_path = os.path.join(MEDIA_PATH, image_path)
            with open(full_path, 'wb+') as destination:
                destination.write(image.read())
            img = Image.open(full_path)
            _, landmarks = detect_faces(img) #TODO: change onet/rnet/pnet path
            count = landmarks.shape[0]
            if count == 0:
                pass
                return
                # there are no faces on the photo
                # TODO: send message
            elif count == 1:
                img = align_face(img, landmarks[0]) # cropped aligned face, ready for search
                # ...

                return render(request, 'results.html', context)

            else:
                face_urls = refine_face(img, landmarks, image_path)
                context = {
                    'title': 'Choose face',
                    'faces_list': face_urls,
                }
                return render(request, 'refine.html', context)
        # SEARCH AFTER REFINING
        elif request.POST.get('refine') == "True":
            image_path = request.POST.get('imagecrop') # number selected face
            full_path = os.path.join(MEDIA_PATH, image_path)
            img = Image.open(full_path) # cropped aligned face, ready for search



def search(img, landmarks):
    img = align_face(img, landmarks) #aligned 112x112 face
    # feature extraction


# def extract_features(img, landmarks):
#     """Extract face features
    
#     Arguments:
#         img {[type]} -- crop of image with face
#     """
#     aligned_image = align_face(img, landmarks)


def align_face(img, landmarks, crop_size=112):
    facial5points = [[landmarks[j], landmarks[j + 5]] for j in range(5)]
    warped_face = warp_and_crop_face(np.array(img), facial5points, reference, crop_size=(crop_size, crop_size))
    img_warped = Image.fromarray(warped_face)
    return img_warped


def refine_face(img, landmarks, image_path):
    count = landmarks.shape[0]
    face_urls = []
    for i in range(count):
        # face = img.resize((224, 224), box=bounding_boxes[i][:4])
        face = align_face(img, landmarks[i], crop_size=112) # try 224x224
        # face = img.crop(bounding_boxes[i][:4])
        # face = face.resize((175,175))
        face.save(os.path.join(MEDIA_PATH, CROPS_PATH, f'{i}_{image_path}'))
        face_urls.append(os.path.join(CROPS_PATH, f'{i}_{image_path}'))
    return face_urls