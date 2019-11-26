import requests


class HbbLogin(object):
    """好呗呗登录"""

    def __init__(self):
        self.host = "http://sns.hbbclub.com/api.php?mod=Oauth&act=authorize&login={0}&password={1}&api_type=sociax&api_version=4.6.0"

    def check_login(self, tel, password):
        responseResult = requests.get(self.host.format(tel, password))
        return responseResult.content.decode()


if __name__ == "__main__":
    hbb = HbbLogin()
    print(hbb.check_login("18487241833", "123256"))
