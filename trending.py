import requests
import json
from datetime import datetime

# ========== 配置区（这里改你的推送webhook）==========
WEBHOOK_URL = ""  # 企业微信/钉钉/飞书webhook地址
PUSH_CHANNEL = "wecom"  # wecom / dingtalk / feishu
TOP_NUM = 5
# 可选：接入大模型生成项目中文简介（DeepSeek/豆包API）
LLM_API_KEY = ""
LLM_BASE_URL = "https://api.deepseek.com/v1"
# =================================================

def get_github_trending(top=5):
    # 免费公共trending接口，返回每日热榜
    resp = requests.get("https://gitstock.org/api/v1/github?period=daily", timeout=20)
    data = resp.json()
    return data[:top]

def ai_summary(repo):
    if not LLM_API_KEY:
        return repo["description"]
    prompt = f"""
给这个GitHub开源项目写简短中文介绍，一句话讲清楚用途：
项目名：{repo['repo']}
描述：{repo['description']}
链接：{repo['url']}
"""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role":"user","content":prompt}],
        "temperature":0.3
    }
    headers = {"Authorization":f"Bearer {LLM_API_KEY}", "Content-Type":"application/json"}
    res = requests.post(f"{LLM_BASE_URL}/chat/completions", json=payload, headers=headers, timeout=30)
    return res.json()["choices"][0]["message"]["content"]

def build_msg(repo_list):
    today = datetime.now().strftime("%Y-%m-%d")
    msg = f"📌 GitHub开源热榜 TOP{TOP_NUM}｜{today}\n"
    for idx, repo in enumerate(repo_list, start=1):
        summary = ai_summary(repo)
        msg += f"\n#{idx} **{repo['repo']}** ⭐{repo['stars']}\n{summary}\n🔗 {repo['url']}"
    return msg

def send_msg(content):
    if PUSH_CHANNEL == "wecom":
        body = {"msgtype":"text", "text":{"content":content}}
    elif PUSH_CHANNEL == "dingtalk":
        body = {"msgtype":"text", "text":{"content":content}}
    elif PUSH_CHANNEL == "feishu":
        body = {"msgtype":"text", "text":{"content":{"text":content}}}
    requests.post(WEBHOOK_URL, json=body, timeout=15)

if __name__ == "__main__":
    repos = get_github_trending(TOP_NUM)
    text = build_msg(repos)
    send_msg(text)
    print("✅ 推送完成")
