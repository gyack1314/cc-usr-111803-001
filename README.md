# 批发猪肉价格发布与更正的连续采集

现有项目保存批发日价与表格的冻结来源响应。transport 核对请求和原文字节，domain 提取来源声明的资料身份，ledger 原子保存版本及跨地址取得依据。collection 将来源目录、待收范围与接收进度持久保存；daily_prices 提供已收到的日价查询，weekly_prices 根据周表列出当前对应的日价，view 展示这些资料和待核状态，archive 保留已发布视图。双来源初版资料已可按当前字段核对并判断发布；后续更正、撤回与范围变化尚待接续。合成样例不访问外部站点。来源字段见 docs/source-contract.md。

在项目根目录运行：

    python -m unittest discover -s tests -v
    python -m compileall -q capture_service tests
    python -m capture_service.cli inspect data/normal.json

容器运行：docker build -t pork-collection-001 .；docker run --rm pork-collection-001。
