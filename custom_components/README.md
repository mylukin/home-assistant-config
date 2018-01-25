# 自定义组件

## alexa_intent

Alexa 播放网易云音乐

```yaml
# 播放私人FM
PlayPersonalFMIntent:
  speech:
    text: >-
      {{ [
        "OK",
        "Done",
        "No worries",
        "No Problem",
        "Enjoy your music"
      ] | random }}

  directives:
    type: play
    audio_type: api
    audio_url: https://music.lukin.cn/recommend.json
```

https://music.lukin.cn/recommend.json 内容如下：

```json
[
    {
        "id": 450612833,
        "name": "远方的姑娘我想念你 你可知道",
        "ar": "秋野",
        "title": "远方的姑娘我想念你 你可知道 - 秋野",
        "url": "https:\/\/music.lukin.cn\/song_450612833.m3u"
    },
    {
        "id": 447938650,
        "name": "第一次旅行（2016现场版）",
        "ar": "小海",
        "title": "第一次旅行（2016现场版） - 小海",
        "url": "https:\/\/music.lukin.cn\/song_447938650.m3u"
    },
    {
        "id": 511215976,
        "name": "野居",
        "ar": "张小九",
        "title": "野居 - 张小九",
        "url": "https:\/\/music.lukin.cn\/song_511215976.m3u"
    }
]
```

## moji_weather

墨迹天气数据

```yaml
sensor:
    - platform: moji_weather
      name: Moji Weather
      monitored_conditions:
        - weather
        - weather_current
        - weather_tips
        - temperature
        - temp_min
        - temp_max
        - wind_grade
        - air_quality
        - humidity
      scan_interval: 1800
```