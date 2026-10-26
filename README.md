# 社科大讲座汇

中国社会科学院大学良乡校区讲座 / 学术沙龙信息聚合网站。数据来自学校官网、各学院网站与官网转载的公众号文章，支持 GitHub Pages 在线访问与定时自动更新。

## 项目结构

```
index.html              网站入口（单页，hash 路由）
assets/app.js           前端渲染与交互
assets/styles.css       视觉样式
data/lectures.json      结构化数据（爬虫产出）
data/site_data.js       内嵌数据（file:// 离线打开用）
crawler/crawl.py        采集脚本
crawler/sources.py      来源配置（18 个官网来源 + 11 个平台入口）
contract/               后端化交接契约（openapi.yaml 等）
.github/workflows/      定时采集 + 自动部署流水线
```

## 本地使用

直接双击 `index.html` 即可离线浏览当前数据。

手动更新数据（需 Python 3.10+ 与 requests、beautifulsoup4）：

```bash
pip install requests beautifulsoup4
python crawler/crawl.py               # 全量采集
python crawler/crawl.py --max-pages 1 # 调试：每个栏目只抓第一页
```

## 部署到 GitHub Pages（上线三步）

1. **注册/登录 GitHub**，右上角 + → New repository，起名如 `ucass-lectures`（Public）。
2. **推送本文件夹**。在本目录执行（把 `<你的用户名>` 换掉）：

   ```bash
   git init
   git add .
   git commit -m "init: 社科大讲座汇"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/ucass-lectures.git
   git push -u origin main
   ```

   推送时浏览器会弹出 GitHub 登录授权，按提示完成即可。

3. **开启 Pages**：仓库页面 → Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。

完成后访问 `https://<你的用户名>.github.io/ucass-lectures/` 即可。

## 自动更新原理

流水线 [.github/workflows/update.yml](.github/workflows/update.yml) 会：

- **每天北京时间 07:30 / 19:30** 自动运行爬虫，抓取全部来源；
- 数据有变化时自动提交并重新发布网站（commit 由 github-actions[bot] 完成，无需人工干预）；
- 每次手动 push 代码也会触发重新部署。

想调整频率：编辑 workflow 中 `cron` 两行（时间为 UTC，北京时间 = UTC + 8）。想立即更新：仓库 Actions 页 → crawl and deploy → Run workflow。

## 常见问题

- **首次部署没反应？** 确认第 3 步 Source 已选 GitHub Actions；到 Actions 标签页看运行日志。
- **定时任务偶尔延迟？** GitHub 免费版的 cron 允许 ±数十分钟偏差，属正常。
- **某学院数据缺失？** 学院可能未发布或栏目改版；可在 `crawler/sources.py` 中核对该来源 URL 是否仍可访问。
- **想接入真实后端？** 见 `contract/` 目录——数据模型与接口契约已备好，前端仅需替换数据加载层。
