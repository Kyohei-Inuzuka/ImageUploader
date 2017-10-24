#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import imghdr
from PIL import Image
import boto3
from botocore.exceptions import ClientError, ParamValidationError
from bootstrap import CONFIG

class ImageUploader(object):
    """ ImageUploader """

    def __init__(self):
        pass

    @staticmethod
    def resize_image(filepath):
        """ サムネイル作成 """
        path, ext = os.path.splitext(os.path.basename(filepath))
        out_file = path + CONFIG['THUMBNAIL_PREFIX'] + ext
        thumb_dir = CONFIG['THUMBNAIL_FILE_ROOT']
        thumb_width = CONFIG['THUMBNAIL_WIDTH']

        try:
            if os.path.exists(thumb_dir) is False:
                os.makedirs(thumb_dir)
            img = Image.open(filepath)
            wpercent = thumb_width / float(img.size[0])
            hsize = int((float(img.size[1]) * float(wpercent)))

            img.resize((thumb_width, hsize)).save(thumb_dir + out_file)
        except IOError as err:
            print 'IOError: ' + err.message


    @staticmethod
    def get_image_list():
        """ ディレクトリ配下の画像ファイルのリストを取得する """
        file_list = []
        for (root, dirs, files) in os.walk(CONFIG['IMAGE_FILE_ROOT']):
            for f_item in files: 
                target = os.path.join(root, f_item).replace("\\", "/")
                if os.path.isfile(target):
                    if imghdr.what(target) != None:
                        file_list.append(target)
        return file_list

    @staticmethod
    def upload_to_s3():
        """ S3ディレクトリ配下のファイルを一括でアップロードする """
        s3_root = CONFIG['S3_ROOT']
        session = boto3.session.Session(aws_access_key_id=CONFIG['AWS_ACCESS_KEY_ID'],
                                        aws_secret_access_key=CONFIG['AWS_SECRET_ACCESS_KEY'],
                                        region_name=CONFIG['S3_REGION'])
        client = session.resource('s3').meta.client


        for (root, dirs, files) in os.walk(s3_root):
            for f_item in files:
                filename = os.path.join(root, f_item).replace("\\", "/")
                try:
                    client.upload_file(filename, CONFIG['S3_BUCKETNAME'], filename.replace(s3_root, ""))
                except ParamValidationError as err:
                        print "ParamValidationError : %s" % err
                except ClientError as err:
                    if err.response['Error']['Code'] == 'EntityAlreadyExists':
                        print "User already exists"
                    else:
                        print "Unexpected error: %s" % err
                except IOError as err:
                    print 'IOError: ' + err.message


if __name__ == '__main__':
    IU = ImageUploader()
    IMGFILELIST = IU.get_image_list()
    for item in IMGFILELIST:
        IU.resize_image(item)
    IU.upload_to_s3()
    