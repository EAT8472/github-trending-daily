import requests
import json
from datetime import datetime

# ========== 配置区（这里改你的推送webhook）==========
WEBHOOK_URL = ""
PUSH_CHANNEL = "wecom"  # wecom / dingtalk / feishu
TOP_NUM = 5
# 可选：接入大模型生成中文摘要，不用可以留空
LLM_API_KEY = ""
LLM_BASE_URL = "https://api.deepseek.com/v1"
# =================================================

def get_github_trending(top=5):
    # 替换成稳定接口
    resp = requests.get("https://api.trending-github.com/github/repositories?since=daily", timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return data[:top]

def ai_summary(repo):
    if not LLM_API_KEY:
        return repo.get("description", "暂无描述")
    prompt = f"""
给这个GitHub开源项目写简短中文介绍，一句话讲清楚用途：
项目名：{repo['name']}
描述：{repo.get('description','')}
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
        star = repo.get("stars", 0)
        msg += f"\n#{idx} **{repo['name']}** ⭐{star}\n{summary}\n🔗 {repo['url']}"
    return msg

def send_msg(content):
    if PUSH_CHANNEL == "wecom":
        body = {"msgtype":"text", "text":{"content":content}}
    elif PUSH_CHANNEL == "dingtalk":
        body = {"msgtype":"text", "text":{"content":{"text":content}}}
    elif PUSH_CHANNEL == "feishu":
        body = {"msgtype":"text", "text":{"content":{"text":content}}}
    requests.post(WEBHOOK_URL, json=body, timeout=15)

if __name__ == "__main__":
    repos = get_github_trending(TOP_NUM)
    text = build_msg(repos)
    send_msg(text)
    print("✅ 推送完成")
