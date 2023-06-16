import os
import json
import openai
import requests
import streamlit as st

from datetime import datetime
from dotenv import load_dotenv


def get_current_time(obj):
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_weather_city(data):
    city = data.get("city", "")
    url = "https://v0.yiketianqi.com/api?unescape=1&version=v91&appid={app_id}&appsecret={secret}&city={city}".format(
        app_id=os.environ.get("WEATHER_APP_ID"),
        secret=os.environ.get("WEATHER_SECRET"),
        city=city
    )
    resp = requests.get(url)
    if resp.status_code == 200:
        result = json.loads(resp.content)
        return result.get("data", list())[0].get("wea", "Weather data not found")
    else:
        return "Weather data not found"


def get_current_address(data):
    return "星巴克（深圳宝安万庭广场店）"


def get_current_inventory(data):
    inventory_data = [
        {"product": "Sony电视机", "count": 123},
        {"product": "马自达ATZ汽车", "count": 535},
    ]

    return json.dumps(inventory_data)


def get_current_remains_room_count(data):
    return json.dumps({"count": 95})


def get_data_metadata(data):
    tag = data.get("tag")
    metadata = [{
        "region": "华南",
        "storage": "hudi",
        "db": "db_ods",
        "table": "ods_order_item",
        "subject_domains": ["电商", "订单"],
        "description": "订单明细数据",
        "fields": [
            {
                "field": "order_id",
                "description": "商品id",
                "tags": ["商品ID", "item id"],
            },
            {
                "field": "order_name",
                "description": "商品名称",
                "tags": ["商品", "产品"]
            },
            {
                "field": "order_amount",
                "description": "商品金额",
                "tags": ["金额"]
            },
            {
                "field": "order_num",
                "description": "商品购买数量",
                "tags": ["数量"]
            },
            {
                "field": "payment_time",
                "description": "支付时间",
            },
            {
                "field": "payment_sn",
                "description": "支付流水号",
                "tags": ["流水号"]
            },
            {
                "field": "payment_method",
                "description": "支付方式",
            },
            {
                "field": "order_payment_status",
                "description": "订单支付状态 ",
                "tags": ["支付状态"],
            }
        ]
    }, {
        "region": "北京",
        "storage": "hive",
        "db": "db_dwd",
        "table": "dwd_order_payment",
        "subject_domains": ["电商", "订单"],
        "description": "付款相关信息",
        "fields": [
            {
                "field": "payment_sn",
                "description": "支付流水号",
                "tags": ["流水号"]
            },
            {
                "field": "payment_time",
                "description": "支付时间",
            },
            {
                "field": "payment_method",
                "description": "支付方式",
            },
            {
                "field": "order_payment_status",
                "description": "订单支付状态",
                "tags": ["支付状态"],
            },
        ],
    }, {
        "region": "广州",
        "storage": "StarRocks",
        "db": "db_ads",
        "table": "ads_order_payment_analysis",
        "subject_domains": ["电商", "订单"],
        "description": "订单支付分析表(支付方式分布)",
        "fields": [
            {
                "field": "payment_method",
                "description": "支付方式",
            },
            {
                "field": "refund_rate",
                "description": "退款率",
            },
        ],
    }
    ]

    metadata_result = list()

    for v in metadata:
        for field in v.get('fields'):
            if tag in field.get('tags', list()) or tag == field.get('description', '') or tag == field.get('field', ''):
                metadata_result.append(v)

    return json.dumps(metadata_result)


def get_chat_completion(content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": content}],
        temperature=0,
        functions=[
            {
                "name": "get_current_time",
                "description": "get the current time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_weather_city",
                "description": "get today's city weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city",
                        }
                    },
                },
            },
            {
                "name": "get_current_address",
                "description": "get the current address",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_current_inventory",
                "description": "get the current inventory",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_data_metadata",
                "description": "get the metadata of data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tag": {
                            "type": "string",
                            "description": "The tag of metadata"
                        }
                    },
                },
            },
            {
                "name": "get_current_remains_room_count",
                "description": "get the current remains room count",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ],
        function_call="auto"
    )

    message = response["choices"][0]["message"]

    if message.get("function_call"):
        function_name = message["function_call"]["name"]
        function_args = json.loads(message["function_call"]["arguments"])

        function_response = eval(function_name)(function_args)

        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": content},
                message,
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                },
            ],
        )
        return second_response


def run_conversation(content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": content}],
        temperature=0,
    )
    return response


def main():
    load_dotenv()
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    openai.api_base = os.environ.get('OPENAI_API_BASE_URL')

    # print(get_chat_completion("what is the time?"))
    # resp = get_chat_completion("现在几点？")
    # resp = get_chat_completion("今天是什么日期？")
    # resp = get_chat_completion("今天深圳市的天气怎么样？")
    # resp = get_chat_completion("我现在在哪个位置？")
    # resp = get_chat_completion("Sony电视机还有多少库存？")
    # resp = get_chat_completion("还有多少台马自达ATZ汽车没有出销？")
    # resp = get_chat_completion('我是一名业务分析人员，我想知道在我们的大数据平台上，有关"数量"的字段存在于哪些表？')
    resp = get_chat_completion('我是一名业务分析人员，我想知道在我们的大数据平台上有关退款率的信息存在哪些表里？')
    # resp = get_chat_completion('我是一名业务分析人员，我想知道在我们的大数据平台上是否有记录金额的数据？')
    # resp = get_chat_completion('请问当前剩余的房间数有多少？')
    # resp = get_chat_completion('请问当前还剩下多少空房间？')

    # resp = run_conversation("现在几点？")
    # resp = run_conversation("今天是什么日期？")
    # resp = run_conversation("今天深圳市的天气怎么样？")
    # resp = run_conversation("我现在在哪个位置？")
    # resp = run_conversation("Sony电视机还有多少库存？")
    # resp = run_conversation('我是一名业务分析人员，我想知道有关"进入"的字段所存在的所有表是哪些？')

    if isinstance(resp, dict) and resp.get('choices', None) is not None:
        print(resp['choices'][0]["message"]["content"])
    else:
        print(resp)

    # st.title("OpenAI 之 function call 探索")
    # st.subheader("小红探索")
    # message = st.text_input("请输入你的信息")
    # if st.button("提交", type="primary"):
    #     resp = get_chat_completion(message)
    #     if isinstance(resp, dict) and resp.get('choices', None) is not None:
    #         st.success(resp['choices'][0]["message"]["content"])
    #     else:
    #         st.warning(resp)


if __name__ == '__main__':
    main()
