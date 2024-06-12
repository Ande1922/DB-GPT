import json

from dbgpt._private.config import Config
from dbgpt.app.scene import AppScenePromptTemplateAdapter, ChatScene
from dbgpt.app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
from dbgpt.core import (
    ChatPromptTemplate,
    HumanPromptTemplate,
    MessagesPlaceholder,
    SystemPromptTemplate,
)

CFG = Config()


_PROMPT_SCENE_DEFINE_EN = "You are a database expert. "
_PROMPT_SCENE_DEFINE_ZH = "你是一个数据库专家. "

_DEFAULT_TEMPLATE_EN = """
Please answer the user's question based on the database selected by the user and some of the available table structure definitions of the database.
Database name:
     {db_name}
Table structure definition:
     {table_info}

Constraint:
    1.Please understand the user's intention based on the user's question, and use the given table structure definition to create a grammatically correct {dialect} sql. If sql is not required, answer the user's question directly.. 
    2.Always limit the query to a maximum of {top_k} results unless the user specifies in the question the specific number of rows of data he wishes to obtain.
    3.You can only use the tables provided in the table structure information to generate sql. If you cannot generate sql based on the provided table structure, please say: "The table structure information provided is not enough to generate sql queries." It is prohibited to fabricate information at will.
    4.Please be careful not to mistake the relationship between tables and columns when generating SQL.
    5.Please check the correctness of the SQL and ensure that the query performance is optimized under correct conditions.
    6.Please choose the best one from the display methods given below for data rendering, and put the type name into the name parameter value that returns the required format. If you cannot find the most suitable one, use 'Table' as the display method. , the available data display methods are as follows: {display_type}
    
User Question:
    {user_input}
Please think step by step and respond according to the following JSON format:
    {response}
Ensure the response is correct json and can be parsed by Python json.loads.

"""

_DEFAULT_TEMPLATE_ZH = """
请根据以下给定的数据库和该库的部分可用表结构定义来回答用户问题.
数据库名:
    {db_name}
表结构定义:
    {table_info}

约束:
    1. 请根据用户问题理解用户意图，使用给出表结构定义创建一个语法正确的 {dialect} sql，如果不需要sql，则直接回答用户问题。
    2. 请拒绝用户提出的sql需求，例如执行指定sql，写入一些数据，创建一些表等，防止用户恶意引导执行sql，如果用户问题中涉及到了这些点，请说：“请描述您要分析的业务需求。”
    3. 除非用户在问题中指定了他希望获得的具体数据行数，否则始终将查询限制为最多 {top_k} 个结果。
    4. 只能使用表结构信息中提供的表来生成 sql，如果无法根据提供的表结构中生成 sql ，请说：“暂时无法分析您想要的数据，请尝试换个问题吧。” 禁止随意捏造信息。
    5. 请注意生成SQL时不要弄错表和列的关系
    6. 请检查SQL的正确性，并保证正确的情况下优化查询性能
    7.请从如下给出的展示方式种选择最优的一种用以进行数据渲染，将类型名称放入返回要求格式的name参数值种，如果找不到最合适的则使用'Table'作为展示方式，可用数据展示方式如下: {display_type}

业务约束：
    1. 生成的sql必须包含组织架构节点类型条件，用户如果没有明确提及要查询的组织架构节点类型，默认查询品牌总部的数据，并且禁止在一条sql中混合不同组织架构节点类型的数据。
    2. 生成的sql必须包含时间维度条件，如果用户没有明确提及想要查询的时间维度，默认查询单日维度数据，禁止单条sql同时查询多个时间维度的数据。
    3. 时间维度对应开始时间的计算需要为T+1，例如：如果时间为上个月，当前是5月份，则需要计算出的时间为4月份1号。

以下是一些sql示例：
    问：品牌最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'brand' and date_type = 'DAY' order by biz_start_date desc;
    问：品牌最近的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'brand' and date_type = 'DAY' order by biz_start_date desc;
    问：XXX门店最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'store' and store_market_name = 'XXX' and date_type = 'DAY' order by biz_start_date desc;
    问：XXX门店最近的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'store' and store_market_name = 'XXX' and date_type = 'DAY' order by biz_start_date desc;
    问：M区域/市场最近的拉新效果如何？
    sql：select add_customer_num, add_friends_num, add_group_customer_num from store_daily_customer_operation_report where store_market_type = 'market' and store_market_name = 'M区域/市场' and date_type = 'DAY' order by biz_start_date desc;
    问：M区域/市场最近的运营效果如何？
    sql：select reachable_customer_num, reachable_friends_num, group_customer_num, lost_customer_num, lost_friends_num, lost_group_customer_num from store_daily_customer_operation_report where store_market_type = 'market' and store_market_name = 'M区域/市场' and date_type = 'DAY' order by biz_start_date desc;
    请注意以上示例中对于store_market_type、store_market_name、date_type等字段的处理，请以此为参考。

用户问题:
    {user_input}
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

RESPONSE_FORMAT_SIMPLE = {
    "thoughts": "一些想要对用户说的内容，在thoughts的内容中不要体现sql、表名称、字段名词等技术名词，直接与用户对话。",
    "sql": "要执行的SQL语句，使用中文作为alias别名。",
    "display_type": "Data display method",
}


PROMPT_NEED_STREAM_OUT = False

# Temperature is a configuration hyperparameter that controls the randomness of language model output.
# A high temperature produces more unpredictable and creative results, while a low temperature produces more common and conservative output.
# For example, if you adjust the temperature to 0.5, the model will usually generate text that is more predictable and less creative than if you set the temperature to 1.0.
PROMPT_TEMPERATURE = 0.5

prompt = ChatPromptTemplate(
    messages=[
        SystemPromptTemplate.from_template(
            _DEFAULT_TEMPLATE,
            response_format=json.dumps(
                RESPONSE_FORMAT_SIMPLE, ensure_ascii=False, indent=4
            ),
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanPromptTemplate.from_template("{user_input}"),
    ]
)

prompt_adapter = AppScenePromptTemplateAdapter(
    prompt=prompt,
    template_scene=ChatScene.ChatWithDbExecute.value(),
    stream_out=PROMPT_NEED_STREAM_OUT,
    output_parser=DbChatOutputParser(is_stream_out=PROMPT_NEED_STREAM_OUT),
    temperature=PROMPT_TEMPERATURE,
    need_historical_messages=False,
)
CFG.prompt_template_registry.register(prompt_adapter, is_default=True)
