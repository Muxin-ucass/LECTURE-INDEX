# -*- coding: utf-8 -*-
"""中国社会科学院大学讲座 / 学术沙龙聚合采集脚本。

用法：
    python crawler/crawl.py                # 全量采集
    python crawler/crawl.py --max-pages 2   # 只抓每个栏目前 2 页，用于调试
    python crawler/crawl.py --workers 4     # 调整并发

输出：
    data/lectures.json         结构化数据
    data/site_data.js          网站直接加载的数据（file:// 也可用）
    data/crawl_report.json     采集报告（各来源条数、错误）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import ACCOUNTS, SOURCES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
}

LECTURE_KW = re.compile(
    r"讲座|沙龙|讲堂|论坛|工作坊|研讨|报告会|学术报告|学术会议|圆桌|对谈|读书会|分享会|思想汇|名家讲坛|学术对话"
)
EXCLUDE_KW = re.compile(
    r"招聘|招生简章|招生|公示|名单|奖学金|助学金|竞赛|征文启事|征稿|申报|立项|结项|答辩|考试|录取|"
    r"课程表|选课|评奖|评优|招标|采购|注销|放假|开学|报到|宿舍|体检|缴费|报名系统|喜报|获奖|"
    r"招聘公告|人才招聘|复试|调剂|推免|夏令营|暑期学校|项目通知|学分项目|交换项目"
)
DATE_RE = re.compile(r"(?:(20\d{2})\s*[年./-]\s*)?(\d{1,2})\s*[月./-]\s*(\d{1,2})\s*日?")
PUB_RE = re.compile(
    r"(?:发布时间|发布日期|发布于|刊发时间|时间)\s*[:：]?\s*(20\d{2})\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})"
)
ISO_DATE_RE = re.compile(r"(20\d{2})\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})")
TIME_RE = re.compile(
    r"(上午|中午|下午|晚上|晚间)?\s*(\d{1,2})\s*[:：]\s*(\d{2})"
    r"(?:\s*[-–—~至]\s*(\d{1,2})\s*[:：]\s*(\d{2}))?"
)

CAMPUS_LIANGXIANG = "良乡校区"
CAMPUS_WANGJING = "望京校区"
CAMPUS_ONLINE = "线上"
CAMPUS_OFF = "校外"
CAMPUS_UNKNOWN = "未注明"


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r" {2,}", " ", text).strip()


def fetch(url: str, timeout: int = 30, retries: int = 2) -> str | None:
    is_wechat = "mp.weixin.qq.com" in url
    headers = dict(HEADERS)
    if is_wechat:
        headers["Referer"] = "https://mp.weixin.qq.com/"
    for attempt in range(retries + 1):
        try:
            time.sleep(random.uniform(0.9, 1.4) if is_wechat else random.uniform(0.08, 0.22))
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                r.encoding = r.apparent_encoding or "utf-8"
                return r.text
            if r.status_code in (404, 403):
                return None
        except Exception:
            pass
        time.sleep(0.6 * (attempt + 1))
    return None


def canonical_url(base: str, href: str) -> str | None:
    href = (href or "").strip()
    if not href or href.startswith(("javascript:", "#", "mailto:")):
        return None
    full = urljoin(base, href)
    parsed = urlparse(full)
    if parsed.netloc.endswith("mp.weixin.qq.com"):
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    if not re.search(r"/info/\d+/\d+\.htm$", parsed.path):
        return None
    if "ucass.edu.cn" not in parsed.netloc:
        return None
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def extract_item_date(parent_text: str) -> str | None:
    m = DATE_RE.search(parent_text)
    if not m:
        return None
    y, mo, d = m.groups()
    if not y:
        return None
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def parse_listing(html: str, listing_url: str) -> tuple[list[dict], int]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        url = canonical_url(listing_url, a["href"])
        if not url or url in seen:
            continue
        title = a.get("title") or ""
        if not title:
            heading = a.find(["h1", "h2", "h3", "h4"])
            title = heading.get_text(" ", strip=True) if heading else a.get_text(" ", strip=True)
        title = clean_text(title)
        title = re.sub(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\s*", "", title)
        title = re.sub(r"\s*\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$", "", title)
        if len(title) < 6 or title in {"查看更多", "更多", "下页", "上页", "尾页", "宣传片", "查看更多 >"}:
            continue

        parent = a.find_parent(["li", "tr", "div"])
        parent_text = parent.get_text(" ", strip=True) if parent else a.get_text(" ", strip=True)
        if len(parent_text) > 1200:
            parent_text = parent_text[:1200]
        published = extract_item_date(parent_text)

        items.append({"title": title, "url": url, "published": published, "listing_text": parent_text})
        seen.add(url)

    # 总页数：分页区数字链接中的最大值
    page_nums = []
    for a in soup.find_all("a", href=True):
        m = re.search(r"/(\d+)\.htm$", a["href"])
        if m:
            page_nums.append(int(m.group(1)))
    total_pages = max(page_nums) if page_nums else 1
    return items, total_pages


def page_urls(first_url: str, total_pages: int) -> list[str]:
    base = first_url.rsplit(".htm", 1)[0]
    urls = [first_url]
    for k in range(2, total_pages + 1):
        urls.append(f"{base}/{total_pages - k + 1}.htm")
    return urls


def keep_item(item: dict, mode: str) -> bool:
    title = item["title"]
    has_kw = bool(LECTURE_KW.search(title)) or bool(LECTURE_KW.search(item.get("listing_text", "")))
    if mode == "all":
        if EXCLUDE_KW.search(title) and not LECTURE_KW.search(title):
            return False
        return len(title) >= 6
    return has_kw and not EXCLUDE_KW.search(title)


def content_node(soup: BeautifulSoup):
    # 优先使用正文容器，避免把标题栏 / 发布时间 / 导航算进正文
    for sel in ["#js_content", "#vsb_content", "#vsb_content_2", "[id^=vsb_content]", ".v_news_content"]:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 30:
            return node
    candidates = []
    for sel in [".content-con", ".contcot", ".article", ".news_content", ".content"]:
        candidates.extend(soup.select(sel))
    candidates = [c for c in candidates if len(c.get_text(strip=True)) > 30]
    if not candidates:
        return soup.body or soup
    return max(candidates, key=lambda c: len(c.get_text(" ", strip=True)))


def split_site_title(raw: str) -> str:
    raw = clean_text(raw)
    raw = re.sub(r"\s*[-—_|｜]\s*中国社会科学院大学.*$", "", raw)
    raw = re.sub(r"\s*[-—_|｜]\s*UCASS.*$", "", raw, flags=re.I)
    return raw.strip()


def parse_meta_date(text: str) -> str | None:
    m = PUB_RE.search(text)
    if not m:
        return None
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def infer_event_date(body: str, published: str | None, is_review: bool) -> tuple[str | None, str]:
    """返回 (ISO 日期, 命中的原始片段)。优先找带“时间/日期”标签的日期。"""
    pub = None
    if published:
        try:
            pub = datetime.strptime(published, "%Y-%m-%d").date()
        except ValueError:
            pub = None

    candidates: list[tuple[date, str, str]] = []

    def add_candidate(y: str | None, mo: str, d: str, raw: str, kind: str) -> None:
        try:
            if y:
                dt = date(int(y), int(mo), int(d))
            elif pub:
                dt = date(pub.year, int(mo), int(d))
                # 只有跨年附近的日期才做年份修正，避免把“9月”的活动误推到来年
                if dt > pub + timedelta(days=3) and pub.month <= 2 and dt.month >= 11:
                    dt = date(pub.year - 1, int(mo), int(d))
                elif dt < pub - timedelta(days=3) and pub.month >= 11 and dt.month <= 2:
                    dt = date(pub.year + 1, int(mo), int(d))
            else:
                dt = date(date.today().year, int(mo), int(d))
            candidates.append((dt, raw, kind))
        except ValueError:
            pass

    # 1) 带标签的日期
    labels = ["讲座时间", "活动时间", "会议时间", "报告时间", "沙龙时间", "举办时间", "时间", "日期"]
    for label in labels:
        for m in re.finditer(label + r"\s*[:：]?\s*(" + DATE_RE.pattern + r")", body):
            if label == "时间":
                prefix = body[max(0, m.start() - 5):m.start()]
                if re.search(r"发布|截止|报名|开始|结束", prefix):
                    continue
            raw = m.group(1)
            dm = DATE_RE.search(raw)
            if dm:
                add_candidate(*dm.groups(), raw, "label")
        if candidates:
            break

    # 2) 正文中的完整日期
    if not candidates:
        for m in re.finditer(r"20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", body):
            raw = m.group(0)
            dm = DATE_RE.search(raw)
            if dm:
                add_candidate(*dm.groups(), raw, "full")

    # 3) 只有月日的写法（回顾稿常见：“10月17日晚”）
    if not candidates:
        for m in re.finditer(r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日", body):
            add_candidate(None, m.group(1), m.group(2), m.group(0), "monthday")

    if not candidates:
        return None, ""

    # 同一日期出现多次时保留；预告取最近一场，回顾取已发生的最近一场
    unique = {}
    for dt, raw, src in candidates:
        unique.setdefault(dt, (raw, src))
    ordered = sorted(unique.items(), key=lambda x: x[0])
    if is_review and pub:
        past = [x for x in ordered if x[0] <= pub]
        chosen = past[-1] if past else ordered[-1]
    elif pub:
        future = [x for x in ordered if x[0] >= pub - timedelta(days=3)]
        chosen = future[0] if future else ordered[0]
    else:
        chosen = ordered[0]
    return chosen[0].isoformat(), chosen[1][0]


def parse_time(body: str, raw_date: str) -> str:
    if not body:
        return ""
    idx = body.find(raw_date) if raw_date else -1
    window = body[max(0, idx - 10): idx + 60] if idx >= 0 else body[:200]
    m = TIME_RE.search(window)
    if not m:
        return ""
    period, h, mi, h2, m2 = m.groups()
    text = f"{int(h):02d}:{mi}"
    if h2 and m2:
        text += f"-{int(h2):02d}:{m2}"
    if period:
        text = f"{period} {text}"
    return text


def find_location(body: str) -> str:
    stop_words = ["主讲嘉宾", "主讲人", "主讲", "报告人", "嘉宾", "主持人", "主办", "承办", "协办",
                  "时间", "日期", "报名", "扫码", "腾讯会议", "线上", "线下", "欢迎", "请",
                  "友情链接", "版权所有", "作题为", "以“", "，", "。", "；", ";"]
    # “地点：xxx”写法优先（排除“时间地点”这种标题）
    m = re.search(r"(?<!时间)地点\s*[:：]\s*([^。；\n]{2,90})", body)
    if m:
        loc = m.group(1)
        for w in stop_words:
            pos = loc.find(w)
            if pos > 1:
                loc = loc[:pos]
        loc = clean_text(loc).strip(" ：:，,、")
        if len(loc) >= 2:
            return loc

    for label in ["讲座地点", "活动地点", "会议地点", "报告地点", "线下地点", "地点"]:
        for m in re.finditer(label + r"\s*[:：]?\s*([^\n]{2,90})", body):
            loc = m.group(1)
            if loc.startswith(("时间", "日期")):
                continue
            for w in stop_words:
                pos = loc.find(w)
                if pos > 1:
                    loc = loc[:pos]
            loc = clean_text(loc).strip(" ：:，,、")
            if len(loc) >= 2:
                return loc

    m = re.search(r"(?:在|于)\s*([^，。]{2,50}?(?:校区|教学楼|教室|会议室|报告厅|会堂|楼)[^，。]{0,25}?)"
                  r"(?=顺利|举行|举办|开展|进行|召开|作题为|，|。|$)", body)
    if m:
        return clean_text(m.group(1))
    return ""


def _clean_name(name: str) -> str:
    name = name.strip(" 　、，,/：:")
    if len(name) > 2:
        name = re.sub(r"^[师所院室心长任副授了的是由]", "", name)
    return name


def _valid_name(name: str) -> bool:
    name = _clean_name(name)
    if not name:
        return False
    if re.search(r"[《》〈〉「」“”\"'0-9]", name):
        return False
    if re.match(r"^(了|的|是|由|邀请|本次|该|其)", name):
        return False
    if re.search(r"介绍|简介|信息|题目|时间|地点|环节|指出|表示|认为|主持|单位|院长|教授|老师|研究员|主任|博士|学院|大学|研究所|"
                 r"专家|教师|管理|学生|同学|嘉宾|成员|团队|小组|报名|通知|系列|名单|计划|讲堂|论坛|讲座|沙龙|智库|平台|建设|"
                 r"效应|赋能|发展|研究|中心|项目|课程|专业|届", name):
        return False
    if re.fullmatch(r"[\u4e00-\u9fa5·]{2,12}", name):
        cjk = re.sub(r"·", "", name)
        return len(cjk) <= (10 if "·" in name else 5)
    if re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,23}", name):
        return len(re.findall(r"[A-Za-z]", name)) >= 2
    return False


def find_speaker(title: str, body: str, lines: list[str]) -> str:
    # 1) 标题里“讲座预告 | 姓名：主题”最可靠
    parts = re.split(r"[|｜丨]", title)
    if len(parts) >= 2 and ("：" in parts[1] or ":" in parts[1]):
        cand = re.split(r"[：:]", parts[1], 1)[0].strip()
        if 2 <= len(cand) <= 20 and _valid_name(cand) and not re.search(r"预告|讲座|沙龙|论坛|第.讲|系列|通知", cand):
            return cand
    # 2) 正文中独立成行的“主讲人 / 主讲嘉宾”
    for i, line in enumerate(lines):
        m = re.match(r"^(?:主讲嘉宾|主讲人|报告人|主讲)\s*[:：]?\s*(.*)$", line)
        if not m:
            continue
        val = m.group(1).strip()
        if not val and i + 1 < len(lines):
            val = lines[i + 1].strip()
        val = re.split(r"[，,]", val)[0].strip(" ：:、")
        if _valid_name(val):
            return _clean_name(val)
    # 3) “主讲人：姓名”同行写法
    m = re.search(r"(?:主讲嘉宾|主讲人|报告人)\s*[:：]\s*([^\s，。；：]{2,30}(?:[（(][^）)]{1,30}[）)])?)", body)
    if m:
        name = clean_text(m.group(1)).strip(" ：:，,")
        if _valid_name(name):
            return _clean_name(name)
    # 4) 公众号常见的“特邀……主讲”
    m = re.search(r"(?:特邀|邀请)\s*([^，。]{2,40}?)(?:教授|研究员|副研究员|主任|院长|老师|担任主讲)", body)
    if m:
        name = clean_text(m.group(1)).strip(" 、，")
        if len(name) > 8:
            name = re.split(r"(?:大学|学院|研究所|研究中心|研究院|系|部)", name)[-1]
        name = name.strip(" 、，")
        if _valid_name(name):
            return _clean_name(name)
    # 5) “刘继峰教授应……邀请”一类回顾稿写法
    m = re.search(r"([\u4e00-\u9fa5·]{2,3})(?:副研究员|副教授|教授|研究员|博士)(?:应|作|以|围绕|担任|主讲)", body)
    if m and _valid_name(m.group(1)):
        return _clean_name(m.group(1))
    # 6) 标题直接以姓名开头
    cand = re.split(r"[：:]", title, 1)[0].strip()
    if 2 <= len(cand) <= 12 and _valid_name(cand) and not re.search(r"预告|讲座|沙龙|论坛|通知|学术|会议|活动", cand):
        return cand
    m = re.search(r"([\u4e00-\u9fa5·]{2,6})\s*(?:主讲|作报告)", title)
    if m and _valid_name(m.group(1)):
        return m.group(1)
    return ""


def _valid_org(name: str) -> bool:
    name = name.strip(" 　、，,/：:")
    if not (2 <= len(name) <= 40):
        return False
    if re.search(r"^(的|了|、|本次|该)|期刊|支持|指出|环节|介绍|单位$|共同$|主办|承办|讲座", name):
        return False
    return bool(re.search(r"大学|学院|处|中心|研究所|研究院|学会|协会|社|部|系", name))


def find_organizer(body: str, lines: list[str], default: str) -> str:
    host = ""
    cohost = ""
    for line in lines:
        m = re.match(r"^(主办单位|主办方|主办|承办单位|承办方|承办)\s*[:：]\s*(.+)$", line)
        if not m:
            continue
        val = clean_text(m.group(2)).strip(" 　、，,/：:共同")
        if not _valid_org(val):
            continue
        if m.group(1).startswith("主办"):
            host = host or val
        else:
            cohost = cohost or val

    m = re.search(r"由\s*([^，。；]{2,50}?)\s*主办", body)
    if m and _valid_org(m.group(1)):
        host = host or clean_text(m.group(1)).strip(" 　、，,/：:共同")
    m2 = re.search(r"(?:由|，|,|、)\s*([^，。；、]{2,40}?)\s*承办", body)
    if m2 and _valid_org(m2.group(1)):
        cohost = cohost or clean_text(m2.group(1)).lstrip("由").strip(" 　、，,/：:共同")
    parts = [p for p in [host, cohost] if p]
    return " / ".join(parts) if parts else default


def infer_campus(location: str, body: str) -> str:
    text = location or ""
    if "良乡" in text:
        return CAMPUS_LIANGXIANG
    if "望京" in text:
        return CAMPUS_WANGJING
    if re.search(r"腾讯会议|线上|直播|Zoom|zoom|云端|B站|哔哩哔哩", text):
        return CAMPUS_ONLINE
    if re.search(r"法学研究所|沙滩北街|月坛|建国门|院部", text):
        return CAMPUS_OFF

    full = text + " " + body
    if "良乡" in full:
        return CAMPUS_LIANGXIANG
    if "望京" in full:
        return CAMPUS_WANGJING
    if re.search(r"腾讯会议|线上|直播|Zoom|zoom|云端", full):
        return CAMPUS_ONLINE
    if re.search(r"法学研究所|沙滩北街|月坛|建国门", full):
        return CAMPUS_OFF
    return CAMPUS_UNKNOWN


def infer_type(title: str, section: str) -> str:
    t = title
    if "沙龙" in t:
        return "学术沙龙"
    if "工作坊" in t:
        return "工作坊"
    if "论坛" in t:
        return "论坛"
    if "研讨" in t or "圆桌" in t or "学术会议" in t or "会议" in t:
        return "研讨会"
    if "报告会" in t or "学术报告" in t:
        return "报告会"
    if "讲堂" in t:
        return "讲堂"
    if "读书会" in t or "分享会" in t:
        return "读书会"
    if "沙龙" in section:
        return "学术沙龙"
    if "工作坊" in section:
        return "工作坊"
    if "论坛" in section:
        return "论坛"
    return "讲座"


def infer_tags(title: str, summary: str, section: str) -> list[str]:
    text = f"{title} {section} {summary}"
    mapping = [
        ("人工智能", r"人工智能|AI|大模型|算法|机器学习|智能体|算力|deepseek|chatgpt"),
        ("数字人文", r"数字人文|数字史学|计算社会科学|数据要素|数字化|平台经济"),
        ("法学", r"法学|法律|法治|司法|刑法|民法|宪法|仲裁|合规"),
        ("经济学", r"经济|金融|产业|贸易|财政|税收|劳动|收入|市场"),
        ("社会学", r"社会学|民族学|田野|社区治理|公益|慈善|人口学|家庭研究"),
        ("历史学", r"历史学|史学|考古|文献|方志|文明史"),
        ("哲学", r"哲学|伦理学|思想史|儒学|朱子|逻辑学|美学"),
        ("新闻传播", r"新闻|传播|媒体|舆论|出版|视听"),
        ("国际关系", r"国际关系|国际政治|外交|地缘政治|区域国别|全球治理|一带一路"),
        ("文学艺术", r"文学|语言学|翻译|诗歌|戏曲|戏剧|艺术|美育|音乐"),
        ("马克思主义", r"马克思|党建|思政|意识形态"),
    ]
    tags = [name for name, pattern in mapping if re.search(pattern, text, re.I)]
    return tags[:3]


def summarize(body: str) -> tuple[str, str]:
    text = clean_text(body)
    text = re.sub(r"(讲座时间|讲座地点|讲座题目|讲座内容|内容简介|讲座摘要|摘要|主讲嘉宾|主讲人介绍|"
                  r"主讲人|报告人|主持人|主办单位|承办单位|主办|承办|发布时间|发布日期|浏览量|来源|作者|编辑)"
                  r"\s*[:：]?\s*", "", text)

    def bad_sentence(s: str) -> bool:
        if re.match(r"^(20\d{2}年|\d{1,2}月|上午|中午|下午|晚上|时间|地点|主讲|嘉宾|主办|承办)", s):
            return True
        if re.match(r"^\d{1,2}\s*[:：]\s*\d{2}", s):
            return True
        if len(s) < 40 and re.search(r"校区|教学楼|教室|报告厅", s):
            return True
        if re.search(r"\d{1,2}\s*[:：]\s*\d{2}", s) and re.search(r"校区|教学楼|教室|报告厅|地点", s):
            return True
        if re.search(r"博士生导师|教授、|研究员、|院长、", s) and not re.search(r"讲座|沙龙|论坛|主题|围绕|分享", s):
            return True
        return False

    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?])", text) if 25 <= len(s.strip()) <= 220]
    summary = ""
    for s in sentences:
        if not bad_sentence(s) and re.search(r"讲座|沙龙|论坛|工作坊|研讨|主题|围绕|介绍|分享|邀请", s):
            summary = s
            break
    if not summary:
        for s in sentences:
            if not bad_sentence(s):
                summary = s
                break
    if not summary:
        summary = ""
    return (summary[:180], text[:1200])


def parse_detail(url: str, fallback: dict) -> dict:
    html = fetch(url, timeout=35)
    if not html:
        return {"ok": False, "error": "fetch_failed", **fallback}

    is_wechat = "mp.weixin.qq.com" in url
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    if is_wechat:
        title_node = soup.find(id="activity-name")
        account_node = soup.find(id="js_name")
        pub_node = soup.find(id="publish_time")
        title = clean_text(title_node.get_text(" ", strip=True)) if title_node else fallback["title"]
        account = clean_text(account_node.get_text(" ", strip=True)) if account_node else ""
        published = ""
        if pub_node:
            pub_text = pub_node.get_text(" ", strip=True)
            m = ISO_DATE_RE.search(pub_text)
            if m:
                published = f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    else:
        title = split_site_title(soup.title.get_text(" ", strip=True)) if soup.title else ""
        if not title or len(title) < 6 or re.fullmatch(r"中国社会科学院大学.*", title):
            h1 = soup.find("h1")
            if h1 and len(h1.get_text(strip=True)) >= 4:
                title = split_site_title(h1.get_text(" ", strip=True))
        account = ""
        published = ""

    node = content_node(soup)
    lines = [clean_text(x) for x in node.get_text("\n").split("\n")] if node else []
    lines = [x for x in lines if x]
    body = " ".join(lines)
    header = clean_text(soup.get_text(" ", strip=True))[:8000]

    if not published:
        published = parse_meta_date(header) or fallback.get("published") or ""
    title = re.sub(r"^(上一篇|下一篇)\s*[:：]\s*", "", title or "")
    if not title or len(title) < 4:
        title = fallback["title"]

    is_review = bool(re.search(r"回顾|综述|简讯|总结|成功举办|顺利举办|圆满|落幕|参加", title)) or bool(
        re.search(r"顺利举行|成功举办|圆满举办|圆满落幕|进行了|展开了|作题为|参加了|举办了|举行了", body[:600])
    )
    event_date, raw_date = infer_event_date(body, published or None, is_review)
    time_text = parse_time(body, raw_date)
    location = find_location(body)
    speaker = find_speaker(title, body, lines)
    organizer = find_organizer(body, lines, fallback.get("org", ""))
    campus = infer_campus(location, body)
    type_ = infer_type(title, fallback.get("section", ""))
    summary, excerpt = summarize(body)
    tags = infer_tags(title, summary, fallback.get("section", ""))
    if is_review or (event_date and published and event_date < published):
        content_kind = "review"
    elif event_date:
        content_kind = "preview"
    else:
        content_kind = "info"

    return {
        "ok": True,
        "title": title,
        "url": url,
        "source_id": fallback["source_id"],
        "source_name": fallback["source_name"],
        "org": fallback["org"],
        "section": fallback["section"],
        "published": published or fallback.get("published") or "",
        "event_date": event_date or "",
        "time_text": time_text,
        "location": location,
        "campus": campus,
        "speaker": speaker,
        "organizer": organizer,
        "type": type_,
        "tags": tags,
        "summary": summary,
        "excerpt": excerpt,
        "content_kind": content_kind,
        "account": account,
        "is_wechat": is_wechat,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }


def normalize_title(title: str) -> str:
    t = re.sub(r"^(讲座预告|讲座回顾|会议预告|会议综述|活动预告|活动回顾|学术报告|学术沙龙)\s*[|｜丨:：]?\s*", "", title)
    t = re.sub(r"[\s|｜丨:：，,。.、“”‘’\"'（）()【】\[\]—\-–]", "", t)
    return t


def merge_lectures(items: list[dict]) -> list[dict]:
    """同一活动可能同时出现在学院官网与公众号，按标题 + 日期合并。"""
    merged: dict[str, dict] = {}
    for item in items:
        if not item.get("ok"):
            continue
        key = normalize_title(item["title"])
        date_key = item.get("event_date") or ""
        if date_key:
            key = f"{date_key}|{key[:18]}"
        existing = merged.get(key)
        if not existing:
            merged[key] = item
            continue
        # 保留字段更完整的记录；缺失字段互相补齐
        score = lambda x: sum(bool(x.get(f)) for f in
                              ["event_date", "time_text", "location", "speaker", "summary", "published"])
        keep, other = (item, existing) if score(item) > score(existing) else (existing, item)
        for f in ["event_date", "time_text", "location", "speaker", "organizer", "summary", "excerpt", "published"]:
            if not keep.get(f) and other.get(f):
                keep[f] = other[f]
        if other.get("url") and other["url"] != keep.get("url"):
            keep.setdefault("also_urls", []).append(other["url"])
        merged[key] = keep
    return list(merged.values())


def make_id(item: dict) -> str:
    raw = f"{item.get('url','')}|{item.get('title','')}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-pages", type=int, default=0, help="覆盖每个栏目的翻页上限，0 表示使用配置")
    parser.add_argument("--workers", type=int, default=6, help="详情页并发数")
    parser.add_argument("--skip-details", action="store_true", help="只抓列表，不抓详情（调试）")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)

    listing_items: list[dict] = []
    report = {"started_at": datetime.now().isoformat(timespec="seconds"), "sources": [], "errors": []}

    for source in SOURCES:
        source_report = {"id": source["id"], "name": source["name"], "listings": [], "kept": 0}
        for listing in source["listings"]:
            max_pages = args.max_pages or listing.get("max_pages", 5)
            first_html = fetch(listing["url"])
            if not first_html:
                source_report["listings"].append({"url": listing["url"], "section": listing["section"],
                                                  "pages": 0, "items": 0, "kept": 0, "error": "fetch_failed"})
                report["errors"].append({"url": listing["url"], "error": "fetch_failed"})
                continue
            page_items, total_pages = parse_listing(first_html, listing["url"])
            total_pages = max(1, min(total_pages, max_pages))
            all_page_items = list(page_items)
            for page_url in page_urls(listing["url"], total_pages)[1:]:
                html = fetch(page_url)
                if not html:
                    report["errors"].append({"url": page_url, "error": "page_fetch_failed"})
                    continue
                more, _ = parse_listing(html, page_url)
                all_page_items.extend(more)

            # 按 URL 去重
            uniq = {}
            for item in all_page_items:
                uniq[item["url"]] = item
            raw_count = len(uniq)
            kept = []
            for item in uniq.values():
                if not keep_item(item, listing["mode"]):
                    continue
                item.update({
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "org": source["org"],
                    "section": listing["section"],
                })
                kept.append(item)

            listing_items.extend(kept)
            source_report["listings"].append({
                "url": listing["url"], "section": listing["section"], "mode": listing["mode"],
                "pages": total_pages, "items": raw_count, "kept": len(kept),
            })
            print(f"[列表] {source['name']} / {listing['section']}: {raw_count} 条 -> {len(kept)} 条 ({total_pages} 页)")
        source_report["kept"] = sum(x["kept"] for x in source_report["listings"])
        report["sources"].append(source_report)

    # 全局 URL 去重
    by_url = {}
    for item in listing_items:
        by_url[item["url"]] = item
    listing_items = list(by_url.values())
    print(f"\n[列表] 去重后待抓详情 {len(listing_items)} 条")

    details: list[dict] = []
    if args.skip_details:
        for item in listing_items:
            item.update({"ok": True, "event_date": "", "time_text": "", "location": "", "campus": CAMPUS_UNKNOWN,
                         "speaker": "", "organizer": item["org"], "type": infer_type(item["title"], item["section"]),
                         "tags": [], "summary": "", "excerpt": "", "content_kind": "info", "is_wechat": False})
            details.append(item)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(parse_detail, item["url"], item): item for item in listing_items}
            for fut in as_completed(futures):
                base = futures[fut]
                try:
                    res = fut.result()
                except Exception as e:
                    res = {"ok": False, "error": repr(e), **base}
                if not res.get("ok"):
                    report["errors"].append({"url": base["url"], "error": res.get("error", "parse_failed")})
                    # 保留列表信息，避免整条丢失
                    res = {**base, "ok": True, "event_date": "", "time_text": "", "location": "",
                           "campus": CAMPUS_UNKNOWN, "speaker": "", "organizer": base["org"],
                           "type": infer_type(base["title"], base["section"]), "tags": [], "summary": "",
                           "excerpt": "", "content_kind": "info", "published": base.get("published", ""),
                           "is_wechat": "mp.weixin.qq.com" in base["url"], "account": ""}
                details.append(res)
                done += 1
                if done % 50 == 0:
                    print(f"  详情进度 {done}/{len(listing_items)}")

    lectures = merge_lectures(details)
    for item in lectures:
        item["id"] = make_id(item)
        item.setdefault("also_urls", [])
    lectures.sort(key=lambda x: (x.get("event_date") or "0000-00-00", x.get("published") or ""), reverse=True)

    today = date.today().isoformat()
    campus_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    for item in lectures:
        campus_counts[item["campus"]] = campus_counts.get(item["campus"], 0) + 1
        type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1
        source_counts[item["source_id"]] = source_counts.get(item["source_id"], 0) + 1

    sources_out = []
    for s in SOURCES:
        sources_out.append({
            "id": s["id"], "name": s["name"], "short": s["short"], "org": s["org"],
            "category": s["category"], "homepage": s["homepage"],
            "listings": next((x["listings"] for x in report["sources"] if x["id"] == s["id"]), []),
            "count": source_counts.get(s["id"], 0),
        })

    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "today": today,
        "total": len(lectures),
        "upcoming": sum(1 for x in lectures if x.get("event_date") and x["event_date"] >= today),
        "liangxiang": campus_counts.get(CAMPUS_LIANGXIANG, 0),
        "sources_count": len(SOURCES),
        "accounts_count": len(ACCOUNTS),
        "campus_counts": campus_counts,
        "type_counts": type_counts,
    }
    payload = {"meta": meta, "lectures": lectures, "sources": sources_out, "accounts": ACCOUNTS}

    with open(os.path.join(DATA_DIR, "lectures.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    js = "window.UCASS_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(DATA_DIR, "site_data.js"), "w", encoding="utf-8") as f:
        f.write(js.replace("</", "<\\/"))

    report["finished_at"] = datetime.now().isoformat(timespec="seconds")
    report["total"] = len(lectures)
    report["campus_counts"] = campus_counts
    with open(os.path.join(DATA_DIR, "crawl_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print(f"\n完成：{len(lectures)} 条讲座/学术活动，其中良乡校区 {campus_counts.get(CAMPUS_LIANGXIANG, 0)} 条")
    print("良乡/校区分布:", campus_counts)
    print("类型分布:", type_counts)
    print(f"输出: {DATA_DIR}")


if __name__ == "__main__":
    main()
