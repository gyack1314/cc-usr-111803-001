# 批发日价与表格来源约定

normal.json 按顺序接收两份原文。conflict.json 的第二份与第一份使用相同资料身份和版次，但内容不同，账本应拒绝冲突。kind、id 和 revision 是来源声明，不能单独证明跨来源业务归属。

`price_correction.correction_id` 用于标识针对某观测日的官方更正。`price_correction_retraction` 通过同一 correction_id 撤回更正；撤回原文与日价页的来源版次分别接续。`withdrawal-pending.json` 表示 v2 日价已取、撤回通知仍待取，`withdrawal-complete.json` 表示撤回原文随后到达。项目值为：原日价 14.79、更正 C-1 为 14.72、日价 v2 为 14.76。

`correction-published.json` 提供 C-1，先前发布视图可保存更正后的 14.72。随后 v2 页面先到而撤回通知仍缺；通知引用 C-1 到达后，该更正才失效，当前日价回到 14.76。周表原文均值为 14.78，日价仍只有一日覆盖，周度差异可更新但周覆盖须显示不完整。
