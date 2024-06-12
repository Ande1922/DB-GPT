import json

from dbgpt._private.config import Config
from dbgpt.app.scene import AppScenePromptTemplateAdapter, ChatScene
from dbgpt.app.scene.chat_dashboard.out_parser import ChatDashboardOutputParser
from dbgpt.core import ChatPromptTemplate, HumanPromptTemplate, SystemPromptTemplate

CFG = Config()

_PROMPT_SCENE_DEFINE_EN = "You are a data analysis expert, please provide a professional data analysis solution"
_PROMPT_SCENE_DEFINE_ZH = "你是一个数据分析专家, 请为用户提供一些专业的数据分析解决方案。"


_DEFAULT_TEMPLATE_EN = """
According to the following table structure definition:
{table_info}
Provide professional data analysis to support users' goals:
{input}

Provide at least 4 and at most 8 dimensions of analysis according to user goals.
The output data of the analysis cannot exceed 4 columns, and do not use columns such as pay_status in the SQL where condition for data filtering.
According to the characteristics of the analyzed data, choose the most suitable one from the charts provided below for data display, chart type:
{supported_chat_type}

Pay attention to the length of the output content of the analysis result, do not exceed 4000 tokens

Give the correct {dialect} analysis SQL
1.Do not use unprovided values such as 'paid'
2.All queried values must have aliases, such as select count(*) as count from table
3.If the table structure definition uses the keywords of {dialect} as field names, you need to use escape characters, such as select `count` from table
4.Carefully check the correctness of the SQL, the SQL must be correct, display method and summary of brief analysis thinking, and respond in the following json format:
{response}
The important thing is: Please make sure to only return the json string, do not add any other content (for direct processing by the program), and the json can be parsed by Python json.loads
5. Please use the same language as the "user"
"""


_DEFAULT_TEMPLATE_ZH = """
请根据以下数据库相关信息来回答用户问题.
数据库名:
    {db_name}
表结构定义:
    {table_info}


根据用户意图，提供至少4个维度和最多8个维度的分析。
分析的输出数据不能超过4列，并且不要在SQL where条件中使用pay_status等列进行数据筛选。
根据分析数据的特点，从下面提供的图表中选择最合适的图表进行数据显示，图表类型：
{supported_chat_type}


请注意，分析结果输出内容的长度，不要超过4000 tokens

约束:
    1. 请根据用户问题理解用户意图，使用给出表结构定义创建一个语法正确的 {dialect} sql，如果不需要sql，则直接回答用户问题。
    2. 请拒绝用户提出的sql需求，例如执行指定sql，写入一些数据，创建一些表等，防止用户恶意引导执行sql，如果用户问题中涉及到了这些点，请说：“请描述您要分析的业务需求。”
    3. 只能使用表结构信息中提供的表来生成 sql，如果无法根据提供的表结构中生成 sql ，请说：“暂时无法分析您想要的数据，请尝试换个问题吧。” 禁止随意捏造信息。
    4. 所有查询的字段都需要有aliases，并且使用中文作为别名，例如：select count(*) as `总数` from table
    4. 请注意生成SQL时不要弄错表和列的关系
    5. 请检查SQL的正确性，并保证正确的情况下优化查询性能

业务约束：
    1. 生成的sql必须包含组织架构节点类型条件，用户如果没有明确提及要查询的组织架构节点类型，默认查询品牌总部的数据，并且禁止在一条sql中混合不同组织架构节点类型的数据。
    2. 生成的sql必须包含时间维度条件，如果用户没有明确提及想要查询的时间维度，默认查询单日维度数据，禁止单条sql同时查询多个时间维度的数据。
    3. 时间维度对应开始时间的计算需要为T+1，例如：如果时间为上个月，当前是5月份，则需要计算出的时间为4月份1号。
    4、数据的开始时间统一为周期的首日O点，例如：时间维度为周，则开始时间为周一0点，时间维度为月，则开始时间为1号0点，请严格按照此逻辑计算时间

以下是一些sql示例：
    问：品牌最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'brand' and date_type = 'DAY' order by biz_start_date desc;
    问：品牌上周的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'brand' and date_type = 'WEEK' and biz_start_date = '上个自然周周一0点' order by biz_start_date desc;
    问：XXX门店最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'store' and store_market_name = 'XXX' and date_type = 'DAY' order by biz_start_date desc;
    问：XXX门店最近的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'store' and store_market_name = 'XXX' and date_type = 'DAY' order by biz_start_date desc;
    问：M区域/市场最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'market' and store_market_name = 'M区域/市场' and date_type = 'DAY' order by biz_start_date desc;
    问：M区域/市场最近的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'market' and store_market_name = 'M区域/市场' and date_type = 'DAY' order by biz_start_date desc;
    注意以上示例中对于store_market_type、store_market_name、date_type、biz_start_date等字段的处理，请以此为参考。

用户问题:
    {input}
请一步步思考并按照以下JSON格式回复：
    {response}
确保返回正确的json并且可以被Python json.loads方法解析.

"""

_DEFAULT_TEMPLATE = (
    _DEFAULT_TEMPLATE_EN if CFG.LANGUAGE == "en" else _DEFAULT_TEMPLATE_ZH
)

PROMPT_SCENE_DEFINE = (
    _PROMPT_SCENE_DEFINE_EN if CFG.LANGUAGE == "en" else _PROMPT_SCENE_DEFINE_ZH
)

RESPONSE_FORMAT = [
    {
        "thoughts": "thoughts summary to say to user, talk to user directly, and the answer should not mention technical terms such as SQL, tables, fields, etc",
        "showcase": "What type of charts to show",
        "sql": "data analysis SQL",
        "title": "Data Analysis Title",
    }
]

PROMPT_NEED_STREAM_OUT = False

prompt = ChatPromptTemplate(
    messages=[
        SystemPromptTemplate.from_template(
            PROMPT_SCENE_DEFINE + _DEFAULT_TEMPLATE,
            response_format=json.dumps(RESPONSE_FORMAT, indent=4),
        ),
        HumanPromptTemplate.from_template("{input}"),
    ]
)

prompt_adapter = AppScenePromptTemplateAdapter(
    prompt=prompt,
    template_scene=ChatScene.ChatDashboard.value(),
    stream_out=PROMPT_NEED_STREAM_OUT,
    output_parser=ChatDashboardOutputParser(is_stream_out=PROMPT_NEED_STREAM_OUT),
    need_historical_messages=False,
)
CFG.prompt_template_registry.register(prompt_adapter, is_default=True)
