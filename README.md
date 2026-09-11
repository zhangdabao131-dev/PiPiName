# PiPiName

PiPiName 是一个本地中文取名和传统文化辅助工具。它根据三才五格筛选笔画组合，再从诗经、楚辞、论语、周易、唐诗、宋诗、宋词和常见姓名库中生成双字名候选，并支持姓名五格分析与基础八字排盘。

相关阅读可以[看这里](https://juejin.cn/post/6868186071260856334)。

> 结果只作为传统文化、文化出处和候选筛选辅助，不承诺命理正确性，也不替代人工或专业判断。

![PiPiName Web 界面](docs/assets/pipiname-web.png)

## 安装

需要先安装 Python 3.10 或更高版本。

```bash
pipx install .
```

## 启动

```bash
pipiname web --open
```

打开 `http://localhost:9191` 使用页面，打开 `http://localhost:9191/docs` 使用 API 文档。

## 部署到 Render

仓库根目录提供了 `render.yaml`，可以通过 Render Blueprint 部署为免费 Web Service：

1. 登录 [Render Dashboard](https://dashboard.render.com/)，连接 GitHub。
2. 选择 **New > Blueprint**，并选择本仓库。
3. 确认 Blueprint 名称和 `pipiname` 服务，然后点击部署。

构建脚本会验证 Git LFS 管理的 SQLite 索引；如果平台检出的是 LFS 指针，会自动下载真实数据库。服务使用 `/api/health` 作为健康检查地址。Render 免费实例可能在闲置后休眠，休眠后的首次访问需要等待冷启动。

网页提供三个功能区域：

- “智能起名”：生成带有古籍出处的双字名候选。
- “姓名分析”：查看单姓双字名的三才五格和名字来源。
- “八字排盘”：根据公历或农历出生日期生成四柱、十神、藏干、纳音、地势和五行表层分布。

八字排盘当前支持 1900—2100 年，按 `Asia/Shanghai` 中国标准时间计算，默认在 `00:00` 换日，也可以选择 `23:00` 晚子时换日。当前不进行出生地经度和真太阳时校正。

## API

### `GET /api/health`

返回索引状态和记录数。

### `GET /api/sources`

返回可用词库。

### `POST /api/names/generate`

请求示例：

```json
{
  "last_name": "林",
  "source": "shijing",
  "gender": "",
  "min_stroke": 3,
  "max_stroke": 30,
  "allow_general": false,
  "validate_name": true,
  "dislike_words": [],
  "limit": 100,
  "offset": 0
}
```

响应字段包含：

- `full_name`
- `first_name`
- `gender`
- `first_char`
- `second_char`
- `stroke1`
- `stroke2`
- `source_type`
- `source_title`
- `author`
- `sentence`

### `POST /api/names/check`

请求示例：

```json
{
  "name": "林蛋大",
  "with_resource": true
}
```

### `POST /api/bazi/calculate`

公历请求示例：

```json
{
  "calendar_type": "solar",
  "year": 1990,
  "month": 5,
  "day": 18,
  "hour": 14,
  "minute": 30,
  "is_leap_month": false,
  "timezone": "Asia/Shanghai",
  "day_boundary": "midnight",
  "gender": "男",
  "yun_sect": 1
}
```

农历日期将 `calendar_type` 设置为 `lunar`；如果输入的是闰月，同时将 `is_leap_month` 设置为 `true`。

响应包含：

- 公历和农历出生时间
- 生肖、时辰和日主
- 年柱、月柱、日柱、时柱
- 每柱的干支五行、阴阳、十神、藏干、藏干十神、纳音和地势
- 四柱干支的五行表层数量
- 性别决定的大运顺逆、起运岁数与起运公历时刻
- 起运前童限、8 步正式大运及每步对应流年
- 本命、大运、流年与原局之间可机械判定的干支合、冲、刑、害、破、三合和三会关系
- 本次排盘使用的年柱、月柱、换日、时区、真太阳时和起运算法规则

八字年柱以立春精确时刻为界，月柱以十二节精确时刻为界。五行数量只统计四柱天干地支的表层分布，不代表五行旺衰、身强身弱或喜用神。

`yun_sect` 可设置为 `1` 或 `2`，对应 `lunar-python` 的两种起运时间折算口径，默认使用 `1`。当前仍仅支持 `Asia/Shanghai` 中国标准时间，不根据出生地校正真太阳时。

### `POST /api/bazi/analyze`

请求字段与 `/api/bazi/calculate` 相同。响应中的 `calculation` 为确定性排盘和运程数据；`analysis` 额外提供关系证据、反证/限制、置信度、流派口径差异及传统文化参考声明。当前版本不计算旺衰、调候、格局或喜用神，也不输出财富、婚姻、疾病、灾祸等确定性预测。

## 数据来源

- [lunar-python](https://github.com/6tail/lunar-python)
- [OpenCC](https://github.com/BYVoid/OpenCC)
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
- [chineseStroke](https://github.com/WTree/chineseStroke)
- [Chinese-Names-Corpus](https://github.com/wainshine/Chinese-Names-Corpus)
- [hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)

## 许可

本项目使用 MIT 许可。请同时遵守所引用数据源的许可和署名要求。
