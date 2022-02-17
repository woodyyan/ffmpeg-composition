# 视频处理

传入视频处理需要的参数，就可以对视频进行相关的处理。目前仅支持对单个视频进行处理。

> 💡 目前不支持大小超过500M的视频。

**支持的功能列表：**

1. 添加文字
    1. 支持指定文字位置
    2. 支持指定文字大小
    3. 支持文字底层蒙版可配置
    4. 支持指定文字颜色`待开发`
    5. 支持修改文字字体
    6. 支持不同文字指定不同字体
    7. 支持文字出场入场动画`待开发`
    8. 支持给文字添加半透明底板
2. 视频转换
    1. 转换分辨率，横屏变竖屏，上下补黑边
    2. 2.0支持转换码率和帧率`待开发`
3. 添加图片
    1. 支持指定图片位置和大小
    2. 2.0支持指定图片形状`待开发`
4. 上传视频
   1. 支持上传VOD
   2. 支持指定分类文件夹
   3. 支持结果回调
    

请求JSON：

```jsx
{
    "Action": "CompositionVideo",
    "Data": {
        "Input": {
            "URL": "xxxx",
            "Audio": true,
            "CallbackURL": "https://xxxx/release/callback",
            "Resolution": {
                "Width": 1600,
                "Height": 900
            },
            "Framerate": 15,
            "Bitrate": 500,
            "Texts": [
                {
                    "Content": "xxxx",
                    "X": 1,
                    "Y": 2,
                    "Size": 3,
                    "EnableBox": true,
                    "Font": "STHeitiLight.ttc"
                },
                {
                    "Content": "xxxx",
                    "X": 1,
                    "Y": 2,
                    "Size": 3,
                    "EnableBox": false,
                    "Font": "STHeitiLight.ttc"
                }
            ],
            "Pictures": [
                {
                    "URL": "xxxx.jpg",
                    "X": 1,
                    "Y": 2,
                    "Width": 3,
                    "Height": 3,
                }
            ]
        },
        "Output": {
            "Vod": {
                "Region": "ap-beijing",
                "SubAppId": 101, 
                "ClassId": 0
            }
        }
    }
}
```

字段解释

| 字段 | 类型 | 解释 |
| --- | --- | --- |
| URL | string | 要处理的视频链接 |
| Audio | bool | 是否保留音频 |
| CallbackURL | string | 回调URL |
| TargetVideoSpec.Resolution | int | 目标分辨率 |
| TargetVideoSpec.Framerate | int | 目标帧率 |
| TargetVideoSpec.Bitrate | int | 目标码率 |
| Texts | list | 要添加的多种文字，x,y表达式请参考下面。 |
| Text.EnableBox | bool | 默认值是false，如果为true则表示给文字加上底部蒙层 |
| Text.Font | string | 指定该文字要用的字体，不填就是默认字体。字体文件放在层里面，这里参数名只需填文件名，如STHeitiLight.ttc。字体文件直接打包上传层，不需要添加文件夹。需要在函数中绑定层。 |
| Pictures | list | 要添加的多张图片 |
| Region | int | 要上传的VOD的地域 |
| SubAppId | int | 要上传的VOD的subappid |
| ClassId | int | 要上传的VOD的分类ID(默认值0) |

Texts的x和y支持以下表达式：
- Top left: `x=0:y=0` (with 10 pixel padding `x=10:y=10`)
- Top center: `x=(w-text_w)/2:y=0` (with 10 px padding `x=(w-text_w)/2:y=10`)
- Top right: `x=w-tw:y=0` (with 10 px padding: `x=w-tw-10:y=10`)
- Centered: `x=(w-text_w)/2:y=(h-text_h)/2`
- Bottom left: `x=0:y=h-th` (with 10 px padding: `x=10:y=h-th-10`)
- Bottom center: `x=(w-text_w)/2:y=h-th` (with 10 px padding: `x=(w-text_w)/2:y=h-th-10`)
- Bottom right: `x=w-tw:y=h-th` (with 10 px padding: `x=w-tw-10:y=h-th-10`)

成功回调JSON：

```jsx
{
    "Result": "Success",
    "Data": {
        "OutputUrl": "xxxxx"
    },
    "RequestId": "xxxxxx"
}
```

失败回调JSON：

```jsx
{
    "Result": "Failure",
    "ErrorCode": "InternalError",
    "ErrorMessage": "internal error: xxxx",
    "RequestId": "xxxx"
}
```