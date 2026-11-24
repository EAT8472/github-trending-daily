import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET

# ========== 配置区 ==========
WEBHOOK_URL = ""
PUSH_CHANNEL = "wecom"  # wecom / dingtalk / feishu
TOP_NUM = 5
# 可选：LLM摘要，不用就留空
LLM_API_KEY = ""
LLM_BASE_URL = "https://api.deepseek.com/v1"
# ============================

def get_github_trending_rss(top=5):
    # GitHub官方Trending RSS，英文每日热榜
    url = "https://github.com/trending?since=daily&rss=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=20)
    root = ET.fromstring(resp.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall("atom:entry", ns)
    repo_list = []
    for item in items[:top]:
        title = item.find("atom:title", ns).text
        link = item.find("atom:link", ns).attrib["href"]
        desc = item.find("atom:summary", ns).text
        repo_list.append({
            "name": title,
            "url": link,
            "description": desc
        })
    return repo_list

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
        msg += f"\n#{idx} **{repo['name']}**\n{summary}\n🔗 {repo['url']}"
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
    try:
        repos = get_github_trending_rss(TOP_NUM)
        text = build_msg(repos)
        send_msg(text)
        print("✅ 推送完成")
    except Exception as e:
        print(f"❌ 脚本异常：{str(e)}")
