import requests

def get_avatar():
    url = "http://adm.hbbclub.com/bcast/admin/ajax/users-query.do"
    number = ""
    data = {
        "page_number":number,
        # "page_size":100,
        "keyword":"",
        # "searchDateStart":"2018年01月01日",
        # "searchDateEnd":"2019年09月27日"
    }
    header = {
        "Authorization":"Basic ZGFsb25nOnArTW1seEpjYzFTajJSR3BabGVTTHlRVXZXQlppVzJtSGgzZmhMTGJVMDQ9"
    }
    num = 0
    for i in range(2000):
        data["page_number"]=i+1
        response = requests.post(url,data=data,headers=header)
        json_response = response.json()
        # print(response.json())
        page_count = len(json_response["lstUser"])
        if page_count > 0:
            num+=page_count
        # print(page_count)
        else:
            break
    print(num)
get_avatar()