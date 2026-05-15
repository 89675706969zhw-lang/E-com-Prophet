# E-com Prophet 需求文档

## 1. 项目名称

E-com Prophet

## 2. 项目背景

E-com Prophet 是一个面向 marketplace 卖家的电商分析与决策支持系统。目标用户是在 Wildberries、Ozon 和 Yandex Market 等平台销售商品的卖家。

在实际经营中，卖家需要经常回答以下问题：

- 哪些商品值得继续销售？
- 哪些商品需要补货？
- 每个 marketplace 应该发送多少库存？
- 哪些商品适合继续投放广告或参加促销？
- 商品当前价格是否还能保证目标利润率？
- 不同平台之间，哪些商品和类目表现更好？

由于真实 marketplace 数据难以直接获取，本项目使用生成数据模拟电商经营数据。系统支持用户上传 CSV 文件，也可以使用内置的模拟数据 `transactions_optimized.csv` 进行分析。

俄语说明：

E-com Prophet представляет собой аналитическую систему поддержки решений для продавца, который работает на маркетплейсах Wildberries, Ozon и Yandex Market. Система помогает продавцу понять, какие товары продавать, на какой маркетплейс их поставлять, сколько товара отправлять, какую цену установить и какие товары продвигать.

## 3. 系统目的

E-com Prophet 是给 marketplace 卖家使用的决策支持系统。

它帮助卖家决定：

1. 哪些商品值得继续销售；
2. 哪些商品需要补货；
3. 每个 marketplace 应该发多少货；
4. 哪些商品适合广告推广；
5. 商品价格是否还能保持目标利润率。

系统不是简单展示销售数据，而是把销售、价格、折扣、广告、佣金、物流和利润等数据结合起来，生成可以直接用于业务决策的分析结果、Markdown 报告和 CSV 文件。

## 4. 目标用户

系统的主要用户是 marketplace 卖家或电商运营人员。

用户画像：

- 在多个平台销售商品；
- 需要定期查看销售、利润和库存情况；
- 需要决定是否补货、涨价、降价或停止推广；
- 不一定具备复杂的数据分析或机器学习背景；
- 希望通过 GUI 界面快速得到推荐结果。

## 5. 当前系统实现基础

根据现有代码，项目已经实现以下模块：

- `app.py`：Streamlit GUI 主程序；
- `data_utils.py`：CSV 数据读取、数据类型处理、筛选功能；
- `models.py`：业务分析逻辑，包括需求预测、供货计划、广告分析、价格推荐和 ML 模型；
- `ui.py`：图表展示、Markdown 报告生成、CSV/Markdown 下载按钮；
- `config.py`：语言文本、文件路径、模型字段配置；
- `transactions_optimized.csv`：用于演示的生成数据。

当前系统支持俄语和中文界面切换，支持内置数据和上传 CSV 两种数据来源。

## 6. 输入数据需求

系统输入为 CSV 格式的电商数据表。

### 6.1 当前支持的核心字段

当前代码主要依赖以下字段：

- `marketplace`：销售平台，例如 OZON、WildBerries、YandexMarket；
- `product_sku`：商品 SKU；
- `category`：商品类别；
- `subcategory`：商品子类别；
- `brand`：品牌；
- `price`：原始价格；
- `discount_percent`：折扣比例；
- `final_price`：最终成交价格；
- `cost`：商品成本；
- `quantity_sold`：销售数量；
- `revenue`：销售收入；
- `commission_rate`：平台佣金比例；
- `advertising_cost`：广告费用；
- `logistics_cost`：物流费用；
- `profit`：利润；
- `margin_percent`：利润率；
- `profit_per_item`：单件利润；
- `page_views`：商品访问量；
- `add_to_cart_count`：加购数量；
- `conversion_rate`：转化率；
- `is_promo`：是否参与促销；
- `product_rating`：商品评分；
- `review_count`：评论数量；
- `marketing_roi`：广告投资回报率；
- `ad_efficiency`：广告效率。

### 6.2 上传 CSV 的优化需求

当前系统假设上传的 CSV 字段名与内部字段完全一致。为了让系统更接近真实业务场景，后续应增加“字段识别与校验”功能。

例如，用户上传的数据中可能使用不同字段名：

- `sku`、`article`、`product_id` 可以识别为 `product_sku`；
- `platform`、`marketplace`、`площадка` 可以识别为 `marketplace`；
- `sales`、`quantity`、`sold_units` 可以识别为 `quantity_sold`；
- `sales_amount`、`revenue`、`выручка` 可以识别为 `revenue`；
- `unit_price`、`price`、`цена` 可以识别为 `final_price`。

系统应在上传后自动完成：

1. 字段识别；
2. 字段标准化；
3. 缺失字段检查；
4. 根据字段完整性判断哪些功能可用；
5. 对缺失字段给出明确提示。

俄语说明：

После загрузки CSV система должна проверить структуру данных, распознать основные бизнес-поля, привести их к внутреннему формату и показать, какие функции доступны для данного файла.

## 7. 功能需求

### 7.1 数据加载与数据概览

用户可以选择两种数据来源：

1. 使用内置生成数据 `transactions_optimized.csv`；
2. 上传自己的 CSV 文件。

系统加载数据后，应在主页面展示核心指标：

- 数据行数；
- 总收入；
- 总利润；
- 平均利润率；
- 按 marketplace 汇总的收入和利润图表；
- 原始数据预览。

业务意义：

用户可以快速判断整体经营状态，以及不同 marketplace 的销售表现。

### 7.2 需求预测

功能名称：

Прогнозирование спроса / 需求预测

功能目的：

预测商品在未来 14 天或 30 天的预期销售数量。

当前实现逻辑：

系统基于历史销售数量，并结合以下因素调整预测结果：

- 转化率；
- 商品评分；
- 是否参加促销；
- 折扣比例；
- 预测周期。

当前输出字段包括：

- `marketplace`
- `product_sku`
- `category`
- `subcategory`
- `brand`
- `final_price`
- `quantity_sold`
- `forecast_quantity`
- `expected_revenue`
- `expected_profit`
- `margin_percent`
- `conversion_rate`
- `product_rating`
- `is_promo`

业务意义：

卖家可以通过预测结果判断哪些商品未来需求更高，从而提前准备库存。

### 7.3 供货计划

功能名称：

Планирование поставок / 供货计划

功能目的：

根据需求预测、利润率和目标利润率，决定哪些商品需要补货、补多少，以及应该发往哪个 marketplace。

当前实现逻辑：

系统先计算需求预测，然后判断商品是否满足盈利条件：

- 预期利润大于 0；
- 当前利润率大于或等于目标利润率。

如果商品满足条件，系统推荐补货数量为预测销量的 115%，其中 15% 作为安全库存。

当前输出字段包括：

- `marketplace`
- `product_sku`
- `category`
- `subcategory`
- `forecast_quantity`
- `recommended_supply_quantity`
- `expected_revenue`
- `expected_profit`
- `margin_percent`
- `priority_level`

系统还支持为不同 marketplace 生成单独的 CSV 文件：

- `supply_plan_wildberries.csv`
- `supply_plan_ozon.csv`
- `supply_plan_yandex_market.csv`

业务意义：

该功能回答老师提出的核心问题：系统会规划“向哪个 marketplace 投放或供货哪些商品”。

优化建议：

后续应增加库存字段，让供货逻辑更真实：

- `current_stock`
- `reserved_stock`
- `safety_stock`
- `days_of_stock_left`

推荐公式可以优化为：

`recommended_supply_quantity = max(0, forecast_quantity + safety_stock - current_stock)`

这样系统不仅预测需求，还能结合当前库存决定实际补货量。

### 7.4 广告与促销分析

功能名称：

Анализ рекламы и промо / 广告与促销分析

功能目的：

判断商品是否适合继续广告推广或参加促销。

当前实现逻辑：

系统根据以下指标判断广告和促销效果：

- 利润；
- 广告 ROI；
- 转化率；
- 是否参加促销；
- 折扣比例；
- 广告费用。

当前推荐结果包括：

- `Promote more`：建议继续或加大推广；
- `Monitor`：建议观察；
- `Stop or reduce`：建议停止或减少推广。

当前输出字段包括：

- `marketplace`
- `product_sku`
- `category`
- `brand`
- `promo_status`
- `discount_percent`
- `advertising_cost`
- `marketing_roi`
- `conversion_rate`
- `revenue`
- `profit`
- `margin_percent`
- `recommendation`

业务意义：

卖家可以识别哪些广告有效，哪些广告不赚钱，从而优化广告预算。

### 7.5 价格推荐

功能名称：

Рекомендация цены / 价格推荐

功能目的：

根据成本、平台佣金、物流费用、广告费用和目标利润率，计算推荐售价。

当前实现逻辑：

系统计算单件综合成本，然后根据目标利润率反推出推荐价格。

当前输出字段包括：

- `marketplace`
- `product_sku`
- `category`
- `brand`
- `price`
- `final_price`
- `cost`
- `commission_rate`
- `logistics_cost`
- `advertising_cost`
- `margin_percent`
- `recommended_price`
- `price_action`

价格操作建议包括：

- `Increase price`：建议提高价格；
- `Price can be reduced`：价格可以降低；
- `Keep price`：保持价格。

业务意义：

卖家可以判断当前商品价格是否能覆盖成本和费用，并保持目标利润率。

### 7.6 ML 模型与指标

功能名称：

ML-модель и метрики / 机器学习模型与指标

功能目的：

使用机器学习模型对商品销量进行预测，并比较不同模型效果。

当前实现模型包括：

- Linear Regression；
- Random Forest；
- Gradient Boosting。

当前评估指标包括：

- MAE；
- RMSE；
- R²。

系统根据 MAE 选择最佳模型，并用该模型生成销量预测。

业务意义：

该模块用于展示系统不仅支持规则预测，也支持机器学习预测，并能通过指标评估模型质量。

## 8. 分析模式需求

系统应支持两种分析模式：

### 8.1 单个商品分析

用户选择具体 SKU 后，系统只分析该商品。

适用场景：

- 卖家想检查某一个商品是否值得补货；
- 卖家想知道某个商品是否需要调价；
- 卖家想判断某个商品是否适合继续推广。

### 8.2 批量商品分析

用户选择 `全部 / Все` 时，系统对所有商品进行批量分析。

适用场景：

- 卖家需要生成完整补货计划；
- 卖家需要导出所有商品的推荐结果；
- 卖家需要按 marketplace 下载独立 CSV 文件。

优化建议：

当前系统通过选择 `Все` 实现批量分析，但界面没有明确说明。建议在 GUI 中新增“分析模式”选项：

- `Один товар / 单个商品`
- `Все товары / 全部商品`

## 9. 输出需求

系统输出包括 GUI 展示、CSV 文件和 Markdown 报告。

### 9.1 GUI 输出

GUI 应展示：

- 总体 KPI；
- marketplace 收入和利润图表；
- 筛选后的数据表；
- 各功能的分析结果表；
- 14 天和 30 天预测对比图；
- 简化的每日预测曲线；
- 下载按钮。

### 9.2 CSV 输出

不同功能应输出不同 CSV 文件：

- `demand_forecast.csv`
- `supply_plan_all_marketplaces.csv`
- `supply_plan_wildberries.csv`
- `supply_plan_ozon.csv`
- `supply_plan_yandex_market.csv`
- `promo_advertising_analysis.csv`
- `price_recommendations.csv`
- `ml_demand_forecast.csv`

其中供货计划 CSV 是最重要的业务输出，因为它可以直接回答：

- 哪些商品需要补货；
- 补货数量是多少；
- 应该发往哪个 marketplace；
- 预期利润是多少；
- 优先级是什么。

### 9.3 Markdown 报告输出

系统应生成 Markdown 分析报告。

当前报告已经包含：

- 分析参数；
- 数据行数；
- 总收入；
- 总利润；
- 平均利润率；
- ML 指标；
- 简短结论。

建议进一步增加：

- 每个平台表现汇总；
- 推荐补货商品 Top 10；
- 高利润商品 Top 10；
- 不建议补货商品；
- 广告推广建议；
- 价格调整建议；
- 最终业务结论。

示例结论：

根据分析，Wildberries 上部分类目的预期利润最高，建议优先补货。Ozon 上部分商品广告 ROI 较低，建议减少广告预算。Yandex Market 上部分商品利润率低于目标值，建议提高价格或停止补货。

## 10. 多语言需求

系统应支持俄语和中文两种语言。

当前代码已经通过 `config.py` 中的 `TEXT` 字典实现界面文本切换。

要求：

- 用户可以在侧边栏切换语言；
- 主要按钮、标题、筛选器和结果说明应随语言切换；
- Markdown 报告也应根据当前语言生成；
- 后续应检查所有文本编码，避免出现乱码。

## 11. GUI 需求

系统使用 Streamlit 实现 GUI。

页面结构：

1. 左侧栏：
   - 语言选择；
   - 数据来源选择；
   - 功能选择；
   - marketplace 筛选；
   - category 筛选；
   - SKU 筛选；
   - 预测周期选择；
   - 目标利润率设置；
   - ML 训练样本大小；
   - 运行分析按钮。

2. 主页面：
   - 系统标题；
   - 系统用途说明；
   - KPI 指标；
   - 数据概览图表；
   - 数据预览；
   - 分析结果；
   - 下载按钮。

## 12. 非功能需求

### 12.1 易用性

用户不需要写代码，只需要上传 CSV、选择功能和筛选条件，即可获得分析结果。

### 12.2 可解释性

每个功能都应提供简单说明，让用户知道：

- 这个功能解决什么业务问题；
- 使用了哪些数据；
- 输出结果如何理解。

### 12.3 可扩展性

系统后续可以扩展：

- 新 marketplace；
- 新商品类别；
- 更复杂的库存逻辑；
- 更准确的时间序列预测；
- 自动字段识别；
- 真实 API 数据接入。

### 12.4 数据兼容性

系统应支持内置数据，也应支持用户上传 CSV。

后续应加强上传 CSV 的字段识别、字段映射和错误提示。

## 13. 当前项目存在的问题

根据现有代码和界面，当前项目主要存在以下问题：

1. 系统用途说明还不够明显，老师可能看不出系统具体服务于卖家的哪些业务决策；
2. 单品分析和批量分析已经存在，但没有在 GUI 中明确标出；
3. 上传 CSV 目前要求字段名与系统内部字段一致，缺少自动字段识别；
4. 供货计划逻辑还比较简化，没有结合真实库存；
5. Markdown 报告内容偏简单，还没有把核心推荐结果写入报告；
6. 部分代码注释或文本可能存在编码问题，需要统一检查；
7. 生成数据虽然字段完整，但应保证商品类别、SKU 和品牌名称看起来更接近真实电商场景。

## 14. 优化优先级

### 第一优先级

1. 在首页增加系统目的说明；
2. 在 GUI 中明确“单品分析 / 批量分析”；
3. 增强 Markdown 报告，把推荐结果写入报告；
4. 对上传 CSV 增加字段校验和缺失提示。

### 第二优先级

1. 增加库存字段，优化供货计划；
2. 让系统输出更完整的平台级供货 CSV；
3. 增加每个平台的推荐补货数量汇总图；
4. 优化价格推荐结果，显示调整后的预计利润率。

### 第三优先级

1. 增加自动字段识别；
2. 增加真实 marketplace API 接入的可能性说明；
3. 增强 ML 模型；
4. 增加时间序列预测模型。

## 15. 答辩说明建议

可以这样向老师介绍项目：

E-com Prophet 是一个面向 marketplace 卖家的分析系统。它的目的不是简单显示销售数据，而是帮助卖家做经营决策。用户可以上传电商 CSV 数据，系统会分析销售、价格、折扣、广告、佣金、物流和利润等指标。系统支持需求预测、供货计划、广告和促销分析、价格推荐以及机器学习预测。

最重要的输出是供货计划文件。系统可以生成所有 marketplace 的总供货计划，也可以分别生成 Wildberries、Ozon 和 Yandex Market 的 CSV 文件。卖家可以根据这些文件看到每个商品的预测需求、推荐补货数量、预期利润和优先级。

俄语版本：

E-com Prophet — это система поддержки решений для продавца на маркетплейсах. Она не просто показывает продажи, а помогает принять практические решения: какие товары продавать, куда их поставлять, сколько товара отправить, какие товары продвигать и какую цену установить. Пользователь загружает CSV-файл с данными, после чего система выполняет прогноз спроса, планирование поставок, анализ рекламы и промо, рекомендацию цены и ML-прогноз. Главный результат работы системы — аналитический отчет Markdown и CSV-файлы с рекомендациями по поставкам для Wildberries, Ozon и Yandex Market.

## 16. 开发问题 1：上传 CSV 后如何识别字段并保证功能可运行

### 16.1 问题描述

当前系统已经支持上传 CSV 文件，但现有代码默认上传文件的字段名必须和系统内部字段完全一致。例如系统需要 `product_sku`、`quantity_sold`、`final_price`、`marketplace` 等字段。

真实用户上传的电商表格不一定使用这些字段名。例如：

- 商品编号可能叫 `sku`、`article`、`product_id`、`артикул`；
- 销售数量可能叫 `sales`、`quantity`、`sold_units`、`количество`；
- 平台可能叫 `platform`、`marketplace`、`площадка`；
- 收入可能叫 `revenue`、`sales_amount`、`выручка`；
- 价格可能叫 `price`、`unit_price`、`цена`。

因此，如果系统只是读取 CSV 然后直接调用分析函数，很多真实 CSV 会因为字段缺失而报错。为了让系统更接近真实业务工具，需要增加一个“数据识别与预处理层”。

### 16.2 目标效果

用户上传 CSV 后，系统不应立即进入分析，而应先完成以下流程：

```text
上传 CSV
    ↓
字段识别
    ↓
字段标准化
    ↓
缺失字段检查
    ↓
自动计算派生字段
    ↓
判断每个功能是否可用
    ↓
用户选择功能
    ↓
生成分析表格、CSV 和 Markdown 报告
```

系统应在 GUI 中向用户显示：

- 已识别出的字段；
- 未识别字段；
- 自动映射结果；
- 缺失的必要字段；
- 当前 CSV 可以运行哪些功能；
- 当前 CSV 不能运行哪些功能以及原因。

### 16.3 字段标准化方案

建议新增 `schema_utils.py` 模块，负责字段识别、字段映射和字段检查。

核心设计：

```python
COLUMN_ALIASES = {
    "product_sku": ["product_sku", "sku", "article", "product_id", "item_id", "артикул", "товар"],
    "marketplace": ["marketplace", "platform", "channel", "площадка", "маркетплейс"],
    "category": ["category", "product_category", "категория"],
    "final_price": ["final_price", "price", "unit_price", "sale_price", "цена"],
    "quantity_sold": ["quantity_sold", "quantity", "sales", "sold_units", "units_sold", "количество"],
    "revenue": ["revenue", "sales_amount", "turnover", "выручка"],
    "cost": ["cost", "unit_cost", "purchase_price", "себестоимость"],
    "commission_rate": ["commission_rate", "commission", "platform_fee_rate", "комиссия"],
    "logistics_cost": ["logistics_cost", "shipping_cost", "delivery_cost", "логистика"],
    "advertising_cost": ["advertising_cost", "ad_cost", "marketing_cost", "реклама"],
    "conversion_rate": ["conversion_rate", "conversion", "cr", "конверсия"],
}
```

字段识别应先基于字段名匹配。后续可以增加更复杂的识别方法，例如：

- 根据字段值的数据类型判断；
- 根据数值范围判断；
- 根据字段内容示例判断；
- 让用户在 GUI 中手动确认字段映射。

### 16.4 功能可用性检查

不同功能需要不同字段。系统应为每个功能定义最低字段要求。

需求预测最低字段：

```text
product_sku
marketplace
quantity_sold
final_price
```

供货计划最低字段：

```text
product_sku
marketplace
quantity_sold
final_price
cost
```

广告与促销分析最低字段：

```text
product_sku
marketplace
advertising_cost
conversion_rate
profit
marketing_roi
```

价格推荐最低字段：

```text
product_sku
marketplace
cost
commission_rate
logistics_cost
advertising_cost
final_price
```

ML 模型最低字段：

```text
quantity_sold
至少 3 个可用特征字段
足够的数据行数
```

如果某个功能缺少必要字段，系统不应报错，而应显示：

```text
当前 CSV 不能运行广告分析。
原因：缺少 advertising_cost、conversion_rate、marketing_roi。
```

### 16.5 自动计算派生字段

部分字段可以根据已有字段自动生成。

例如：

```text
revenue = final_price * quantity_sold
commission_cost = revenue * commission_rate
profit = revenue - cost * quantity_sold - logistics_cost - advertising_cost - commission_cost
margin_percent = profit / revenue * 100
profit_per_item = profit / quantity_sold
marketing_roi = profit / advertising_cost
conversion_rate = quantity_sold / page_views
```

注意：

- 自动计算字段时需要处理除零问题；
- 如果必要输入字段不存在，则不能计算；
- 系统应在报告中说明哪些字段来自原始 CSV，哪些字段由系统计算得到。

### 16.6 降级分析策略

真实 CSV 经常字段不完整，因此系统应支持降级分析。

示例：

- 如果没有广告字段，可以禁用广告分析，但仍允许需求预测；
- 如果没有库存字段，可以使用简化版供货计划；
- 如果有库存字段，则使用完整版供货计划；
- 如果没有 `product_rating` 或 `conversion_rate`，需求预测可以使用基础销量预测，不使用这些修正因子；
- 如果 ML 特征不足，则不训练 ML 模型，只显示规则预测结果。

这样系统可以尽可能给出可用分析，而不是因为缺少某个字段导致整个程序失败。

### 16.7 第一阶段实现目标

第一阶段不需要做到任意 CSV 完全自动识别。更合理的目标是：

1. 支持常见电商字段名映射；
2. 上传后显示字段识别结果；
3. 显示每个功能是否可运行；
4. 缺字段时给出明确原因；
5. 自动计算 revenue、profit、margin_percent 等基础派生字段；
6. 对不可运行功能进行禁用或提示；
7. 成功运行可用功能并生成分析表格、CSV 和 Markdown 报告。

## 17. 开发问题 2：ML 模型预测与特征工程如何处理

### 17.1 当前 ML 模块现状

当前系统在 `models.py` 中已经实现 ML 模块。系统会训练三个回归模型：

- Linear Regression；
- Random Forest；
- Gradient Boosting。

目标变量是：

```text
quantity_sold
```

当前特征主要来自 `config.py` 中的：

- `LOW_CARDINALITY_CAT_FEATURES`
- `NUMERIC_FEATURES`
- `ML_FEATURES`

系统会使用 MAE、RMSE、R² 评估模型，并选择 MAE 最低的模型作为最佳模型。

### 17.2 当前 ML 问题

当前 ML 模块的问题是：它也假设上传 CSV 一定包含固定特征字段。

如果用户上传的数据缺少某些字段，例如：

- `conversion_rate`
- `product_rating`
- `review_count`
- `marketing_roi`
- `ad_efficiency`
- `weekday_type`
- `price_segment`

那么当前 ML 训练流程可能无法运行。

因此，ML 模块也必须接入“字段识别、字段标准化、字段可用性检查和特征工程”流程。

### 17.3 ML 可运行性判断

ML 模型不能只检查目标变量是否存在，还需要检查：

1. 是否存在目标字段 `quantity_sold`；
2. 是否有足够的数据行数；
3. 是否有足够的可用特征；
4. 特征是否存在严重缺失；
5. 类别特征是否可以编码；
6. 数值特征是否可以转换为数字；
7. 训练集和测试集划分后是否仍有足够样本。

建议第一阶段设置最低要求：

```text
quantity_sold 必须存在
数据行数不少于 100 行
可用特征不少于 3 个
目标变量不能全部相同
```

如果不满足要求，GUI 应显示：

```text
当前 CSV 不适合训练 ML 模型。
原因：缺少目标字段 quantity_sold，或可用特征不足。
```

### 17.4 特征工程方案

ML 模型的特征工程应分为四类。

#### 17.4.1 基础商品特征

这些特征描述商品本身：

- `marketplace`
- `category`
- `subcategory`
- `brand`
- `price`
- `final_price`
- `discount_percent`
- `price_segment`

用途：

帮助模型学习不同平台、类目、品牌和价格区间对销量的影响。

#### 17.4.2 销售与流量特征

这些特征描述用户行为和销售过程：

- `page_views`
- `add_to_cart_count`
- `conversion_rate`
- `review_count`
- `product_rating`

用途：

帮助模型判断商品受欢迎程度和转化能力。

#### 17.4.3 成本与利润特征

这些特征描述商品经济性：

- `cost`
- `commission_rate`
- `advertising_cost`
- `logistics_cost`
- `profit_per_item`
- `margin_percent`
- `marketing_roi`
- `ad_efficiency`

用途：

帮助模型学习价格、成本、广告和利润结构对销量的影响。

#### 17.4.4 时间特征

这些特征描述销售发生的时间：

- `order_date`
- `month`
- `week`
- `day_of_week`
- `quarter`
- `is_holiday`
- `weekday_type`

如果 CSV 只有 `order_date`，系统应自动提取：

```text
year
month
week
day_of_week
quarter
weekday_type
```

用途：

帮助模型识别季节性、周末效应和节假日影响。

### 17.5 自动特征生成

为了让 ML 适配更多上传 CSV，系统应支持自动生成一部分特征。

示例：

```text
discount_percent = (price - final_price) / price * 100
revenue = final_price * quantity_sold
profit_per_item = profit / quantity_sold
margin_percent = profit / revenue * 100
conversion_rate = quantity_sold / page_views
ad_efficiency = revenue / advertising_cost
marketing_roi = profit / advertising_cost
price_segment = 根据 final_price 分箱生成
weekday_type = 根据 day_of_week 生成 weekday/weekend
```

如果无法生成某个特征，则从 ML 特征列表中移除，而不是让模型报错。

### 17.6 动态特征选择

当前代码使用固定的 `ML_FEATURES`。优化后应改为动态特征选择。

流程：

```text
读取标准化后的 DataFrame
    ↓
从候选特征列表中选择实际存在的字段
    ↓
区分数值特征和类别特征
    ↓
删除缺失率过高的特征
    ↓
对数值特征填充中位数
    ↓
对类别特征填充 Unknown
    ↓
编码类别特征
    ↓
训练模型
```

这样即使用户上传的 CSV 字段不完整，ML 模型也可以用已有字段训练。

### 17.7 类别特征编码

对于类别字段，例如 `marketplace`、`category`、`brand`、`price_segment`，需要编码后才能进入模型。

建议策略：

- 低基数类别字段使用 One-Hot Encoding；
- 高基数字段如 `product_sku`、`brand` 不建议直接 One-Hot；
- 高基数字段可以暂时不用，或使用 Target Encoding；
- 如果数据量较小，不建议使用过多高基数字段，避免过拟合。

当前代码已经使用 `TargetEncoder`，这是一个可以保留的方向。

### 17.8 缺失值处理

ML 模型训练前必须处理缺失值。

建议：

- 数值字段：使用中位数填充；
- 类别字段：使用 `Unknown` 填充；
- 缺失率超过 60% 的字段：从特征中移除；
- 目标变量 `quantity_sold` 缺失的行：删除。

### 17.9 模型评估

ML 模型输出不仅应给出预测结果，还应解释模型质量。

应展示：

- MAE：平均绝对误差；
- RMSE：均方根误差；
- R²：模型解释能力；
- 最佳模型名称；
- 使用了哪些特征；
- 训练数据行数；
- 测试数据行数。

报告中应写明：

```text
本次 ML 模型使用 X 行数据训练，使用 Y 个特征。
最佳模型为 Random Forest，MAE 为 ...。
如果上传 CSV 字段较少，ML 预测准确性会下降。
```

### 17.10 ML 输出结果

ML 预测结果应包括：

- `marketplace`
- `product_sku`
- `category`
- `quantity_sold`
- `ml_forecast_quantity`
- `expected_revenue`
- `expected_profit`
- `margin_percent`

如果部分字段缺失，则输出可用字段，并在报告中说明缺失情况。

### 17.11 ML 降级方案

如果上传 CSV 不满足 ML 训练要求，系统应自动降级：

1. 不训练 ML 模型；
2. 显示不能训练的原因；
3. 建议用户补充哪些字段；
4. 允许继续使用规则预测功能；
5. Markdown 报告中记录 ML 未运行原因。

示例：

```text
ML 模型未运行。
原因：当前 CSV 缺少 quantity_sold，无法定义监督学习目标。
建议补充字段：quantity_sold、final_price、marketplace、category、page_views。
```

### 17.12 ML 第一阶段实现目标

第一阶段 ML 优化不需要追求复杂模型，而应保证系统稳定可运行。

建议目标：

1. 使用字段识别后的标准化数据训练 ML；
2. 动态选择存在的 ML 特征；
3. 自动生成基础派生特征；
4. 缺失值自动处理；
5. 判断 ML 是否可运行；
6. 不可运行时给出清楚原因；
7. 可运行时输出模型指标、预测结果和 Markdown 报告；
8. 报告中说明本次使用了哪些特征。

### 17.13 俄语说明

Для ML-модуля система должна не только обучать модель на фиксированном наборе колонок, но и проверять, какие признаки реально доступны в загруженном CSV-файле. После загрузки данных система должна распознать поля, создать производные признаки, выбрать доступные числовые и категориальные признаки, обработать пропуски и только после этого обучать модель. Если данных недостаточно, система не должна выдавать ошибку, а должна объяснить, почему ML-прогноз недоступен и какие поля нужно добавить.

## 18. 具体开发计划与未解决问题解决方案

本节用于把当前项目中尚未解决的问题转化为可执行的开发任务。每个问题都包含：现状、影响、解决方案、涉及模块和验收标准。

### 18.1 问题一：系统用途说明不够明显

现状：

当前 GUI 首页只有标题、简短副标题、KPI 和数据概览图。虽然系统已经包含需求预测、供货计划、广告分析、价格推荐和 ML 预测，但老师或用户第一次打开系统时，可能无法立刻理解系统到底为卖家解决什么业务问题。

影响：

- 项目展示时容易被认为只是普通数据看板；
- 老师提出的“系统为什么存在、为你的活动做什么”没有在界面上直接回答；
- 用户不知道不同功能和实际经营决策之间的关系。

解决方案：

在首页标题下方增加“系统目的 / Цель системы”说明区域。内容应明确写出系统帮助卖家决定：

1. 哪些商品值得继续销售；
2. 哪些商品需要补货；
3. 每个 marketplace 应该发多少货；
4. 哪些商品适合广告推广；
5. 商品价格是否还能保持目标利润率。

建议 GUI 中展示为一个简洁说明区，而不是长篇文字。俄语和中文都应支持。

涉及模块：

- `config.py`：新增中俄双语文本；
- `app.py`：在标题和 KPI 之间展示系统目的说明；
- `ui.py`：可以新增说明组件函数，例如 `show_system_purpose()`。

验收标准：

- 打开首页后，用户无需点击任何按钮即可看到系统用途；
- 说明中明确出现 marketplace、供货、价格、广告、利润率等业务关键词；
- 中文和俄语切换后内容正常显示；
- 文本没有乱码。

优先级：

高。

### 18.2 问题二：单品分析和批量分析没有在 GUI 中明确标出

现状：

当前系统通过 SKU 下拉框实现两种分析：

- 选择具体 SKU：单品分析；
- 选择 `Все / 全部`：批量分析。

但是 GUI 没有明确写出“单品分析 / 批量分析”，用户和老师不一定能看懂这个逻辑。

影响：

- 项目描述中提到系统支持单个商品和批量分析，但界面没有直观体现；
- 老师可能认为系统只是在筛选数据；
- 批量生成 CSV 的业务意义不够明显。

解决方案：

在侧边栏新增“分析模式 / Режим анализа”选项：

- `Один товар / 单个商品`
- `Все товары / 全部商品`

交互逻辑：

- 如果选择“单个商品”，SKU 下拉框必须选择具体 SKU；
- 如果选择“全部商品”，SKU 自动设置为 `Все / 全部`；
- 批量模式下，供货计划应显示 marketplace 分文件下载按钮；
- 单品模式下，报告和 CSV 应只包含该商品。

涉及模块：

- `config.py`：新增模式相关文本；
- `app.py`：新增分析模式控件和 SKU 联动逻辑；
- `data_utils.py`：根据模式筛选数据；
- `ui.py`：报告中写明当前分析模式。

验收标准：

- GUI 中可以清楚看到“单个商品 / 全部商品”模式；
- 单品模式下只输出一个 SKU 的分析结果；
- 批量模式下输出全部商品结果；
- 批量供货计划可以生成所有 marketplace 的 CSV。

优先级：

高。

### 18.3 问题三：上传 CSV 缺少字段识别与功能可用性判断

现状：

当前系统可以上传 CSV，但默认上传文件字段必须和系统内部字段一致。如果用户上传真实电商 CSV，字段名可能不同，系统容易报错。

影响：

- 系统不能稳定处理真实用户数据；
- 上传 CSV 功能看起来存在，但实用性不足；
- 后续需求预测、供货计划、广告分析、价格推荐和 ML 模型都可能失败。

解决方案：

新增“CSV schema 识别与校验层”。

完整流程：

```text
上传 CSV
    ↓
读取原始字段
    ↓
字段名标准化
    ↓
根据别名表映射到内部字段
    ↓
检查每个功能需要的字段
    ↓
自动计算可派生字段
    ↓
显示可用功能和不可用原因
    ↓
运行可用分析
```

建议新增模块：

```text
schema_utils.py
```

核心函数建议：

```python
detect_columns(df) -> dict
standardize_columns(df, mapping) -> pd.DataFrame
derive_missing_columns(df) -> pd.DataFrame
check_feature_availability(df) -> dict
build_schema_report(df, mapping, availability) -> str
```

功能可用性规则：

- 需求预测：至少需要 `product_sku`、`marketplace`、`quantity_sold`、`final_price`；
- 供货计划：至少需要需求预测字段和 `cost`；
- 广告分析：至少需要 `advertising_cost`、`conversion_rate`、`profit` 或可计算 profit；
- 价格推荐：至少需要 `cost`、`commission_rate`、`final_price`；
- ML 模型：至少需要 `quantity_sold`、足够数据行和至少 3 个可用特征。

涉及模块：

- 新增 `schema_utils.py`；
- `data_utils.py`：上传 CSV 后调用 schema 识别；
- `app.py`：显示字段识别结果和功能可用性；
- `models.py`：分析函数支持字段缺失时的降级逻辑；
- `ui.py`：报告中写入字段识别结果。

验收标准：

- 上传字段名不同但含义相同的 CSV 后，系统能自动映射核心字段；
- 缺少字段时不直接报错，而是显示缺失字段；
- GUI 显示“可运行功能 / 不可运行功能”；
- 至少可以成功运行一个可用功能并导出 CSV 和 Markdown 报告。

优先级：

最高。

### 18.4 问题四：供货计划逻辑过于简化，没有结合真实库存

现状：

当前供货计划逻辑为：

```text
recommended_supply_quantity = forecast_quantity * 1.15
```

该逻辑可以作为简化演示，但不像真实补货决策。真实场景中应考虑当前库存、预留库存、安全库存和未来需求。

影响：

- 老师可能认为供货计划只是预测销量的简单放大；
- 不能完整回答“每个平台应该发多少货”；
- CSV 文件作为实际补货清单的说服力不足。

解决方案：

增加库存相关字段和两级供货逻辑。

建议字段：

- `current_stock`：当前库存；
- `reserved_stock`：已预留库存；
- `available_stock`：可用库存；
- `safety_stock`：安全库存；
- `days_of_stock_left`：预计库存可支撑天数。

推荐公式：

```text
available_stock = current_stock - reserved_stock
safety_stock = forecast_quantity * safety_stock_rate
recommended_supply_quantity = max(0, forecast_quantity + safety_stock - available_stock)
```

如果上传 CSV 没有库存字段，则使用降级方案：

```text
recommended_supply_quantity = forecast_quantity * 1.15
```

但报告中要说明：

```text
当前 CSV 缺少库存字段，系统使用简化供货计划。
```

涉及模块：

- `transactions_optimized.csv` 或数据生成逻辑：增加库存字段；
- `models.py`：优化 `build_supply_plan()`；
- `ui.py`：供货报告写明使用的是完整逻辑还是简化逻辑；
- `app.py`：供货计划结果表增加库存字段。

验收标准：

- 有库存字段时，补货数量根据库存计算；
- 无库存字段时，系统自动降级，不报错；
- 供货计划 CSV 包含 forecast、stock、recommended supply、profit、priority；
- 每个平台都能下载独立供货 CSV。

优先级：

高。

### 18.5 问题五：Markdown 报告内容偏简单

现状：

当前 Markdown 报告主要包含分析参数、数据行数、总收入、总利润、平均利润率和简短结论。核心推荐结果没有系统性写入报告。

影响：

- 报告不能独立说明分析结果；
- 用户下载报告后仍需要回到 GUI 查看表格；
- 老师可能认为报告只是形式化输出。

解决方案：

增强 Markdown 报告结构。

建议报告包含：

1. 分析目的；
2. 数据来源；
3. 字段识别结果；
4. 可运行功能说明；
5. 分析参数；
6. 总体 KPI；
7. marketplace 表现汇总；
8. 推荐补货商品 Top 10；
9. 高利润商品 Top 10；
10. 不建议补货或低优先级商品；
11. 广告推广建议；
12. 价格调整建议；
13. ML 模型指标和使用特征；
14. 最终业务结论。

不同功能的报告应有不同重点：

- 需求预测报告重点写预测销量和预期利润；
- 供货计划报告重点写补货数量、平台和优先级；
- 广告分析报告重点写推广、观察、停止推广；
- 价格推荐报告重点写当前价格、推荐价格和操作建议；
- ML 报告重点写模型指标、特征和预测结果。

涉及模块：

- `ui.py`：重构 `make_report()`；
- `schema_utils.py`：提供字段识别报告；
- `models.py`：输出结果中保留报告需要的字段。

验收标准：

- Markdown 报告可以独立阅读；
- 报告中至少包含 Top 10 推荐结果；
- 报告中说明当前功能的业务意义；
- 报告中说明缺失字段和降级逻辑；
- 中文和俄语报告都能正常生成。

优先级：

高。

### 18.6 问题六：代码和文本存在编码风险

现状：

部分 Python 文件中的注释和文本曾经出现乱码。GUI 当前显示正常，但代码层面仍需要统一检查编码，避免后续维护和报告生成时出现问题。

影响：

- 代码可读性下降；
- 文档或报告可能出现乱码；
- 中俄双语文本维护困难；
- 答辩展示时如果出现乱码，会明显影响项目质量。

解决方案：

统一项目编码为 UTF-8。

具体措施：

1. 所有 `.py` 和 `.md` 文件使用 UTF-8 保存；
2. 删除或修复乱码注释；
3. 中俄文本统一放在 `config.py` 或独立语言文件中；
4. CSV 导出继续使用 `utf-8-sig`，方便 Excel 打开；
5. Markdown 报告使用 UTF-8；
6. 测试中文、俄语界面和报告是否正常。

涉及模块：

- `config.py`
- `app.py`
- `models.py`
- `ui.py`
- `data_utils.py`
- `requirements_document.md`

验收标准：

- Python 文件中不再出现乱码注释；
- GUI 中俄双语正常显示；
- 下载的 CSV 在 Excel 中正常显示；
- Markdown 报告中文和俄语正常显示；
- 终端编码问题不影响文件本身内容。

优先级：

中。

### 18.7 问题七：生成数据应更接近真实电商场景

现状：

当前生成数据字段比较完整，但如果商品类别、SKU、品牌名称看起来不真实，会削弱系统展示效果。

影响：

- 老师可能认为数据是随机构造，业务意义不强；
- 图表和筛选器中的类别不够真实；
- 报告中的商品推荐看起来不像真实 marketplace 场景。

解决方案：

优化模拟数据，使字段值更接近真实电商。

建议类别：

- Электроника / 电子产品；
- Одежда и обувь / 服装鞋类；
- Красота и здоровье / 美妆健康；
- Товары для дома / 家居用品；
- Детские товары / 儿童用品；
- Спорт и отдых / 运动休闲。

建议 SKU 格式：

```text
WB-ELEC-000001
OZON-BEAUTY-000002
YM-HOME-000003
```

建议品牌格式：

```text
Brand-A
Brand-B
HomePro
BeautyLab
SportLine
```

数据生成还应包含更真实的业务关系：

- 高折扣通常提高销量但降低利润率；
- 广告费用高不一定 ROI 高；
- 评分高的商品转化率更高；
- 不同 marketplace 佣金和物流成本不同；
- 节假日销量可能更高；
- 库存低但预测高的商品应优先补货。

涉及模块：

- 数据生成脚本，如果后续新增；
- `transactions_optimized.csv`；
- `config.py` 中 marketplace 文件映射；
- 测试报告。

验收标准：

- GUI 中类别、SKU、品牌看起来真实；
- 数据字段覆盖所有主要功能；
- 至少包含 3 个 marketplace；
- 至少包含 5 个商品类别；
- 数据能成功运行所有功能。

优先级：

中。

### 18.8 问题八：ML 模型特征工程仍需增强

现状：

当前 ML 模型使用固定特征列表。如果上传 CSV 缺少这些字段，ML 模型可能无法运行。模型训练结果也没有清楚说明使用了哪些特征。

影响：

- ML 模块对真实 CSV 兼容性不足；
- 用户不知道模型为什么能预测或不能预测；
- 模型指标难以解释；
- 容易出现固定字段依赖问题。

解决方案：

改为动态特征工程。

具体流程：

```text
标准化 DataFrame
    ↓
自动生成派生字段
    ↓
选择当前存在的候选特征
    ↓
区分数值特征和类别特征
    ↓
删除缺失率过高字段
    ↓
填充缺失值
    ↓
编码类别字段
    ↓
训练多个模型
    ↓
输出指标、最佳模型和使用特征
```

ML 可运行最低要求：

- 存在目标字段 `quantity_sold`；
- 数据不少于 100 行；
- 可用特征不少于 3 个；
- 目标变量不能全部相同。

涉及模块：

- `models.py`：重构 `train_ml_models()` 和 `ml_forecast()`；
- `config.py`：保留候选特征池，而不是固定必需特征；
- `schema_utils.py`：提供可用特征检查；
- `ui.py`：报告展示模型使用特征和不能运行原因。

验收标准：

- 缺少部分 ML 字段时，模型仍可使用已有字段训练；
- 字段不足时不报错，而是说明原因；
- ML 报告中显示训练行数、测试行数、使用特征、最佳模型和指标；
- 预测结果可下载为 CSV。

优先级：

高。

### 18.9 问题九：缺少错误处理和用户提示

现状：

如果数据为空、字段缺失、类型错误或模型训练失败，当前系统可能直接报错，用户不一定知道如何处理。

影响：

- 用户体验不稳定；
- 上传真实 CSV 时风险较高；
- 答辩演示中如果报错，会影响展示效果。

解决方案：

增加统一错误处理和提示。

需要处理的情况：

- CSV 文件无法读取；
- CSV 编码不正确；
- 数据为空；
- 必要字段缺失；
- 数值字段无法转换；
- 筛选后没有数据；
- ML 数据不足；
- 导出结果为空。

建议 GUI 提示：

- `st.error()`：严重错误，无法继续；
- `st.warning()`：字段缺失或功能不可用；
- `st.info()`：系统使用了降级逻辑；
- `st.success()`：分析完成。

涉及模块：

- `data_utils.py`
- `schema_utils.py`
- `app.py`
- `models.py`

验收标准：

- 上传错误 CSV 时系统不崩溃；
- 缺字段时显示清楚原因；
- 筛选结果为空时显示提示；
- ML 不能运行时显示原因和建议补充字段。

优先级：

高。

### 18.10 问题十：缺少系统测试用例

现状：

项目有测试报告，但缺少系统化的测试数据和测试步骤来验证每个功能。

影响：

- 不容易证明系统稳定；
- 修改代码后可能破坏已有功能；
- 答辩时缺少“我如何验证系统”的说明。

解决方案：

增加测试用例和测试 CSV。

建议准备 4 类测试数据：

1. 完整字段 CSV：所有功能都可运行；
2. 最小字段 CSV：只能运行需求预测；
3. 缺少广告字段 CSV：广告分析不可用，但其他功能可用；
4. 字段名不同 CSV：测试字段识别和映射。

每个测试用例记录：

- 输入文件；
- 预期可用功能；
- 预期不可用功能；
- 是否成功生成 CSV；
- 是否成功生成 Markdown 报告。

涉及模块：

- `tests/` 目录，如果后续创建；
- 测试 CSV 文件；
- `system_test_report.md`；
- `schema_utils.py`。

验收标准：

- 至少有 4 个测试 CSV；
- 每个核心功能至少测试一次；
- 字段缺失场景不会导致程序崩溃；
- 测试报告记录结果。

优先级：

中。

### 18.11 总体实施路线图

建议按以下顺序实施，避免一次修改过大。

第一阶段：稳定上传 CSV 和功能可用性

1. 新增 `schema_utils.py`；
2. 增加字段映射和字段标准化；
3. 增加功能可用性检查；
4. GUI 显示字段识别结果；
5. 缺字段时显示提示，不直接报错。

第二阶段：增强业务表达

1. 首页增加系统目的说明；
2. 明确单品分析和批量分析；
3. 优化 Markdown 报告；
4. 报告中写入字段识别和功能可用性。

第三阶段：优化供货计划

1. 增加库存字段；
2. 优化供货公式；
3. 支持完整逻辑和简化逻辑自动切换；
4. 增加 marketplace 级供货汇总图。

第四阶段：优化 ML 模型

1. 动态选择 ML 特征；
2. 自动生成派生特征；
3. 增加缺失值处理；
4. 输出使用特征和模型指标；
5. ML 不可运行时给出原因。

第五阶段：优化数据和测试

1. 生成更真实的模拟数据；
2. 准备多种测试 CSV；
3. 更新系统测试报告；
4. 检查中俄文本编码；
5. 完成最终演示流程。

### 18.12 最终验收标准

项目优化完成后，应满足以下标准：

1. 用户打开 GUI 后能清楚理解系统目的；
2. 用户可以选择单品分析或批量分析；
3. 用户上传字段名不同的 CSV 后，系统可以识别核心字段；
4. 系统可以判断每个功能是否可用；
5. 缺少字段时系统不崩溃，而是提示原因；
6. 需求预测、供货计划、广告分析、价格推荐和 ML 模型都能在合适数据下成功运行；
7. 供货计划能生成总 CSV 和 marketplace 独立 CSV；
8. Markdown 报告包含核心推荐结果和业务结论；
9. ML 报告包含模型指标、最佳模型和使用特征；
10. 中文和俄语界面及报告没有乱码；
11. 至少使用 4 类测试 CSV 验证系统稳定性。
