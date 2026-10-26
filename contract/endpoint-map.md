# 端点 → 页面映射

| 页面 (hash) | 消费数据 | 说明 |
|---|---|---|
| `#/list` 活动索引 | `lectures[]` 全量 + `meta` | 客户端筛选/排序/分页，无需额外端点 |
| `#/calendar` 学术日历 | `lectures[]` 全量 + 按月聚合 | 客户端构建月历 |
| `#/sources` 来源矩阵 | `sources[]` + `accounts[]` + `meta` | 来源/账号展示 |
| `#/about` 采集说明 | `meta` | 统计与生成时间 |
| `#/lecture/<id>` 详情 | `lectures[]` 按 id 查找 | 抽屉打开 |

## 后端化建议

当前一次拉取全量 payload；数据量增长后可拆为：

| 端点 | 用途 |
|---|---|
| `GET /api/lectures?since=<date>&campus=&type=&q=&page=` | 列表筛选（替换前端内存过滤） |
| `GET /api/lectures/{id}` | 单条详情 |
| `GET /api/sources` | 来源矩阵 |
| `GET /api/accounts` | 平台入口 |
| `GET /api/meta` | 元信息与统计 |

前端只需把 `boot()` 中的 `fetch("data/lectures.json")` 改为按需调用上述端点，页面逻辑不动。
