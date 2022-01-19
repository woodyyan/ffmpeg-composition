# coding=utf-8

import json
import logging
import os
import subprocess
import sys
import time

import requests

from config import TENCENTCLOUD_SECRETID, TENCENTCLOUD_SECRETKEY
from parameters import Params
from picture import Picture
from qcloud_vod.model import VodUploadRequest
from qcloud_vod.vod_upload_client import VodUploadClient
from text import Text

cmd_path_ffmpeg = '/tmp/ffmpeg'
video_command = cmd_path_ffmpeg + ' -y -i %s -vf %s -c:v libx264 -x264-params nal-hrd=cbr:force-cfr=1 -b:v 400000 -bufsize 400000 -minrate 400000 -maxrate 400000 %s'
cmd_path_ffprobe = '/tmp/ffprobe'
cmd_query_video_info = cmd_path_ffprobe + ' -select_streams v -show_entries format=duration,size,bit_rate,filename -show_streams -v quiet -of csv="p=0" -of json -i %s'
cmd_download = "curl -o %s  '%s' -H 'Connection: keep-alive' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'  " \
               "-H 'Accept: */*' -H 'Referer: %s' -H 'Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en-HK;q=0.7,en;q=0.6' -H 'Range: bytes=0-' --compressed --insecure"

# 日志配置
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)


def main_handler(event, context):
    logger.info("start main handler")
    request_id = context.get('request_id')

    if "body" not in event.keys():
        return {"code": 410, "errorMsg": "event is not come from api gateway"}

    req_body = event['body']
    callback_url = ""
    try:
        params = extract_parameters(req_body)

        if not callback_url:
            logger.warning("Callback url是空的，请检查。")
    except Exception as err:
        logger.error("bad request: %s, please check." % (str(err)))
        callback_body = {
            "Result": "Failure",
            "ErrorCode": "InvalidParameter",
            "ErrorMessage": "Invalid parameter: " + str(err),
            "RequestId": request_id
        }
        callback(callback_url, callback_body)
        return json.dumps(callback_body)

    # 将ffmpeg文件复制到/tmp下并赋予执行权限
    subprocess.run(
        'cp ./ffmpeg /tmp/ffmpeg && chmod 755 /tmp/ffmpeg',
        shell=True)
    subprocess.run(
        'cp ./ffprobe /tmp/ffprobe && chmod 755 /tmp/ffprobe',
        shell=True)

    try:
        logger.info('开始下载视频：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        input_video_path = download(params.video_url)
        logger.info('视频下载完成：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        logger.info('开始处理视频：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        output_video = '/tmp/output.mp4'
        scale_param = calc_scale_param(input_video_path, params.width, params.height)
        child = subprocess.run(video_command % (input_video_path, scale_param, output_video),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, close_fds=True, shell=True)
        if child.returncode == 0:
            print("success:", child)
        else:
            print("error:", child)
            raise KeyError("拼接视频失败, 错误: ", child)
        logger.info('处理视频完成：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        logger.info('开始上传视频：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        uploaded_video_url = upload_vod(params.vod_region, params.sub_app_id, output_video)
        logger.info('视频上传完成：' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        callback_body = {
            "Result": "Success",
            "Data": {
                "OutputUrl": uploaded_video_url
            },
            "RequestId": request_id
        }
    except Exception as err:
        logging.error(err)
        callback_body = {
            "Result": "Failure",
            "ErrorCode": "InternalError",
            "ErrorMessage": "internal error: " + str(err),
            "RequestId": request_id
        }
        pass

    # 回调逻辑
    callback(callback_url, callback_body)

    # 清理工作目录
    # TODO
    # clear_files('/tmp/')

    return callback_body


def extract_parameters(req_body):
    req_param = json.loads(req_body)
    logger.info("输入参数: " + json.dumps(req_param))
    video_url = req_param['Data']['Input']['URL']
    audio = req_param['Data']['Input']['Audio']
    callback_url = req_param['Data']['Input']['CallbackURL']
    width = req_param['Data']['Input']['Resolution']['Width']
    height = req_param['Data']['Input']['Resolution']['Height']
    framerate = req_param['Data']['Input']['Framerate']
    bitrate = req_param['Data']['Input']['Bitrate']
    texts_json = req_param['Data']['Input']['Texts']
    texts = []
    for text in texts_json:
        content = text['Content']
        x = text['X']
        y = text['Y']
        size = text['Size']
        texts.append(Text(content, x, y, size))
    pictures_json = req_param['Data']['Input']['Pictures']
    pictures = []
    for picture in pictures_json:
        url = picture['URL']
        x = picture['X']
        y = picture['Y']
        picture_width = picture['Width']
        pictures.append(Picture(url, x, y, width))
    vod_region = req_param['Data']['Output']['Vod']['Region']
    sub_app_id = req_param['Data']['Output']['Vod']['SubAppId']
    return Params(video_url, audio, callback_url, framerate, height, width, texts, pictures, vod_region, sub_app_id)


# 回调逻辑。
def callback(url, data):
    if not url:
        logger.info("Callback url is empty, no need to callback.")
        return

    response = requests.post(url, json=data)
    logger.info("Callback response: %s" % str(response.text.encode('utf8')))


# 视频上传VOD，sdk自动选择普通上传还是分片上传
def upload_vod(vod_region, sub_app_id, media_file_path):
    secret_id = os.environ.get("TENCENTCLOUD_SECRETID")
    secret_key = os.environ.get("TENCENTCLOUD_SECRETKEY")
    token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN")
    if not vod_region:
        vod_region = os.environ.get('TENCENTCLOUD_REGION')

    client = VodUploadClient(secret_id, secret_key, token)
    request = VodUploadRequest()
    request.SubAppId = sub_app_id
    request.MediaFilePath = media_file_path
    response = client.upload(vod_region, request)
    logger.info("Upload Success. FileId: %s. MediaUrl: %s, RequestId: %s" % (response.FileId, response.MediaUrl,
                                                                             response.RequestId))
    return response.MediaUrl


def download(url):
    filename = os.path.basename(url).split('?')[0]
    (_filename, ext) = os.path.splitext(filename)
    download_file = os.path.join("/tmp", '%s_%s%s' %
                                 (_filename, int(round(time.time() * 1000)), ext))

    command = cmd_download % (download_file, url, url)
    logger.info("download media command: %s" % command)

    # 从url下载视频文件
    ret = subprocess.run(command, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True, check=True)
    if ret.returncode == 0:
        logger.info("下载[%s]完成, 详情: %s" % (url, ret.stdout))
    else:
        logger.info("下载[%s]失败, 错误: %s" % (url, ret.stderr))
        raise KeyError("下载[%s]失败, 错误: %s" % (url, ret.stderr))

    if os.path.exists(download_file):
        logger.info("下载[%s]成功, 本地文件路径：[%s]" % (url, download_file))
    else:
        logger.info("下载[%s]失败, 本地文件不存在。" % url)
        raise KeyError("下载[%s]失败, 本地文件不存在。" % url)

    return download_file


def clear_files(src):
    try:
        logger.info("clear work dir...")
        if os.path.isfile(src):
            os.remove(src)
        elif os.path.isdir(src):
            for item in os.listdir(src):
                itemsrc = os.path.join(src, item)
                clear_files(itemsrc)
    except Exception as err:
        logging.exception(err)
        pass


# 查询视频文件宽和高
def query_width_height(file_path):
    width = -1
    height = -1

    video_info = ffprobe_info(file_path)
    if video_info:
        width = video_info['streams'][0]['width']
        height = video_info['streams'][0]['height']

    logger.info("media file width[%s], height[%s]" % (width, height))

    return width, height


# 获取源视频信息，分辨率等
def ffprobe_info(file_path):
    video_info = None

    command = cmd_query_video_info % (file_path,)
    logger.info("ffprobe query file info command: %s" % (command,))
    ret = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         close_fds=True, shell=True)
    if ret.returncode == 0:
        logger.info('query file info command finished.')
        video_info = json.loads(ret.stdout)
    else:
        logger.warning('query file info command failed, ret code: {}, err: {}'.format(ret.returncode, ret.stderr))

    return video_info


def calc_scale_param(video_path, target_video_width, target_video_height):
    width, height = query_width_height(video_path)
    if width != target_video_width or height != target_video_height:
        scale_param = ""
        if width < target_video_width and height <= target_video_height:
            x = (target_video_width - width) / 2
            y = (target_video_width - height) / 2
            scale_param = "pad=%d:%d:%d:%d:black" % (target_video_width, target_video_height, x, y)
        else:
            if width > target_video_width:
                _width = target_video_width
                _height = height * target_video_width / width
                if _height <= target_video_height:
                    x = 0
                    y = (target_video_height - _height) / 2
                    scale_param = "scale=%d:%d,pad=%d:%d:%d:%d:black" % (
                        _width, _height, target_video_width, target_video_height, x, y)
                else:
                    _width = _width * target_video_height / _height
                    _height = target_video_height
                    x = (target_video_width - _width) / 2
                    y = 0
                    scale_param = "scale=%d:%d,pad=%d:%d:%d:%d:black" % (
                        _width, _height, target_video_width, target_video_height, x, y)
            else:
                if height > target_video_height:
                    _width = width * target_video_height / height
                    _height = target_video_height
                    x = (target_video_width - _width) / 2
                    y = 0
                    scale_param = "scale=%d:%d,pad=%d:%d:%d:%d:black" % (
                        _width, _height, target_video_width, target_video_height, x, y)
        return scale_param
    else:
        return ''


if __name__ == '__main__':
    event = {
        'body': '''{
                        "Action": "SpliceVideo",
                        "Data": {
                            "Input": {
                                "URL": "http://1500009267.vod2.myqcloud.com/6c9c6980vodcq1500009267/0d7032f3387702294461673432/pz3wNIkIjCEA.mp4",
                                            "Audio": true,
                                "CallbackURL": "https://enk885gn0j1qox.m.pipedream.net",
                                "Resolution": {
                                    "Width": 720,
                                    "Height": 1280
                                },
                                "Framerate": 15,
                                "Bitrate": 500,
                                "Texts": [
                                    {
                                        "Content": "xxxxxxxxxxx",
                                        "X": 1,
                                        "Y": 2,
                                        "Size": 30
                                    },
                                    {
                                        "Content": "YYYYYYY",
                                        "X": 1,
                                        "Y": 2,
                                        "Size": 20
                                    }
                                ],
                                "Pictures": [
                                    {
                                        "URL": "xxxx",
                                        "X": 1,
                                        "Y": 2,
                                        "Width": 3
                                    }
                                ]
                            },
                            "Output": {
                                "Vod": {
                                    "Region": "ap-beijing",
                                    "SubAppId": 1500009267
                                }
                            }
                        }
                    }'''
    }
    context = {
        "request_id": "123"
    }

    os.environ.setdefault("TENCENTCLOUD_SECRETID", TENCENTCLOUD_SECRETID)
    os.environ.setdefault("TENCENTCLOUD_SECRETKEY", TENCENTCLOUD_SECRETKEY)
    video_command = video_command.replace('/tmp/', '')
    cmd_query_video_info = cmd_query_video_info.replace('/tmp', '')
    main_handler(event, context)

    print('')
