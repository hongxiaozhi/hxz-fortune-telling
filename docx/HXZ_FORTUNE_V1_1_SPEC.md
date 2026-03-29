# HXZ Fortune v1.1 产品规格（可执行）

最后更新：2026-03-29
适用范围：v1.1 MVP
依赖文档：docx/HXZ_FORTUNE_V1_PLAN.md

---

## 一、范围说明

本规格仅覆盖 v1.1，目标是用最短路径上线可用版本：

1. 免登录输入出生信息并生成结果
2. 输出八字简版 + 五行 + 时间段建议
3. 支持任意日期区间（上限 180 天）
4. 缺失时辰时可继续使用并提示精度升级

不在 v1.1 范围内：账号体系、跨设备同步、专业推导演示、多流派切换。

---

## 二、核心业务对象

### 1) AnalysisRequest（分析请求）

- request_id: string（后端生成）
- name: string | null（可选）
- gender: enum(male, female, other, unknown)
- calendar_type: enum(solar, lunar)
- birth_date: YYYY-MM-DD
- birth_time: HH:mm | null
- has_birth_time: boolean
- precision_mode: enum(approx, standard)
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD
- timezone: string（默认 Asia/Shanghai）
- created_at: datetime

### 2) AnalysisResult（分析结果）

- request_id: string
- disclaimer: string（固定免责声明）
- precision_level: enum(low, medium)
- precision_note: string
- bazi_summary: object
  - year_pillar: string
  - month_pillar: string
  - day_pillar: string
  - hour_pillar: string | null
- wuxing_score: object
  - wood: number
  - fire: number
  - earth: number
  - metal: number
  - water: number
- overall_advice: object
  - suitable: string
  - avoid: string
  - reminder: string
- segments: array<AdviceSegment>
- upgrade_hint: object
  - show: boolean
  - title: string
  - content: string
  - affected_dimensions: string[]

### 3) AdviceSegment（分段建议）

- segment_index: number（从 1 开始）
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD
- trend_alignment: enum(aligned, deviated)
- suitable: string
- avoid: string
- reminder: string
- dimensions: object
  - work_study: enum(low, medium, high)
  - finance: enum(low, medium, high)
  - social: enum(low, medium, high)
  - health: enum(low, medium, high)

### 4) LocalHistoryItem（本地历史）

- local_id: string
- created_at: datetime
- display_title: string
- input_snapshot: AnalysisRequest（脱敏后）
- result_snapshot: AnalysisResult（摘要版）

---

## 三、接口清单（v1.1）

基线：延续 Flask + SQLite + Vue CDN 架构，接口命名风格与现有项目一致。

### 1) POST /api/fortune/analyze

用途：提交分析请求并返回结果。

请求体：

```json
{
  "name": "可选",
  "gender": "male",
  "calendar_type": "solar",
  "birth_date": "1993-08-15",
  "birth_time": "09:30",
  "has_birth_time": true,
  "precision_mode": "standard",
  "start_date": "2026-04-01",
  "end_date": "2026-04-30",
  "timezone": "Asia/Shanghai"
}
```

校验规则：

1. birth_date 必填。
2. gender、calendar_type 必填。
3. has_birth_time=false 时，birth_time 必须为空。
4. start_date <= end_date。
5. 日期区间天数 <= 180。
6. precision_mode=standard 且 has_birth_time=false 时，允许请求但强制降级为 approx，并返回 precision_note。

响应体（200）：

```json
{
  "request_id": "req_123",
  "disclaimer": "本结果仅供参考，不替代医疗、法律、财务等专业建议。",
  "precision_level": "medium",
  "precision_note": "已采用标准模式进行分析。",
  "bazi_summary": {
    "year_pillar": "癸酉",
    "month_pillar": "庚申",
    "day_pillar": "甲子",
    "hour_pillar": "己巳"
  },
  "wuxing_score": {
    "wood": 62,
    "fire": 48,
    "earth": 55,
    "metal": 44,
    "water": 67
  },
  "overall_advice": {
    "suitable": "适合推进已有计划，优先完成确定性高的任务。",
    "avoid": "不建议在信息不足时做高风险承诺。",
    "reminder": "先稳节奏，再做扩张，会更顺。"
  },
  "segments": [
    {
      "segment_index": 1,
      "start_date": "2026-04-01",
      "end_date": "2026-04-07",
      "trend_alignment": "aligned",
      "suitable": "适合启动沟通和排期。",
      "avoid": "避免临时改动大方向。",
      "reminder": "先把共识对齐，再推进执行。",
      "dimensions": {
        "work_study": "high",
        "finance": "medium",
        "social": "high",
        "health": "medium"
      }
    }
  ],
  "upgrade_hint": {
    "show": false,
    "title": "",
    "content": "",
    "affected_dimensions": []
  }
}
```

异常码：

- 400: 参数错误（含日期区间超限）
- 422: 可解析但无法完成推演
- 429: 请求过于频繁（可选，v1.1 可不启用）
- 500: 服务异常

### 2) GET /api/fortune/health

用途：健康检查，供 Nginx/Gunicorn 运维和前端预检测。

响应体：

```json
{
  "status": "ok",
  "service": "hxz-fortune",
  "version": "v1.1.0"
}
```

---

## 四、前端页面信息架构（IA）

### 页面 A：输入页

模块顺序：

1. 顶部标题区
2. 基础输入区（姓名可选、性别、阴历/阳历、出生日期、出生时辰可选）
3. 时间段区（默认未来 30 天，可改任意起止）
4. 精度说明区（大概/标准解释）
5. 主按钮“开始分析”
6. 次级入口“历史记录（本机）”
7. 预留入口“登录后可跨设备同步（即将上线）”

### 页面 B：加载页（或覆盖层）

模块顺序：

1. 加载动画
2. 温和文案（示例：“正在为你整理近期节奏建议...”）
3. 超时与重试提示

### 页面 C：结果页

模块顺序：

1. 顶部固定免责声明
2. 顶部结论卡（整体结论）
3. 八字简版卡
4. 五行占比卡
5. 整段建议卡（宜做/慎做/一句总结）
6. 分段建议列表（每段一张卡）
7. 缺失时辰时显示“精度升级提示卡”（位于基础结论之后）
8. 操作区（重新分析、修改区间）

---

## 五、关键交互流程

### 流程 1：标准输入并生成结果

1. 用户填写基础信息和区间
2. 前端本地校验通过
3. 调用 POST /api/fortune/analyze
4. 展示结果页
5. 写入本地历史

### 流程 2：缺失时辰

1. 用户未填写出生时辰
2. 前端提示“可继续生成基础结论”
3. 后端按 approx 输出结果
4. 结果页展示升级提示卡

### 流程 3：区间过长

1. 用户选择超过 180 天
2. 前端即时报错并阻止提交
3. 如绕过前端，后端返回 400 + 明确错误文案

### 流程 4：分段偏离整体趋势

1. 后端标记 trend_alignment=deviated
2. 前端在对应分段卡顶部显示“本段偏离整体趋势”提示
3. 提示文案使用温和语气，不做命令式判断

---

## 六、文案与语气规范（v1.1）

语气原则：温和、建议式、非命令式。

推荐句式：

1. “可以优先考虑...”
2. “更适合先做...”
3. “这段时间建议暂缓...”

避免句式：

1. “必须...”
2. “绝对不要...”
3. “一定会...”

免责声明固定文案（顶部常驻）：

“本结果仅供参考，不替代医疗、法律、财务等专业建议。”

---

## 七、数据存储建议（v1.1）

### 后端数据库（SQLite）

v1.1 可选两种策略：

1. 仅计算不落库（最轻量）
2. 落库请求与摘要结果（便于后续统计）

推荐：先落库摘要，便于 v1.5 运营指标。

建议表结构：

- analysis_request
  - id, gender, calendar_type, birth_date, birth_time, has_birth_time, precision_mode, start_date, end_date, timezone, created_at
- analysis_result
  - id, request_id, precision_level, overall_suitable, overall_avoid, overall_reminder, wuxing_json, segments_json, upgrade_hint_json, created_at

### 前端本地存储

- localStorage key: hxz_fortune_history
- 容量：最多 5 条，超出按时间淘汰最旧

---

## 八、验收清单（v1.1）

1. 免登录情况下可完整走通输入到结果。
2. 缺失时辰可生成基础结论，并显示升级提示。
3. 自定义区间支持任意起止，但超过 180 天会被拦截。
4. 分段按连续 7 天拆分，尾段不足 7 天独立显示。
5. 分段偏离整体趋势时有明确提示。
6. 四维简表仅使用低/中/高三档。
7. 顶部免责声明固定可见。
8. 文案语气符合温和陪伴型。

---

## 九、实施优先级（建议）

1. P0：输入校验、分析接口、结果基础展示
2. P1：分段建议、偏离提示、缺时辰升级提示
3. P1：本地历史与移动端适配
4. P2：健康检查、埋点预留字段
