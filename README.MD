# 视频处理

传入视频处理需要的参数，就可以对视频进行相关的处理。目前仅支持对单个视频进行处理。

> 💡 目前不支持大小超过500M的视频。

**支持的功能列表：**

1. 添加文字
    1. 1.0支持指定文字位置
    2. 1.0支持指定文字大小
    3. 2.0支持指定文字颜色`待开发`
    4. 2.0支持修改文字字体`待开发`
    5. 3.0支持文字出场入场动画`待开发`
    6. 4.0支持给文字添加半透明底板`待开发`
2. 视频转换
    1. 转换分辨率，横屏变竖屏，上下补黑边
    2. 2.0支持转换码率和帧率`待开发`
3. 添加图片
    1. 1.0支持指定图片位置和大小
    2. 2.0支持指定图片形状`待开发`
    

请求JSON：

```jsx
{
    "Action": "SpliceVideo",
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
                    "Size": 3
                },
                {
                    "Content": "xxxx",
                    "X": 1,
                    "Y": 2,
                    "Size": 3
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
                "SubAppId": 101
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
| Texts | list | 要添加的多种文字 |
| Pictures | list | 要添加的多张图片 |
| Region | int | 要上传的VOD的地域 |
| SubAppId | int | 要上传的VOD的subappid |

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