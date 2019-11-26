# H5模型定义
## 轮播图模型(banner)
```
{
    "uuid":"string",
    "name":"string",
    "icon":"string",
    "type":int,
    "target":"string"
}
````
## 标签模型(tags)
```
{
    "uuid":"string",
    "name":"string",
}
```
## 首页模块模型(section)
```
{
    "name":"string",
    "uuid":"string",
    "courses":[
        {courses模型}，
        ...
    ],
    "showType":int,
}
```
## 课程列表模型（courses）
```
{
    "uuid":"string",
    "name":"string",
    "startTime":int,
    "endTime":int,
    "icon":"string",
    "intro":"string", 
    "originalPrice":int, 
    "realPrice":int, 
    "courseType":int, 
    "duration":int,
    "expert":{
        专家模型
    },
    "vPopularity"：int，  
}

```
## 专家模型(expert)
```
{
   "uuid":"string",
   "name":"string",
   "avatar":"string",
   "hospital":"string",
   "department":"string",
   "jobTitle":"sting"
}

```
## 讨论消息模型(userMsg)--->依据原有数据库模型定义
```
{
    "avatar":"string",
    "username":"string",
    "role":"txt",
    "type":"string",
    "isQuestion":Bool,
    "content":"string"
}
```
## 专家消息模型(expertMsg)--->依据原有数据库模型定义
### 发送文字模型
```
{
    "avatar":"string",
    "username":"string",
    "role":"expert",
    "type":"txt",
    "isQuestion":false,
    "content":"string"
}
```
### 发送语音模型
```
{
    "avatar":"string",
    "username":"string",
    "role":"expert",
    "type":"voice",
    "fileKey":"string",
    "duration":4
}
```
### 发送图片模型
```
{
    "avatar"string",
    "username":"string",
    "role":"expert",
    "type":"img",
    "fileKey":"string",
    "width":3120,
    "height":4160,
    "size":799278
}
```
### 删除的信息（待定）
```
{
    "avatar":"string",
    "username":"string",
    "role":"compere",
    "type":"del",
    "seq":9,
    "op":222
}
```
### 发送ppt某一张图片
```
{
    "avatar":"string",
    "username":"Victoria",
    "role":"compere",
    "type":"ppt-pos",
    "id":131
}

```
### 回复模型
```
{
    "avatar":"string",
    "username":"string",
    "role":"compere",
    "type":"qna",
    "question":{
        "seq":598,(信息id)
        "avatar":"string",
        "username":"string",
        "role":"normal",
        "type":"txt",
        "isQuestion":false,
        "content":"string"
    },
    "answer":"string"
}
```

# 课件模型(courseSource)
```
{
    "uuid":string,
    "name":string
    "url":string
    "sourceType":1代表音频，2代表视频，3代表PPT
    "fileSize":int64,
    "duration":int64,
}
```
# 用户模型（user）
```
    "user": {
        "uuid": "5bb015976ff1457a9eb5825d04b7eec4",
        "nickName": "陈泽1",
        "avatar": "http://sns.hbbclub.com/data/upload/avatar/23/cf/11/original_100_100.jpg",
        "gender": 1,
        "intro": "",
        "birthday": null,
        "point": 0,
        "remark": null,
        "roles": "3",
        "location": "北京 北京市 东城区"
    }
```

# 聊天室内存定义
```
{
    "roomUuid1":{
        "userUuid1":{
            用户信息对象
        },
        "userUuid2":{
            用户信息对象
        },
    },
    "roomUuid2":{
        "userUuid1":{
            用户信息对象
        },
        "userUuid2":{
            用户信息对象
        },
    },
}
```

## message结构定义
```
# 专家、嘉宾、主持人
{
    type:string,
    content:string,
    msgSeq:int,
    msgTime:int,
    duration:int,
    question:{ #当type为回复类型时才会有该字段
        content:string,
        avatar:string,
        username:string,
        role:string,
        type:string,
        from_uid:string,
        from:string,
        seq:int,
    }
}

# 普通用户
{
    msgTime:int,
    isQuestion:bool,
    content:string,
}
```