# 爸妈课堂后端
2019/09/18 创建 
使用Django 完成后台


使用restframework框架

RESTful风格开发,路由格式：
```
    GET     /user/              获取所有用户列表
    GET     /user/<str:uuid>/   获取单个用户
    POST    /user/              创建用户
    PUT     /user/<str:uuid>/   修改用户
    DELETE  /user/<str:uuid>/   删除用户
```

接口报错信息
```
请求方法错误报错：
{
    "code": 405,
    "msg": "方法 “POST” 不被允许。"
}

没有有效token：
{
    "code": 403,
    "msg": "请提供有效的身份认证标识"
}

没有权限：
{
    "code": 403,
    "msg": "对不起，你没有权限"
}

请求的资源不存在：
{
    "code": 404,
    "msg": "未找到。"
}

```


client 为H5端
manager 为后台管理端

common 为共用的工具类方法和模型
