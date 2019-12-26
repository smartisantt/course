import logging

import requests
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import qrcode

from parentscourse_server.config import DEFAULT_AVATAR, DEFAULT_SHARE_COURSE


def download_image(url, name, ftype="avatar"):
    """下载图片到本地"""
    r = requests.get(url)
    if r.status_code != 200:
        if ftype == "avatar":
            r = requests.get(DEFAULT_AVATAR)
        elif ftype == "course":
            r = requests.get(DEFAULT_SHARE_COURSE)
    with open(name, 'wb') as f:
        f.write(r.content)


def images_filter():
    imgF = Image.open(r".\first.png")
    outF = imgF.filter(ImageFilter.DETAIL)
    conF = imgF.filter(ImageFilter.CONTOUR)
    edgeF = imgF.filter(ImageFilter.FIND_EDGES)
    radiusF = imgF.UnsharpMask(radius=2, percent=150, threshold=3)
    imgF.show()
    outF.show()
    conF.show()
    edgeF.show()
    radiusF.show()


def circle_new(path):
    ima = Image.open(path).convert("RGBA")
    ima = ima.resize((72, 72))
    r2 = 72
    circle = Image.new('1', (r2, r2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, r2, r2), fill=(255))
    alpha = Image.new('RGBA', (r2, r2), (255, 255, 255, 255))
    alpha = alpha.convert("1")
    alpha.paste(circle, (0, 0))
    ima.putalpha(alpha)  # 蒙层图片
    # ima.show()
    # ima.save(r".\head.png")
    return ima


def circle_corder_image(path=None):
    im = Image.open(path).convert("RGBA")
    rad = 50  # 设置半径
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    im.show()
    # im.save('test_circle_corder.png')
    # return im


def create_code(url, QRcenter=r".\QRcenter.jpg"):
    qr = qrcode.QRCode(
        version=5, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image()
    img = img.convert("RGBA")
    icon = Image.open(QRcenter)  # 这里是二维码中心的图片

    img_w, img_h = img.size
    factor = 4
    size_w = int(img_w / factor)
    size_h = int(img_h / factor)

    icon_w, icon_h = icon.size
    if icon_w > size_w:
        icon_w = size_w
    if icon_h > size_h:
        icon_h = size_h
    icon = icon.resize((icon_w, icon_h), Image.ANTIALIAS)

    w = int((img_w - icon_w) / 2)
    h = int((img_h - icon_h) / 2)
    icon = icon.convert("RGBA")
    img.paste(icon, (w, h), icon)
    # img.show()  # 显示图片,可以通过save保存
    return img


def circle(path=r".\top.png"):
    ima = Image.open(path).convert("RGBA")
    size = ima.size
    # 因为是要圆形，所以需要正方形的图片
    r2 = min(size[0], size[1])
    if size[0] != size[1]:
        ima = ima.resize((r2, r2), Image.ANTIALIAS)
    imb = Image.new('RGBA', (r2, r2), (255, 255, 255, 0))
    pima = ima.load()
    pimb = imb.load()
    r = float(r2 / 2)  # 圆心横坐标
    for i in range(r2):
        for j in range(r2):
            lx = abs(i - r + 0.5)  # 到圆心距离的横坐标
            ly = abs(j - r + 0.5)  # 到圆心距离的纵坐标
            l = pow(lx, 2) + pow(ly, 2)
            if l <= pow(r, 2):
                pimb[i, j] = pima[i, j]
    # imb.save("test_circle.png")
    # imb.show()
    return imb


def code_tool(urlName=None, url=None, centerUrl=None, price=None, nickName=None, fontPath=None, logoPath=None,
              coursePath=None, avatarPath=None):
    target = Image.new('RGBA', (600, 696), "white")

    # 顶部宣传图
    box = (0, 0, 600, 439)  # 区域
    region = Image.open(coursePath)
    region = region.convert("RGBA")
    region = region.resize((600, 439))

    # 企业logo
    box1 = (0, 626, 600, 696)
    region1 = Image.open(logoPath)
    region1 = region1.convert("RGBA")
    region1 = region1.resize((600, 70))

    # 用户头像
    box2 = (20, 530, 92, 602)
    region2 = circle_new(avatarPath)
    region2 = region2.resize((72, 72))

    # 二维码
    box3 = (472, 461, 580, 569)
    region3 = create_code(url, centerUrl)
    region3 = region3.convert("RGBA")
    region3 = region3.resize((108, 108))

    # 粘贴图片
    target.paste(region, box)
    target.paste(region1, box1)
    target.paste(region2, box2)
    target.paste(region3, box3)

    # 写入介绍
    draw = ImageDraw.Draw(target)
    font = ImageFont.truetype(fontPath, 30)
    # (fl, il) = math.modf(price)
    # priceList = [str(il), str(int(fl * 10))]
    draw.text((20, 456), "成功邀请后，将获得", "#333333", font)
    draw.text((293, 456), str(price) + "元收益", "#FFCC33", font)

    # 写入昵称
    font1 = ImageFont.truetype(fontPath, 28)
    draw.text((101, 546), nickName + "推荐", "#333333", font1)
    # 写入固定文字
    font2 = ImageFont.truetype(fontPath, 24)
    draw.text((478, 573), "扫码购买", "#333333", font2)
    x, y = target.size
    p = Image.new('RGBA', target.size, (255, 255, 255))
    p.paste(target, (0, 0, x, y), target)
    # p.show()
    p.save(urlName)  # 保存图片


def get_res_url(backgroundUrl, avatarBase64, courseBase64=None, price=None, nickName=None):
    # text_Info1 = get_base64_txt("成功邀请后，将获得")
    # text_Info2 = get_base64_txt(str(price / 100) + "元收益")
    # text_Info3 = get_base64_txt(nickName + "推荐")
    # text_Info4 = get_base64_txt("扫码购买")

    resStr = backgroundUrl
    resStr += "?x-oss-process=image/resize,w_600,h_696"
    # resStr += "/watermark,image_" + logoBase64 + ",x_0,y_637"
    resStr += "/watermark,image_" + avatarBase64 + ",x_508,y_94/rounded-corners,r_30"
    # resStr += "/watermark,image_" + courseBase64 + ",x_0,y_0"
    # resStr += "/watermark,type_d3F5LXplbmhlaQ,size_30,text_" + text_Info1 + ",color_333333,x_20,y_456"
    # resStr += "/watermark,type_d3F5LXplbmhlaQ,size_30,text_" + text_Info2 + ",color_FFCC33,x_293,y_456"
    # resStr += "/watermark,type_d3F5LXplbmhlaQ,size_28,text_" + text_Info3 + ",color_333333,x_101,y_546"
    # resStr += "/watermark,type_d3F5LXplbmhlaQ,size_24,text_" + text_Info4 + ",color_333333,x_478,y_573"
    return resStr


if __name__ == "__main__":
    # main()
    # circle_new(r".\top.png").show()
    # circle()
    # circle_new(r".\avatar.jpg")
    # img = Image.open(r".\avatar.jpg")
    # transparent_back(circle_new(r".\avatar.jpg"))
    # transPNG("avatar.jpg")
    # code_tool("haha", "htt://www.baidu.com", r".\QRcenter.jpg", intro="haha", nickName="陈泽", fontPath=r".\wFont.ttf")
    # download_image("https://hbb-ads.oss-cn-beijing.aliyuncs.com/file417348768620.png",r".\logo.png")
    circle_corder_image(r".\top.png")
