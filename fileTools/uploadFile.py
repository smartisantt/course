import base64
import json
import os

import requests
from urllib3 import encode_multipart_formdata



class UploadTool():
    def __init__(self):
        self.host = "https://appupload.hbbclub.com"
        self.local = "/api/oss/upload"

    def put_file(self, filePath, fileName="res.png"):
        with open(filePath, "rb") as f:
            url = "{0}{1}".format(self.host, self.local)
            file_content = f.read()
            file_name = fileName
            file_data = {
                "file": (file_name, file_content)
            }
            encode_data = encode_multipart_formdata(file_data)
            headers = {
                "Content-Type": encode_data[1]
            }
            res = requests.post(url, headers=headers, data=encode_data[0])
            return json.loads(res.content.decode("utf-8"))

def delete_file(fileList):
    """删除文件"""
    for fileName in fileList:
        if os.path.exists(fileName):
            os.remove(fileName)


def get_base64(info, fType="user"):
    fileObj = info.split(".com/")[1]
    if fType == "course":
        fileObj += "?x-oss-process=image/resize,w_600,h_439"
    encodestr = base64.b64encode(fileObj.encode('utf-8'))
    return str(encodestr, 'utf-8')


def get_base64_txt(info):
    encodestr = base64.b64encode(info.encode('utf-8'))
    return str(encodestr, 'utf-8')


if __name__ == "__main__":
    upload = UploadTool()
    upload.put_file(r".\res.png")
    print(get_base64("file3174320402509.png"))
    # print(BASE_DIR)
    # print(os.path.join(BASE_DIR, 'imageTools'))
