"""E-com Prophet configuration: UI text, data paths, and model constants."""

DATA_PATH = "transactions_optimized.csv"

MARKETPLACE_FILES = {
    "WildBerries": "supply_plan_wildberries.csv",
    "OZON": "supply_plan_ozon.csv",
    "YandexMarket": "supply_plan_yandex_market.csv",
}

TEXT = {
    "ru": {
        "title": "E-com Prophet",
        "subtitle": "Система прогнозирования спроса, планирования поставок и анализа юнит-экономики",
        "language": "Язык",
        "data": "Данные",
        "default_data": "Использовать transactions_optimized.csv",
        "upload_data": "Загрузить CSV",
        "function": "Функция системы",
        "forecast": "Прогнозирование спроса",
        "supply": "Планирование поставок",
        "promo": "Анализ рекламы и промо",
        "price": "Рекомендация цены",
        "marketplace": "Маркетплейс",
        "category": "Категория",
        "sku": "Товар",
        "all": "Все",
        "mode": "Режим анализа",
        "mode_all": "Все товары",
        "mode_one": "Один товар",
        "period": "Период прогноза",
        "target_margin": "Целевая маржа, %",
        "supply_min_margin": "Минимальная маржа для поставки, %",
        "supply_min_margin_note": (
            "Товары с маржей ниже этого значения останутся в таблице, "
            "но не получат рекомендацию на поставку."
        ),
        "run": "Запустить анализ",
        "rows": "Строк",
        "revenue": "Выручка",
        "profit": "Прибыль",
        "margin": "Средняя маржа",
        "download_csv": "Скачать CSV",
        "download_md": "Скачать Markdown-отчет",
        "forecast_result": "Результат прогноза спроса",
        "supply_result": "План поставок",
        "promo_result": "Анализ рекламы и промо",
        "price_result": "Рекомендации по ценам",
        "dashboard": "Обзор данных",
        "horizon_label": "Горизонт прогноза",
        "days_unit": "дн.",
        "daily_chart_title": "Упрощенное распределение прогноза по дням",
        "daily_chart_caption": (
            "Иллюстрация: суммарный прогноз делится поровну по каждому дню горизонта. "
            "Это не дневной прогноз из временного ряда."
        ),
        "supply_top_title": "Топ товаров к поставке",
        "supply_top_caption": (
            "Показаны товары с наибольшим recommended_supply_quantity. "
            "Цвет показывает приоритет поставки."
        ),
        "supply_no_recommendations": "При текущем пороге маржи нет товаров, рекомендованных к поставке.",
        "supply_single_recommended": "Рекомендуется поставка",
        "supply_single_not_recommended": "Поставка не рекомендуется при текущем пороге маржи",
        "supply_single_marketplace_breakdown": "Рекомендации по маркетплейсам",
        "system_description_title": "Описание системы",
        "schema_panel_title": "Распознавание полей CSV",
        "schema_empty_warning": "В этом CSV не удалось автоматически распознать известные бизнес-поля.",
        "derived_columns": "Автоматически рассчитанные поля: ",
        "unmapped_columns": "Нераспознанные поля: ",
        "function_availability": "Доступность функций",
        "upload_label": "Загрузите CSV-файл",
        "upload_help": "Выберите CSV-файл с продажами, товарами, ценами и расходами.",
        "upload_missing": "Файл пока не выбран. Система временно показывает демонстрационные данные.",
        "batch_mode_caption": "Пакетный режим: система проанализирует все товары, которые подходят под выбранные фильтры.",
        "feature_unavailable": "Выбранная функция недоступна для этого CSV. Причина: {reason}",
        "filtered_rows": "Строк после фильтров",
        "filtered_preview": "Предпросмотр строк после фильтров",
        "empty_selection": "Анализ нельзя запустить, потому что выбранная выборка пуста.",
        "analysis_stopped": "Анализ остановлен: выбранная функция недоступна для этого CSV.",
        "all_marketplaces": "Все маркетплейсы",
        "marketplace_csv_files": "CSV-файлы по маркетплейсам:",
    },
    "zh": {
        "title": "E-com Prophet",
        "subtitle": "电商需求预测、供货计划与单元经济分析系统",
        "language": "语言",
        "data": "数据",
        "default_data": "使用 transactions_optimized.csv",
        "upload_data": "上传 CSV",
        "function": "系统功能",
        "forecast": "需求预测",
        "supply": "供货计划",
        "promo": "广告与促销分析",
        "price": "价格推荐",
        "marketplace": "平台",
        "category": "类别",
        "sku": "商品",
        "all": "全部",
        "mode": "分析模式",
        "mode_all": "全部商品",
        "mode_one": "单个商品",
        "period": "预测周期",
        "target_margin": "目标利润率，%",
        "supply_min_margin": "补货最低利润率，%",
        "supply_min_margin_note": "低于该利润率的商品仍会显示在结果表中，但不会推荐补货。",
        "run": "运行分析",
        "rows": "行数",
        "revenue": "销售额",
        "profit": "利润",
        "margin": "平均利润率",
        "download_csv": "下载 CSV",
        "download_md": "下载 Markdown 报告",
        "forecast_result": "需求预测结果",
        "supply_result": "供货计划",
        "promo_result": "广告与促销分析",
        "price_result": "价格推荐",
        "dashboard": "数据概览",
        "horizon_label": "预测周期",
        "days_unit": "天",
        "daily_chart_title": "按日均匀拆分的简化预测曲线",
        "daily_chart_caption": "说明：将总预测量按天平均拆分，用于演示周期，不是时间序列日预测。",
        "supply_top_title": "建议补货商品 Top",
        "supply_top_caption": "展示建议补货量最高的商品，颜色表示补货优先级。",
        "supply_no_recommendations": "当前利润率阈值下，没有商品被推荐补货。",
        "supply_single_recommended": "建议补货",
        "supply_single_not_recommended": "当前利润率阈值下不建议补货",
        "supply_single_marketplace_breakdown": "按平台补货建议",
        "system_description_title": "系统说明",
        "schema_panel_title": "CSV 字段识别",
        "schema_empty_warning": "当前 CSV 未能自动识别已知业务字段。",
        "derived_columns": "自动计算字段：",
        "unmapped_columns": "未识别字段：",
        "function_availability": "功能可用性",
        "upload_label": "上传 CSV 文件",
        "upload_help": "请选择包含销售、商品、价格和费用的 CSV 文件。",
        "upload_missing": "尚未选择文件。系统暂时显示演示数据。",
        "batch_mode_caption": "批量模式：系统会分析符合筛选条件的全部商品。",
        "feature_unavailable": "当前 CSV 无法使用所选功能。原因：{reason}",
        "filtered_rows": "筛选后可用行数",
        "filtered_preview": "筛选后数据预览",
        "empty_selection": "当前筛选结果为空，无法运行分析。",
        "analysis_stopped": "分析已停止：当前 CSV 无法使用所选功能。",
        "all_marketplaces": "全部平台",
        "marketplace_csv_files": "按平台下载 CSV：",
    },
}

TEXT["ru"].update(
    {
        "api_sync_data": "\u0421\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u044f \u0447\u0435\u0440\u0435\u0437 API (\u043f\u043e\u043a\u0430 \u043d\u0435 \u043f\u043e\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044f)",
        "api_sync_unavailable": (
            "\u042d\u0442\u043e\u0442 \u0432\u0445\u043e\u0434 \u0437\u0430\u0440\u0435\u0437\u0435\u0440\u0432\u0438\u0440\u043e\u0432\u0430\u043d \u0434\u043b\u044f \u0431\u0443\u0434\u0443\u0449\u0435\u0439 \u0441\u0438\u043d\u0445\u0440\u043e\u043d\u0438\u0437\u0430\u0446\u0438\u0438 \u0447\u0435\u0440\u0435\u0437 API-token Ozon / Wildberries / Yandex Market."
        ),
    }
)
TEXT["zh"].update(
    {
        "api_sync_data": "\u5b98\u65b9 API \u81ea\u52a8\u540c\u6b65\uff08\u6682\u4e0d\u652f\u6301\uff09",
        "api_sync_unavailable": (
            "\u8be5\u5165\u53e3\u9884\u7559\u7ed9\u540e\u7eed Ozon / Wildberries / Yandex Market API token \u540c\u6b65\u529f\u80fd\u3002"
        ),
    }
)
