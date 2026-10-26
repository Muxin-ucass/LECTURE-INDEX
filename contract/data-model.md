# 数据模型

> 字段口径与采集脚本一致；后端建表时按此结构建模。

## 实体关系

```
Lecture ──< Source (1:N, 通过 source_id 关联)
Lecture ──< Account (1:1 可选, 通过 url 中 mp.weixin.qq.com 或 account 字段)
Payload ──< Source, Account, Meta（聚合输出）
```

## Lecture（活动）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 内容指纹，去重与抽屉直达的主键 |
| title | string | 是 | 原文标题（含"讲座预告\|"前缀，前端 display_title 已剥离） |
| url | string(uri) | 是 | 原文链接 |
| source_id | string | 是 | 关联 Source.id |
| source_name | string | 是 | 来源单位名 |
| org | string | 是 | 主办单位（默认取 source.org） |
| section | string | 是 | 来源栏目名，如"预告通知" |
| published | date | 否 | 原文发布日期，YYYY-MM-DD |
| event_date | date | 否 | 活动日期，YYYY-MM-DD；空=日期待定 |
| time_text | string | 否 | "18:10" 等时间文本 |
| location | string | 否 | 地点原文 |
| campus | enum | 是 | 良乡校区/望京校区/线上/校外/未注明 |
| speaker | string | 否 | 主讲人姓名 |
| organizer | string | 是 | 主办/承办单位，可含"主办 / 承办"组合 |
| type | enum | 是 | 讲座/学术沙龙/工作坊/论坛/研讨会/报告会/讲堂/读书会 |
| tags | string[] | 否 | 主题标签，如 ["政治学"] |
| summary | string | 否 | 一两句摘要 |
| excerpt | string | 否 | 正文摘录 |
| content_kind | enum | 是 | preview/review/info |
| account | string | 否 | 公众号账号名（来源为微信转载时） |
| is_wechat | bool | 是 | URL 是否来自 mp.weixin.qq.com |
| fetched_at | string | 否 | 详情抓取时间戳 |
| also_urls | string[] | 否 | 跨来源合并掉的重复链接 |

## Source（来源）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 来源缩写，如 `sg` |
| name | string | 全称 |
| short | string | 简称 |
| org | string | 默认主办单位 |
| category | enum | 校级/学院 |
| homepage | uri | 官网首页 |
| count | int | 已收录活动数 |
| listings | Listing[] | 栏目列表 |

### Listing

`url` 栏目首页 · `section` 栏目名 · `mode` all/filter · `pages` 实际抓取页数 · `items` 列表条目数 · `kept` 入库条数

## Account（平台账号入口）

`platform` 微信公众号/抖音 · `name` · `handle`（公众号 id 或抖音号，可空） · `org` · `note` 用途说明 · `search_url` 抖音站内搜索 URL（可空）

## Meta（元信息）

`generated_at` 数据生成时间戳 · `today` 今日日期 · `total` `upcoming` `liangxiang` 总数 · `sources_count` `accounts_count` 入口数 · `campus_counts` `type_counts` 各维度分布（map）
