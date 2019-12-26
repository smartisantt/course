import json
import logging

import requests
import ffmpy

from urllib3 import encode_multipart_formdata
from utils.clientJsSDK import JsSdk


class GetWechatFile(JsSdk):
    """获取微信文件"""

    def __init__(self):
        JsSdk.__init__(self)
        self.file_host = "http://file.api.weixin.qq.com/cgi-bin/media/get"
        self.upload_host = "https://xcxupload.hbbclub.com/api/oss/upload"

    def get_file(self, access_token, fileId, path):
        url = self.file_host + "?access_token={0}&media_id={1}".format(access_token, fileId)
        try:
            r = requests.get(url)
            if r.status_code != 200:
                return False
            with open(path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logging.error(str(e))
            return False
        return True

    def put_file(self, filePath):
        with open(filePath, "rb") as f:
            file_content = f.read()
            file_name = filePath
            file_data = {
                "file": (file_name, file_content)
            }
            encode_data = encode_multipart_formdata(file_data)
            headers = {
                "Content-Type": encode_data[1]
            }
            res = requests.post(self.upload_host, headers=headers, data=encode_data[0])
            return json.loads(res.content.decode("utf-8"))

    def transformat_voice(self, amrPath, mp3Path):
        try:
            ff = ffmpy.FFmpeg(inputs={amrPath: None}, outputs={mp3Path: None})
            print(ff.cmd)
            ff.run()
        except Exception as e:
            logging.error(str(e))
            return False
        return True


if __name__ == "__main__":
    fileServer = GetWechatFile()
    fileServer.transformat_voice()
