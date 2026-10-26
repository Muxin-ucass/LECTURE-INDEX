# -*- coding: utf-8 -*-
"""中国社会科学院大学讲座 / 学术沙龙信息源配置。

每条 listing 的 mode:
  all    - 该栏目本身就是讲座/沙龙栏目，条目全部尝试入库
  filter - 综合新闻/通知栏目，仅保留命中讲座关键词的条目
max_pages 用于控制每个栏目的翻页上限，避免对站点造成压力。
"""

SOURCES = [
    {
        "id": "www",
        "name": "中国社会科学院大学",
        "short": "学校官网",
        "org": "中国社会科学院大学",
        "category": "校级",
        "homepage": "https://www.ucass.edu.cn/",
        "listings": [
            {"url": "https://www.ucass.edu.cn/index/xsdt.htm", "section": "学术动态", "mode": "filter", "max_pages": 9},
            {"url": "https://www.ucass.edu.cn/index/tzgg.htm", "section": "通知公告", "mode": "filter", "max_pages": 24},
        ],
    },
    {
        "id": "ky",
        "name": "科研处",
        "short": "科研处",
        "org": "中国社会科学院大学科研处",
        "category": "校级",
        "homepage": "https://ky.ucass.edu.cn/",
        "listings": [
            {"url": "https://ky.ucass.edu.cn/xwdt.htm", "section": "新闻动态", "mode": "filter", "max_pages": 4},
            {"url": "https://ky.ucass.edu.cn/tzgg.htm", "section": "通知公告", "mode": "filter", "max_pages": 3},
        ],
    },
    {
        "id": "sg",
        "name": "政府管理学院",
        "short": "政管学院",
        "org": "政府管理学院",
        "category": "学院",
        "homepage": "https://sg.ucass.edu.cn/",
        "listings": [
            {"url": "https://sg.ucass.edu.cn/index/ygtz.htm", "section": "预告通知", "mode": "all", "max_pages": 16},
            {"url": "https://sg.ucass.edu.cn/jxgl/jzxx.htm", "section": "讲座信息", "mode": "all", "max_pages": 12},
            {"url": "https://sg.ucass.edu.cn/fb/xshd1.htm", "section": "学术活动", "mode": "filter", "max_pages": 8},
        ],
    },
    {
        "id": "law",
        "name": "法学院",
        "short": "法学院",
        "org": "法学院",
        "category": "学院",
        "homepage": "https://law.ucass.edu.cn/",
        "listings": [
            {"url": "https://law.ucass.edu.cn/xwzhong_xin/hdyg.htm", "section": "活动预告", "mode": "all", "max_pages": 24},
            {"url": "https://law.ucass.edu.cn/xsky/xshd.htm", "section": "学术活动", "mode": "filter", "max_pages": 8},
        ],
    },
    {
        "id": "phil",
        "name": "哲学院",
        "short": "哲学院",
        "org": "哲学院",
        "category": "学院",
        "homepage": "https://phil.ucass.edu.cn/",
        "listings": [
            {"url": "https://phil.ucass.edu.cn/xwtz/hyjz1.htm", "section": "会议讲座", "mode": "all", "max_pages": 7},
        ],
    },
    {
        "id": "history",
        "name": "历史学院",
        "short": "历史学院",
        "org": "历史学院",
        "category": "学院",
        "homepage": "https://history.ucass.edu.cn/",
        "listings": [
            {"url": "https://history.ucass.edu.cn/xsyj/xshd1.htm", "section": "学术活动", "mode": "all", "max_pages": 20},
            {"url": "https://history.ucass.edu.cn/xsyj/qnsxlt.htm", "section": "青年史学论坛", "mode": "filter", "max_pages": 6},
        ],
    },
    {
        "id": "bs",
        "name": "商学院",
        "short": "商学院",
        "org": "商学院",
        "category": "学院",
        "homepage": "https://bs.ucass.edu.cn/",
        "listings": [
            {"url": "https://bs.ucass.edu.cn/xsky/xueshuj.htm", "section": "学术讲座", "mode": "all", "max_pages": 6},
            {"url": "https://bs.ucass.edu.cn/xsky/xshd.htm", "section": "学术活动", "mode": "filter", "max_pages": 8},
        ],
    },
    {
        "id": "se",
        "name": "经济学院",
        "short": "经济学院",
        "org": "经济学院",
        "category": "学院",
        "homepage": "https://se.ucass.edu.cn/",
        "listings": [
            {"url": "https://se.ucass.edu.cn/xshd/xue_shult.htm", "section": "学术论坛", "mode": "all", "max_pages": 3},
            {"url": "https://se.ucass.edu.cn/xshd/skjy.htm", "section": "社科经苑", "mode": "filter", "max_pages": 8},
            {"url": "https://se.ucass.edu.cn/xwdt.htm", "section": "新闻动态", "mode": "filter", "max_pages": 8},
        ],
    },
    {
        "id": "fae",
        "name": "应用经济学院",
        "short": "应经学院",
        "org": "应用经济学院",
        "category": "学院",
        "homepage": "https://fae.ucass.edu.cn/",
        "listings": [
            {"url": "https://fae.ucass.edu.cn/xsky/qlxzgzf.htm", "section": "青蓝学者工作坊", "mode": "all", "max_pages": 4},
            {"url": "https://fae.ucass.edu.cn/xsky/xshd.htm", "section": "学术活动", "mode": "filter", "max_pages": 6},
        ],
    },
    {
        "id": "shymzxy",
        "name": "社会与民族学院",
        "short": "社民学院",
        "org": "社会与民族学院",
        "category": "学院",
        "homepage": "https://shymzxy.ucass.edu.cn/",
        "listings": [
            {"url": "https://shymzxy.ucass.edu.cn/xwzx/tzgg1.htm", "section": "通知公告", "mode": "filter", "max_pages": 13},
            {"url": "https://shymzxy.ucass.edu.cn/sxkc/MSWsxsj/swjz.htm", "section": "实务讲座", "mode": "all", "max_pages": 5},
            {"url": "https://shymzxy.ucass.edu.cn/xstd/xsdt.htm", "section": "学术动态", "mode": "filter", "max_pages": 6},
        ],
    },
    {
        "id": "media",
        "name": "新闻传播学院",
        "short": "新传学院",
        "org": "新闻传播学院",
        "category": "学院",
        "homepage": "https://media.ucass.edu.cn/",
        "listings": [
            {"url": "https://media.ucass.edu.cn/xsky/xsdt.htm", "section": "学术动态", "mode": "filter", "max_pages": 4},
        ],
    },
    {
        "id": "sfl",
        "name": "外国语学院",
        "short": "外院",
        "org": "外国语学院",
        "category": "学院",
        "homepage": "https://sfl.ucass.edu.cn/",
        "listings": [
            {"url": "https://sfl.ucass.edu.cn/kyxx1/xsdt.htm", "section": "学术动态", "mode": "filter", "max_pages": 2},
        ],
    },
    {
        "id": "marxism",
        "name": "马克思主义学院",
        "short": "马院",
        "org": "马克思主义学院",
        "category": "学院",
        "homepage": "https://marxism.ucass.edu.cn/",
        "listings": [
            {"url": "https://marxism.ucass.edu.cn/tzgg/jztz.htm", "section": "讲座通知", "mode": "all", "max_pages": 4},
            {"url": "https://marxism.ucass.edu.cn/kxyj1/xshd.htm", "section": "学术活动", "mode": "filter", "max_pages": 6},
        ],
    },
    {
        "id": "wenxue",
        "name": "文学院",
        "short": "文学院",
        "org": "文学院",
        "category": "学院",
        "homepage": "https://wenxue.ucass.edu.cn/",
        "listings": [
            {"url": "https://wenxue.ucass.edu.cn/mygz/myjz.htm", "section": "美育讲座", "mode": "all", "max_pages": 3},
            {"url": "https://wenxue.ucass.edu.cn/xsyj/xsjl.htm", "section": "学术交流", "mode": "filter", "max_pages": 5},
        ],
    },
    {
        "id": "sipe",
        "name": "全球与区域国别学院",
        "short": "国别学院",
        "org": "全球与区域国别学院",
        "category": "学院",
        "homepage": "https://sipe.ucass.edu.cn/",
        "listings": [
            {"url": "https://sipe.ucass.edu.cn/kygz/kydt.htm", "section": "科研动态", "mode": "filter", "max_pages": 3},
            {"url": "https://sipe.ucass.edu.cn/xwzx/xwdt.htm", "section": "新闻动态", "mode": "filter", "max_pages": 3},
        ],
    },
    {
        "id": "sged",
        "name": "国际教育学院",
        "short": "国教学院",
        "org": "国际教育学院",
        "category": "学院",
        "homepage": "https://sged.ucass.edu.cn/",
        "listings": [
            {"url": "https://sged.ucass.edu.cn/xsky/xshd.htm", "section": "学术活动", "mode": "filter", "max_pages": 5},
            {"url": "https://sged.ucass.edu.cn/xwgg/xwdt.htm", "section": "新闻动态", "mode": "filter", "max_pages": 5},
        ],
    },
    {
        "id": "intl",
        "name": "国际交流与合作处",
        "short": "国际处",
        "org": "国际交流与合作处",
        "category": "校级",
        "homepage": "https://intl.ucass.edu.cn/",
        "listings": [
            {"url": "https://intl.ucass.edu.cn/swhy.htm", "section": "涉外会议", "mode": "all", "max_pages": 3},
            {"url": "https://intl.ucass.edu.cn/xwsd1.htm", "section": "新闻速递", "mode": "filter", "max_pages": 4},
        ],
    },
    {
        "id": "youth",
        "name": "校团委",
        "short": "校团委",
        "org": "共青团中国社会科学院大学委员会",
        "category": "校级",
        "homepage": "https://youth.ucass.edu.cn/",
        "listings": [
            {"url": "https://youth.ucass.edu.cn/tzgg.htm", "section": "通知公告", "mode": "filter", "max_pages": 3},
        ],
    },
]

# 微信公众号 / 抖音等平台入口（人工维护）。官网已转载的公众号文章会在采集时自动入库。
ACCOUNTS = [
    {"platform": "微信公众号", "name": "中国社会科学院大学", "handle": "", "org": "学校官方", "note": "学校官方公众号，发布校级学术活动与校园资讯"},
    {"platform": "微信公众号", "name": "中国社科大科研处", "handle": "", "org": "科研处", "note": "“之和知”午间学术沙龙等科研活动的主要发布渠道"},
    {"platform": "微信公众号", "name": "社科大政管", "handle": "", "org": "政府管理学院", "note": "学院讲座预告、讲座回顾"},
    {"platform": "微信公众号", "name": "社科大法学院", "handle": "", "org": "法学院", "note": "法学讲座、学术会议信息"},
    {"platform": "微信公众号", "name": "社科大社会与民族学院", "handle": "", "org": "社会与民族学院", "note": "笃学讲堂、实务讲座、学术沙龙"},
    {"platform": "微信公众号", "name": "青春社科大", "handle": "UCASSYOUTH", "org": "校团委", "note": "团委活动、青年学术活动"},
    {"platform": "微信公众号", "name": "社科大望京校区", "handle": "ucass-wangjing", "org": "望京校区", "note": "望京校区讲座与校园活动"},
    {"platform": "微信公众号", "name": "中国社会科学院大学招生", "handle": "", "org": "招生办", "note": "招生宣讲、专业介绍"},
    {"platform": "微信公众号", "name": "UCASSInternational", "handle": "UCASSInternational", "org": "国际交流与合作处", "note": "国际交流项目、全球视野大讲堂"},
    {"platform": "抖音", "name": "中国社会科学院大学", "handle": "", "org": "学校官方", "note": "官方短视频账号（账号名待核实，建议在抖音内搜索确认）", "search_url": "https://www.douyin.com/search/%E4%B8%AD%E5%9B%BD%E7%A4%BE%E4%BC%9A%E7%A7%91%E5%AD%A6%E9%99%A2%E5%A4%A7%E5%AD%A6"},
    {"platform": "抖音", "name": "社科大讲座/学术活动", "handle": "", "org": "聚合检索", "note": "抖音站内关键词聚合入口，需登录后查看", "search_url": "https://www.douyin.com/search/%E7%A4%BE%E7%A7%91%E5%A4%A7%20%E8%AE%B2%E5%BA%A7"},
]
