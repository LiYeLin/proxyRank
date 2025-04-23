# llm_interface.py
import json
import logging
import os
from http import HTTPStatus  # Import HTTPStatus for checking response codes
from typing import List, Dict, Any

# 导入 DashScope SDK
import dashscope
from openai import OpenAI

logger = logging.getLogger(__name__)
# 从 config 导入所有需要的配置
from config import (
    DASHSCOPE_API_KEY,
    BAILIAN_MODEL_ID,
    BAILIAN_VL_MODEL_ID,  # Import VL Model ID
    LLM_EXTRACTION_PROMPT,
    LLM_IMAGE_EXTRACTION_PROMPT  # Import Image Prompt
)

logger = logging.getLogger(__name__)

# Flag to track configuration status
IS_LLM_CONFIGURED = False
IS_VL_MODEL_CONFIGURED = False
client = None


# 在模块加载时配置 DashScope API Key

def configure_llm_vl_models():
    """配置 DashScope API Key 并检查模型 ID"""
    global IS_LLM_CONFIGURED, IS_VL_MODEL_CONFIGURED
    api_key = DASHSCOPE_API_KEY
    if not api_key:
        logger.warning("DashScope API Key (DASHSCOPE_API_KEY) 未配置，LLM/VL 功能将无法使用。")
        IS_LLM_CONFIGURED = False
        IS_VL_MODEL_CONFIGURED = False
        return

    # 设置 API Key
    dashscope.api_key = api_key
    logger.info("DashScope API Key 已配置。")

    # 检查文本模型 ID
    if not BAILIAN_MODEL_ID:
        logger.error(f"Bailian 文本模型 ID (BAILIAN_MODEL_ID) 未配置或无效: '{BAILIAN_MODEL_ID}'")
        IS_LLM_CONFIGURED = False
    else:
        logger.info(f"将使用 Bailian 文本模型: {BAILIAN_MODEL_ID}")
        IS_LLM_CONFIGURED = True

    # 检查多模态模型 ID
    if not BAILIAN_VL_MODEL_ID:
        logger.error(f"Bailian 多模态模型 ID (BAILIAN_VL_MODEL_ID) 未配置或无效: '{BAILIAN_VL_MODEL_ID}'")
        IS_VL_MODEL_CONFIGURED = False
    else:
        logger.info(f"将使用 Bailian 多模态模型: {BAILIAN_VL_MODEL_ID}")
        IS_VL_MODEL_CONFIGURED = True  # Mark VL as configured if ID is present
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


# 执行配置
configure_llm_vl_models()


def extract_info_llm(article_text: str) -> dict | None:
    """
    使用配置好的阿里云百炼/DashScope模型从文章文本中提取结构化信息。
    返回一个包含提取信息的字典，格式见 config.py 中的 LLM_EXTRACTION_PROMPT。
    """
    if not IS_LLM_CONFIGURED:
        logger.warning("LLM 未正确配置，无法提取信息。")
        return None

    # 确保模型 ID 已加载
    if not BAILIAN_MODEL_ID:
        logger.error("BAILIAN_MODEL_ID 配置丢失，无法调用模型。")
        return None

    full_prompt = LLM_EXTRACTION_PROMPT.format(article_text=article_text)

    try:
        logger.info(f"正在调用 DashScope API (模型: {BAILIAN_MODEL_ID})...")
        # 使用 Generation.call 调用模型
        response = dashscope.Generation.call(
            model=BAILIAN_MODEL_ID,
            prompt=full_prompt,
            result_format='text'  # 请求纯文本输出，便于 JSON 解析
            # 可以根据需要添加其他参数，如 temperature, top_p 等
            # temperature=0.8
        )

        # 检查 API 调用状态
        if response.status_code == HTTPStatus.OK:
            logger.debug(f"DashScope API 原始响应: {response}")
            extracted_text = response.output['text']

            # 清理和解析 LLM 返回的 JSON
            if not extracted_text:
                logger.warning("LLM 返回了空内容。")
                return None

            # 移除可能的 Markdown 代码块标记
            if extracted_text.strip().startswith("```json"):
                extracted_text = extracted_text.strip()[7:-3].strip()
            elif extracted_text.strip().startswith("```"):
                extracted_text = extracted_text.strip()[3:-3].strip()

            logger.debug(f"清理后的 LLM 响应文本: {extracted_text}")

            try:
                extracted_data = json.loads(extracted_text)
                logger.info("LLM 提取信息并成功解析 JSON。")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"解析 LLM 返回的 JSON 时出错: {e}. 原始文本: '{extracted_text}'", exc_info=True)
                return None

        else:
            # 处理 API 调用错误
            logger.error(f"DashScope API 调用失败: Code={response.code}, Message={response.message}")
            return None

    except Exception as e:
        # 处理 SDK 或网络等其他异常
        logger.error(f"调用 DashScope API 时发生未知错误: {e}", exc_info=True)
        return None


import re


def extract_json_content(text):
    pattern = r'```json(.*?)```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None


# --- 新增函数：使用 VL 模型处理图片 ---
def extract_info_from_image_llm(img_path: str) -> List[Dict[str, Any]] | None:
    """
    使用配置好的阿里云百炼/DashScope多模态模型从图片中提取表格信息。
    返回一个包含提取信息的字典列表，格式基于 LLM_IMAGE_EXTRACTION_PROMPT。
    """
    if not IS_VL_MODEL_CONFIGURED:  # Check specific flag for VL model
        logger.warning("多模态 LLM 未正确配置，无法从图片提取信息。")
        return None
    if not BAILIAN_VL_MODEL_ID:
        logger.error("BAILIAN_VL_MODEL_ID 配置丢失，无法调用多模态模型。")
        return None

    try:
        image_path = f"file://{img_path}"

        logger.info(f"正在调用 DashScope API (多模态模型: {BAILIAN_VL_MODEL_ID})...")
        prompt_ = [
            {
                "role": "user",
                "content": [
                    {
                        "image": image_path,
                    },
                    {"text": LLM_IMAGE_EXTRACTION_PROMPT},
                ],
            }
        ]
        response = dashscope.MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model=BAILIAN_VL_MODEL_ID,
            messages=prompt_,
            vl_high_resolution_images=True,
            result_format='message',
            response_format={'type': 'json_object'}
        )

        print("大模型的回复:\n ", response.output.choices[0].message.content[0]["text"])
        print("Token用量情况：", "输入总Token：", response.usage["input_tokens"], "，输入图像Token：",
              response.usage["image_tokens"])

    except Exception as e:
        # 处理 SDK、Base64 编码或网络等其他异常
        logger.error(f"调用 DashScope 多模态 API 时发生未知错误: {e}", exc_info=True)
        return None


# --- 示例用法 ---
if __name__ == '__main__':
    # 确保你的 API Key 和 Model ID 在 config.py 或 .env 中已正确配置
    if not IS_LLM_CONFIGURED:
        print("LLM 未配置，请检查 config.py 或 .env 文件中的 DASHSCOPE_API_KEY 和 BAILIAN_MODEL_ID。")
    # sample_text = """
    # 本次带来的是 ABC 服务商的最新情况。
    # 官网地址：https://abc-service.com。
    # 他们最近上线了新的套餐：入门版，每月仅需 15 元；专业版，年付 180 元，流量更多。
    # 节点方面，香港 HKT、日本 IIJ 和新加坡线路表现不错。美国 GIA 稍有延迟。
    # 总体来说值得推荐。
    # """
    # print(f"使用的模型: {BAILIAN_MODEL_ID}")
    # info = extract_info_llm(sample_text)
    # if info:
    #     print("\nLLM 提取结果:")
    #     print(json.dumps(info, indent=2, ensure_ascii=False))
    # else:
    #     print("\nLLM 提取失败。")
    #
    # print("\n测试一个可能不包含单一机场信息的文本：")
    # sample_text_general = """
    # 最近市场上出现了很多新的网络服务，选择时需要注意稳定性。香港和日本节点通常延迟较低。价格方面差异很大。
    # """
    # info_general = extract_info_llm(sample_text_general)
    # if info_general:
    #      print("\nLLM 提取结果 (通用文本):")
    #      print(json.dumps(info_general, indent=2, ensure_ascii=False))
    # else:
    #      print("\nLLM 提取失败 (通用文本)。")

    # --- 测试图片提取 ---
    print("\n--- 测试图片提取 ---")
    if not IS_VL_MODEL_CONFIGURED:
        print("多模态 LLM 未配置。")
    else:
        # 需要一个真实的本地图片文件用于测试
        # !! 修改为你本地的测速图片路径 !!
        image_path_vl = '/Users/liyelin/PycharmProjects/proxyRank/downloaded_images/d0254ec646b6fa3c2a7f0ae4a75caa0492da3a55.png'  # 假设你有一个示例图片
        try:

            print(f"\n开始使用多模态模型 ({BAILIAN_VL_MODEL_ID}) 处理图片...")
            image_data = extract_info_from_image_llm(image_path_vl)

            if image_data:
                print("\nLLM 图片提取结果:")
                print(json.dumps(image_data, indent=2, ensure_ascii=False))
                print(f"\n成功提取 {len(image_data)} 条记录。")
            else:
                print("\nLLM 图片提取失败或未提取到有效记录。")

        except FileNotFoundError:
            print(f"\n错误：测试图片文件未找到: {image_path_vl}")
        except Exception as e:
            print(f"\n测试图片提取时发生意外错误: {e}")
            import traceback

            traceback.print_exc()
