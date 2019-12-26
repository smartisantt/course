import os, django
import json
import logging
import threading
import time
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parentscourse_server.settings")
django.setup()

import requests
from aliyunsdkimm.request.v20170906 import CreateOfficeConversionTaskRequest, GetOfficeConversionTaskRequest
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth.credentials import StsTokenCredential

from common.models import CoursePPT, LiveCourseBanner

sts_token_url = "https://aiupload.hbbclub.com/api/oss/sts"
imm_project = "adspreview"                  # 阿里云多媒体项目
region_id = "cn-beijing"                    # oss的地区
# bucket = "hbb-ads"
# srcUri = "oss://" + bucket + "/"
# tgtUri = "oss://" + bucket + "/hbbcourse/ppt/"
tgtType = "png"                             # ppt转成图片的格式



def get_sts_token(token=None):
    # url = '{0}{1}'.format(self.sts_token_host, self.sts_token_url)
    url = sts_token_url
    # headers = {'token': token}

    try:
        re = requests.get(url)
        # re = requests.get(url, headers=headers)
        if re.status_code == 200:
            if re.json().get('data'):
                data = re.json().get('data')
                accessKeyId = data["credentials"]["accessKeyId"]
                accessKeySecret = data["credentials"]["accessKeySecret"]
                securityToken = data["credentials"]["securityToken"]
                sts_token_credential = StsTokenCredential(accessKeyId, accessKeySecret, securityToken)
                client = AcsClient(region_id=region_id, credential=sts_token_credential)
                return client
        return
    except Exception as e:
        logging.error(e)
        return


def change(client, source, bucket="hbb-ads"):
    # 单个文档的转换请求，它是异步接口，会快速返回任务ID
    createReq = CreateOfficeConversionTaskRequest.CreateOfficeConversionTaskRequest()
    createReq.set_Project(imm_project)  # 智能媒体管理 配置
    createReq.set_SrcUri("oss://" + bucket + "/" + source)
    createReq.set_TgtUri("oss://" + bucket + "/hbbcourse/ppt/" + source.split(".")[0] + "/")
    createReq.set_TgtType(tgtType)
    response = client.do_action_with_exception(createReq)
    res = json.loads(response)
    taskId = res["TaskId"]
    print(taskId)
    return taskId


def get_res(client, taskId, sourceUrl, liveCourseBannerId):
    period = 5
    timeout = 120
    start = time.time()
    getReq = GetOfficeConversionTaskRequest.GetOfficeConversionTaskRequest()
    getReq.set_Project(imm_project)
    getReq.set_TaskId(taskId)
    while True:
        time.sleep(period)
        response = client.do_action_with_exception(getReq)
        print(response)
        status = json.loads(response)["Status"]
        print(status)
        if status == "Finished":  # 任务完
            pageCount = json.loads(response)["PageCount"]               # ppt页数
            liveCourseBanner = LiveCourseBanner.objects.filter(uuid=liveCourseBannerId).first()
            liveCourseBanner.pages = pageCount
            liveCourseBanner.save()
            # sourceUrl(前端传的) -》imgUrl(数据库存储格式)
            # sourceUrl "https://hbb-ads.oss-cn-beijing.aliyuncs.com/file1182754557408.ppt",
            # imgUrl https://hbb-ads.oss-cn-beijing.aliyuncs.com/hbbcourse/ppt/file1182754557408/1.png
            temp = sourceUrl.split("/")
            temp.insert(3, "hbbcourse/ppt")
            temp[-1] = temp[-1].split(".")[0]
            url = "/".join(temp)
            ppt_list_to_insert = []

            for x in range(pageCount):
                ppt_list_to_insert.append(
                    CoursePPT(
                        imgUrl="{}/{}.png".format(url, x+1),
                        sortNum=x+1,    # 从1开始排序
                        enable=1,
                        liveCourseBanner_id=liveCourseBannerId
                    )
                )
            CoursePPT.objects.bulk_create(ppt_list_to_insert)
            print("Task finished.")
            break
        if status == "Failed":  # 任务失败
            print("Task failed.")
            break
        if time.time() - start > timeout:  # 任务超时
            print("Task timeout.")
            break


def get_res2(client, taskId):
    getReq = GetOfficeConversionTaskRequest.GetOfficeConversionTaskRequest()
    getReq.set_Project(imm_project)
    getReq.set_TaskId(taskId)

    response = client.do_action_with_exception(getReq)
    status = json.loads(response)

    return status

if __name__ == '__main__':
    cli = get_sts_token()
    # taskid = change(cli, "5dc5678f16d3fc10511c4cfa.ppt")
    # t = threading.Thread(target=get_res, args=(cli, taskid,
    #     "https://airobot-test.oss-cn-beijing.aliyuncs.com/5dc5678f16d3fc10511c4cfa.ppt"))
    # t.start()
    # print("end")

    # https://hbb-ads.oss-cn-beijing.aliyuncs.com/hbbcourse/ppt/file1182754557408/1.png
    print(get_res("C6500ABB-1A3F-4D7A-8DFC-B7E50ED94C45"))
