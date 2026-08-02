# 飞书多维表格重建：主字段 / 父子记录分组 / 字段格式（2026-08-01 实战）

持仓明细表从"代码主字段"重建为"序号主字段 + 角色父记录分组 + ¥/百分比格式"的完整方案。
所有命令基于 lark-cli v1.0.72-1.0.80，base 操作走 `lark-cli base +...`。

## 1. 主字段（primary field）规则 — 最重要

- **`--fields` 数组第一个字段 = 主字段**（table-create 时）。
- 主字段**不能被移动、隐藏、删除**（API 强制）。visible_fields 顺序对它无效，永远排第一列。
- 若需要"第一列可移动/可排序"（如序号），必须把该字段设为主字段。
- 症状：visible_fields 传 `["名称","代码",...]`，返回却是 `["代码","名称",...]` → 代码是主字段，被强制前置。

## 2. visible_fields 控制顺序

- `{"visible_fields":["A","B","C",...]}` 同时控制可见性和顺序（除主字段外均按传入顺序生效）。
- 传字段名或字段 ID 均可；传 ID 更稳。
- 命令：`lark-cli base +view-set-visible-fields --base-token <t> --table-id <tid> --view-id <vid> --json '{"visible_fields":[...]}' --as user`

## 3. 父子记录（角色=父，个股=子）自关联 link

- **必须先建表，再加自关联字段**：`link_table` 需要目标 table_id，而新表 table_id 建表后才返回。
- 步骤：
  1. `+table-create --name "持仓明细" --fields '[...不含 link 字段...]'` → 拿到 table_id
  2. `+field-create --json '{"name":"父记录","type":"link","link_table":"<table_id>"}'`（link_table 用 ID 不是表名，用名字会报 800030104 not_found）
  3. `+record-batch-create` 建父记录（角色名，序号 20+）
  4. 逐条 `+record-upsert --record-id <子记录id> --json '{"父记录":[{"id":"<父记录id>"}]}'` 关联
- 视图分组：`+view-set-group --json '{"group_config":[{"field":"父记录","desc":false}]}'`

## 4. 字段格式：百分比 / 货币

- 百分比：`{"name":"占总资产","type":"number","style":{"type":"plain","precision":2,"percentage":true,"thousands_separator":true}}` — 数据仍存小数（0.0324 → 显示 3.24%）
- 货币：`{"name":"现价¥","type":"number","style":{"type":"currency","precision":2,"currency_code":"CNY"}}`
- 表头加 ¥ = 字段名直接带 ¥（现价¥、持仓市值¥、浮盈亏¥ 等），配合 currency 格式

## 5. field-update 是 FULL PUT，不是 patch

- `+field-update --json` 传**完整字段定义**；高风险操作需 `--yes`。
- 会偶发瞬时失败（exit 0 但 ok=false），**重试一次即可**（本次 4 个 currency 字段首次 3 失败，重试全过）。

## 6. 批量建表会静默丢字段 — 必须验证

- `+table-create --fields` 一次传 17 个字段，返回 ok=true 但「浮盈亏比」字段实际没建成。
- **建表后必须 `+field-list` 对照预期逐字段核对**，缺了补 `+field-create`，再迁移数据。

## 7. 脚本用字段 ID 而非字段名

- 字段改名（现价→现价¥）后，cron 更新脚本按名字写会全部失败。
- 方案：脚本里直接写字段 ID（fldXXX），改名后不用改脚本。用字段 ID 的 record-upsert：
  `--json '{"fldobqhRB6": 34.99, "fldev0IlK8": 0.0324}'`（顶层 map，不包 fields）

## 8. 其他 lark-cli 坑（复述）

- `+record-upsert` 的 `--json` 是**顶层 field map**；没有 `+record-update` 命令。
- `--json @file` 要求**相对路径**（当前目录），绝对路径 /tmp/... 被拒。
- `+record-batch-create` 的 `--json` 结构：`{"fields":["列1","列2"],"rows":[["v1","v2"]]}`，单批 ≤200。
- 旧表删除：`+table-delete --table-id <tid> --yes`；改名：`+table-update --name "新名"`。
- 迁移数据后删旧表前，**先改 cron 脚本指向新表并实测一次**（本会话：改完跑测试脚本 19/19 成功才删旧表）。

## 9. 完整流程模板（重建持仓表）

```
1. +table-create（序号主字段 + 全字段，不含 link）→ table_id
2. +field-create 自关联"父记录" link
3. +field-list 核对字段 → 补缺
4. 旧表 +record-list --format json 拉全量数据
5. +record-batch-create 写子记录（序号 1-19）
6. +record-batch-create 建父记录（序号 20-24）
7. 逐条 +record-upsert 关联父记录
8. +view-set-group 按父记录分组
9. +view-set-visible-fields 排字段顺序（序号→名称→代码→…）
10. +field-update 改百分比/货币格式（PUT 全量 + --yes）
11. 更新 cron 脚本 TABLE_ID + 字段 ID 映射 → 实测
12. +table-delete 旧表 → +table-update 新表改名
```
