# 社科大讲座汇 · 数据契约（Backend Handoff）

本目录是把当前静态数据层抽象为**架构中立契约**的交接物：未来若要接入真实后端（BaaS / 自建 / 外包），前端只需替换数据加载层内部实现，页面与交互零改动。

## 单一接缝

前端唯一的数据入口是 `assets/app.js` 顶部的 `DATA` 加载逻辑：

- 现状：`file://` 读内嵌 `data/site_data.js`；在线 `fetch("data/lectures.json")`
- 后端化：把这段替换为对下方任一端点的调用即可，`payload` 结构保持不变

## 文件说明

| 文件 | 内容 |
|---|---|
| `openapi.yaml` | 端点契约：响应结构（与 lectures.json 完全一致） |
| `data-model.md` | 实体与字段定义（数据库建表的neutral依据） |
| `endpoint-map.md` | 页面 → 数据消费关系表 |

## 三档接入路径（按团队与时间选一）

| 档 | 适用 | 做法 |
|---|---|---|
| ① BaaS 直连 | 快速验证、无后端人力 | 把 `data-model.md` 映射为 Supabase / PocketBase 表，`boot()` 里换成 SDK 查询 |
| ② 契约生成脚手架 | 自建后端、架构未定 | 把 `openapi.yaml` 喂给 OpenAPI 代码生成器，产出后端路由骨架与前端类型化客户端 |
| ③ 工程外包 | 正式产品化 | 直接把本目录三份文件交给后端团队实现 |
