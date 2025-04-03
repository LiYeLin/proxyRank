import json
import os
from openai import OpenAI, OpenAIError

def do_query_llm(html_content):
    """
    提取 HTML 内容中的主要信息并返回 JSON 数组。
    
    参数:
        html_content (str): 需要提取信息的 HTML 内容。
    
    返回:
        str: 包含提取信息的 JSON 数组字符串。
    """
    if not html_content:
        return []
    try:
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"), 
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
         # 构建完善的 prompt
        prompt = f"""
            请从以下 HTML 中提取文字主要信息（不包含图片以及图片的介绍），以 JSON 数组返回。
            要求返回的 JSON 数组包含以下字段：
            [
                {{
                    "name": "机场名称",
                    "subscription_plan": "订阅套餐详情",
                    "website": "官网链接",
                    "context": "上下文描述"
                }}
            ]

            示例：
            输入：
            <p>为了方便让用户观察一家机场近几月的状态，所以弄一个分帖，然后把部分机场的近几个月的多张测速图挂出来，只弄部分。<br>更多机场介绍请看主贴 <strong><a href="https://www.duyaoss.com/archives/3/">DuyaoSS - 机场测速和简介</a></strong></p><hr><h2 id="toc_0">31.Miru（中转机场）</h2><p>最近发现的一家中转机场，主要是移动和 CN2 中继，比较便宜。</p><p><strong>稳定性还可以。</strong></p><p><strong>套餐情况：</strong></p><blockquote><ul><li><strong>轻量套餐：7元/月，50G流量；21元/季，150G流量；70元/年，600G流量；限制2个客户端；</strong></li><li><strong>标准套餐：17元/月，150G流量；51元/季，450G流量；170元/年，1800G流量；限制3个客户端；</strong></li><li><strong>旗舰套餐：27元/月，500G流量；81元/季，1500G流量；270元/年，6000G流量；限制5个客户端。</strong></li></ul></blockquote><p><strong>其他情况：</strong></p><blockquote><ul><li>支持SSR</li><li>支付方式：支付宝+银联</li></ul></blockquote><p><strong>官网：<a href="https://bit.ly/3tukuIT" target="_blank">https://bit.ly/3tukuIT</a></strong></p><hr><p><br><br><br></p><h2 id="toc_1">落地入口分析</h2
            输出：
            ```json
            [
                {{
                    "name": "Miru（中转机场）",
                    "subscription_plan": "轻量套餐：7元/月...",
                    "website": "https://bit.ly/3tukuIT",
                    "context": "为了方便让用户观察..."
                }}
            ]```
            输入：
            {html_content}"""
        # 调用模型进行内容提取
        completion = client.chat.completions.create(
            model="qwen2.5-1.5b-instruct",  
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt},  # 动态传入 HTML 内容
            ],
        )
        
        # 检查返回结果是否有效
        if not completion or not completion.choices:
            return []
        
        # 提取返回的主要内容
        extracted_content = completion.choices[0].message.content
        
        # 确保返回的是 JSON 数组格式
        try:
            json_content = json.loads(extracted_content)
            if isinstance(json_content, list):
                return extracted_content
            else:
                return []
        except json.JSONDecodeError:
            return []
    
    except OpenAIError as e:
        # 捕获 OpenAI 相关异常
        print(f"OpenAI API 调用失败: {e}")
        return []
    except Exception as e:
        # 捕获其他异常
        print(f"发生未知错误: {e}")
        return []

    