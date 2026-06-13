#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import logging
import sys
from typing import Set, Dict, Any, List, Tuple

# ==================== 配置区域 ====================
# 从浏览器复制的完整 Cookie 字符串（必须，包含 xq_a_token, u, s 等）
RAW_COOKIE = "smidV2=20250518172827a643dd2c05697cccdd1e2bd90195806400936a86a229c2fd0; cookiesu=601773833007334; device_id=e1bc45f84289fa5691682bd6ed65ce53; s=bh13ab6fjk; xq_is_login=1; u=4968062224; bid=115c43fabd8716312556b3b239267df3_molof2jz; xq_a_token=7bd5e9c0d56ed419dc8f1f9238ccf058e2b073fb; xqat=7bd5e9c0d56ed419dc8f1f9238ccf058e2b073fb; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOjQ5NjgwNjIyMjQsImlzcyI6InVjIiwiZXhwIjoxNzgzOTUwNzgyLCJjdG0iOjE3ODEzNTg3ODIwNDIsImNpZCI6ImQ5ZDBuNEFadXAifQ.Zsmz_gdoJCN4543nkeb_2YZX0DBqnSTz_bv-ST-2vs-gam-Dp0N9Dj9npoShtl1Yn2VinD3qSAIpXZ6fc2zbtVJnLy5NStKyILvkpt10vSErBo9ZKyvzZwZ4Z88mWzOi10wswThMXwqW1WzZeCBqCaXFFVqdoxL39Ogn974RUOgXR5WFtLvbl0itsk7vmCz7WPuJaga9NIIxZ4nTyjm7w4ByXmNmvehCGzkINm3sDMvWxQl3mGKqznBAm2aeR9cJZLmABIJ5-mxGIrICOxhoqXQj1HlXeunuDsoUztDl97SDYsLtoCJAW6jsuHJZDbIFPsev4fMjFi6qP9Xt8L1Utg; xq_r_token=3e96f798d06c35055852dde2f7bfa94282512025; acw_tc=276082bd17813609378814786e479bd8fd0e37e44e8c43b6cfe552e8855dc2; is_overseas=0; .thumbcache_f24b8bbe5a5934237bbc0eda20c1b6e7=Abz2ktsG3eUgDi8uJJS5KX62Fao5O1kcxaN2I7bqh3zrX7hNLU+Nmuh880PPr0qiwzjdUAPPzo0RLHXjhVwqTw%3D%3D; ssxmod_itna=1-eqRxciqQw4yAD8DhaDprkbGObG=1DXDUL4iQGgDYq7=GFDmx0PpBxDCbx58jHSKQDeb5kGzri5D/D44GzDiLPGhDBeAFijxDK118A=70pX8mi5hH8Hf1MbnfTiYE8cPbXU6ZS8hisUtiDB3DbqDyWBP1beGGA4GwDGoD34DiDDPfD03Db4D_9CrD7hb=ZeW31j4DQ4GyDitDKL43xi3DA4DjAjXXUWdD0Tdhc_QkSDGWAjux1647xGtPSCGxAeDMtxGXQYk6AeDBnIk6K6TEE/BmCmaFxBQD7k9=de97UjnNHl7iiQoexhdXAYK7o3BKeAN3Aqi0Y=BPz2Dj2DKi53ex8x=YDGD_dCxDiOmx7eDxhxe_cgUBrEgaNiWmHi0Y7qVpmtYviBG54K_WKD6wzAiGCqklPiGD4ji58GePim7mHBXX7DYiD6B0KjewRriGmFYRt3D; ssxmod_itna2=1-eqRxciqQw4yAD8DhaDprkbGObG=1DXDUL4iQGgDYq7=GFDmx0PpBxDCbx58jHSKQDeb5kGzrDeDADcDbq1K/D7P4=m9jxD/QDDKEq3lP79H3mtm3yjIxdc29XXbTFfCGeR98GWX3zOdXZlfLDgw3Y3jN6nuiqWY2LzodXGrftijbX8iRFGitZmuXlj2QZ9d_DXW37Y06xRMPY86PqG0=tsojFSAXHcq4kMQW6Dfwak070fbv7ai5XKBRFVufx8tL9_F9Sj2fKzR8UzgP1DhdudsvzWBvGjEMuwN1uPD"
XQ_TOKEN = "967c71fd28250b546f72458b62e6c4a94076a1b7"

# 监控的用户 UID（数字，可以是自己的或他人的）
# MONITOR_UID = "2292705444"
MONITOR_UID = "4968062224"

# 企业微信机器人 Webhook
WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=d9dbb5f6-d692-4d07-8ea2-54a8ea5059fd"

# 检查间隔（秒），建议 ≥ 60 秒
CHECK_INTERVAL = 60

# 首次启动不推送，只记录基准
SILENT_FIRST_RUN = True

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class XueqiuMonitor:
    STATE_FILE = "monitor_state.json"

    def save_state(self):
        state = {
            "last_stocks": list(self.last_stocks),
            "last_post_ids": list(self.last_post_ids),
            "username": self.username,
            "stock_name_cache": self._stock_name_cache,
        }
        with open(self.STATE_FILE, "w") as f:
            json.dump(state, f)
        logger.debug("状态已保存")

    def load_state(self):
        if os.path.exists(self.STATE_FILE):
            with open(self.STATE_FILE, "r") as f:
                state = json.load(f)
            self.last_stocks = set(state.get("last_stocks", []))
            self.last_post_ids = set(state.get("last_post_ids", []))
            self.username = state.get("username")
            self._stock_name_cache = state.get("stock_name_cache", {})
            logger.info("已加载上次状态")
        else:
            self.last_stocks = set()
            self.last_post_ids = set()
            self._stock_name_cache = {}
    """雪球用户行为监控器（自选股 + 帖子增删）"""

    BASE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://xueqiu.com/",
    }

    def __init__(self, raw_cookie: str, uid: str, webhook: str):
        self.uid = uid
        self.webhook = webhook
        self.username = None  # 延迟从帖子获取
        self.portfolio_details = {}
        # 建立 session 并设置完整 Cookie
        self.session = requests.Session()
        self.session.headers.update(self.BASE_HEADERS)

        # 解析 Cookie 字符串并设置
        cookie_dict = {}
        for item in raw_cookie.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookie_dict[key] = value
        self.session.cookies.update(cookie_dict)
        logger.info("Cookie 已加载，包含字段: %s", list(cookie_dict.keys()))

        # 状态记录
        self.last_stocks: Set[str] = set()      # 股票代码集合
        self.last_post_ids: Set[int] = set()    # 帖子 ID 集合
        self._stock_name_cache = {}

    def _get_json(self, url: str, params: dict = None) -> dict:
        """统一 GET，带重试"""
        for attempt in range(2):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                # logger.info(resp._content)
                # logger.info(f"Response status: {resp.status_code}, body preview: {resp.text[:200]}")
                # resp.raise_for_status()
                # return resp.json()
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.warning(f"请求失败 {resp.status_code} {url}")
            except Exception as e:
                logger.error(f"请求异常: {e}，重试 {attempt+1}")
            time.sleep(2 * (attempt + 1))
        logger.error(f"多次请求失败: {url}")
        return {}

    # ---------- 用户名获取 ----------
    def _extract_username_from_posts(self, posts: List[Dict]):
        """从帖子中提取用户名（仅一次）"""
        if self.username is None and posts:
            user_info = posts[0].get("user", {})
            self.username = user_info.get("screen_name", self.uid)
            logger.info(f"已从帖子获取用户名: {self.username}")

    # ---------- 自选股 ----------
    def fetch_stocks(self) -> List[Dict[str, Any]]:
        """从 portfolios (category=2) 中分页拉取所有自选股"""
        list_url = "https://xueqiu.com/v4/stock/portfolio/list.json"
        data = self._get_json(list_url, {"uid": self.uid})
        portfolios = data.get("portfolios", [])
        if not portfolios:
            logger.warning("未获取到 portfolios 数据，检查 Cookie 是否有效")
            return []

        # 筛选 category=2 的组合
        stock_portfolios = [
            p for p in portfolios
            if p.get("portfolio", {}).get("category") == 2
        ]
        logger.info(f"找到 {len(stock_portfolios)} 个自选组合: {[p['name'] for p in stock_portfolios]}")

        all_stocks = []
        seen_codes = set()
        self.portfolio_details = {}
        for p in stock_portfolios:
            pid = p["portfolio"]["id"]
            name = p["name"]
            page = 1
            portfolio_stocks = []
            while True:
                url = "https://stock.xueqiu.com/v5/stock/portfolio/stock/list.json"
                params = {
                    "pid": pid,
                    "category": 2,
                    "uid": self.uid,
                    "page": page,
                    "size": 100,  # 每次拉取100条，减少请求次数
                    "t": int(time.time() * 1000),
                }
                resp = self._get_json(url, params)
                stocks = resp.get("data", {}).get("stocks", [])
                if not stocks:  # 没有更多数据，退出本组合的循环
                    break
                logger.info(f"组合[{name}] 第{page}页返回 {len(stocks)} 只股票")
                for s in stocks:
                    portfolio_stocks.append(s)
                    symbol = s.get("symbol")
                    if symbol and symbol not in seen_codes:
                        seen_codes.add(symbol)
                        all_stocks.append(s)
                page += 1
                time.sleep(0.5)  # 短暂休眠，避免触发频率限制
            self.portfolio_details[name] = portfolio_stocks
        logger.info(f"汇总后总自选股: {len(all_stocks)}")
        return all_stocks

    def detect_stock_changes(self, current_stocks: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """检测自选股新增和删除"""
        current_symbols = {s["symbol"] for s in current_stocks if "symbol" in s}
        if not self.last_stocks:
            self.last_stocks = current_symbols
            return [], []

        added = current_symbols - self.last_stocks
        removed = self.last_stocks - current_symbols

        added_stocks = [s for s in current_stocks if s["symbol"] in added]
        removed_stocks = [{"symbol": sym, "name": self._stock_name_cache.get(sym, sym)} for sym in removed]

        self.last_stocks = current_symbols
        return added_stocks, removed_stocks

    # @property
    # def _stock_name_cache(self) -> Dict[str, str]:
    #     """简单缓存：从最近一次拉取的 stocks 中建立 code->name 映射"""
    #     if not hasattr(self, '_stock_name_map'):
    #         self._stock_name_map = {}
    #     return self._stock_name_map

    # ---------- 帖子 ----------
    def fetch_recent_posts(self, count: int = 20) -> List[Dict]:
        """获取用户最新帖子"""
        url = "https://xueqiu.com/v4/statuses/user_timeline.json"
        params = {
            "user_id": self.uid,
            "page": 1,
            "type": 0,
            "count": count,
        }
        data = self._get_json(url, params)
        posts = data.get("statuses", [])
        if posts:
            # 更新股票名称缓存（从帖子中也可能获取不到，但这里不重要）
            pass
        return posts

    def detect_post_changes(self, current_posts: List[Dict]) -> Tuple[List[Dict], List[int]]:
        """
        返回 (新增帖子列表, 删除帖子ID列表)
        """
        current_ids = {p["id"] for p in current_posts if "id" in p}
        if not self.last_post_ids:
            self.last_post_ids = current_ids
            return [], []

        new_ids = current_ids - self.last_post_ids
        deleted_ids = self.last_post_ids - current_ids

        new_posts = [p for p in current_posts if p.get("id") in new_ids]

        # 更新记录，保留最近 200 个 ID
        self.last_post_ids = (self.last_post_ids | current_ids)
        if len(self.last_post_ids) > 200:
            sorted_ids = sorted(list(self.last_post_ids), reverse=True)
            self.last_post_ids = set(sorted_ids[:200])

        return new_posts, list(deleted_ids)

    # ---------- 推送 ----------
    def send_wechat_msg(self, content: str):
        """发送 Markdown 到企业微信"""
        payload = {
            "msgtype": "text",
            "text": {"content": content}
        }
        try:
            resp = requests.post(self.webhook, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("推送成功")
            else:
                logger.warning(f"推送失败: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"推送异常: {e}")

    def push_changes(self, added_stocks, removed_stocks, new_posts, deleted_post_ids):
        """组装推送内容"""
        if not (added_stocks or removed_stocks or new_posts or deleted_post_ids):
            return

        user_display = self.username if self.username else self.uid
        msg_parts = [f"雪球用户 {user_display} 动态提醒\n"]

        # 自选股变动
        if added_stocks:
            names = ", ".join(
                f"[{s['name']}({s['symbol']})](https://xueqiu.com/S/{s['symbol']})"
                for s in added_stocks
            )
            msg_parts.append(f"📈 新增自选：{names}")

        if removed_stocks:
            names = ", ".join(
                f"[{s['name']}({s['symbol']})](https://xueqiu.com/S/{s['symbol']})"
                for s in removed_stocks
            )
            msg_parts.append(f"📉 删除自选：{names}")

        # 帖子变动
        if new_posts:
            for post in new_posts:
                post_id = post["id"]
                text_preview = post.get("text", "").replace("\n", " ")[:50]
                post_url = f"https://xueqiu.com/{self.uid}/{post_id}"
                msg_parts.append(f"💬 新发帖：[{text_preview}...]({post_url})")

        if deleted_post_ids:
            # 删除时只有 ID，无法获取标题，可列出 ID 和时间（可选）
            deleted_list = ", ".join(str(pid) for pid in deleted_post_ids)
            msg_parts.append(f"🗑️ 删帖：帖子ID {deleted_list}")

        if len(msg_parts) > 1:
            full_msg = "\n".join(msg_parts)
            self.send_wechat_msg(full_msg)

        target_name = "只看沪深"
        if added_stocks or removed_stocks:
            target_stocks = self.portfolio_details.get(target_name, [])
            if target_stocks:
                stock_str = ", ".join(
                    f"{s['name']}({s['symbol']})" for s in target_stocks
                )
                header = f"📋 {user_display} 的「{target_name}」持仓\n"
                full_msg = header + stock_str
                self._send_markdown(full_msg)  # 自动处理超长拆分
        else:
            logger.info(f"未找到分组「{target_name}」，可能未创建或被重命名")

    def _send_markdown(self, content: str):
        """发送 Markdown 消息，超过 4096 字节自动拆分"""
        max_len = 4096
        if len(content.encode("utf-8")) <= max_len:
            self.send_wechat_msg(content)
            return
        # 按行拆分
        lines = content.split("\n")
        chunk = lines[0] + "\n"
        for line in lines[1:]:
            if len((chunk + line + "\n").encode("utf-8")) > max_len:
                self.send_wechat_msg(chunk)
                chunk = line + "\n"
            else:
                chunk += line + "\n"
        if chunk:
            self.send_wechat_msg(chunk)

    # ---------- 主循环 ----------
    def run_once(self):
        self.load_state()
        stocks = self.fetch_stocks()
        posts = self.fetch_recent_posts()
        self._extract_username_from_posts(posts)
        # 更新股票名称缓存
        name_map = {s["symbol"]: s.get("name", s["symbol"]) for s in stocks}
        self._stock_name_cache.update(name_map)

        added, removed = self.detect_stock_changes(stocks)
        new_posts, deleted_ids = self.detect_post_changes(posts)

        self.push_changes(added, removed, new_posts, deleted_ids)
        self.save_state()

    # def run_forever(self, interval: int = 60):
    #     """持续监控"""
    #     logger.info(f"开始监控用户 {self.uid}，间隔 {interval} 秒")
    #     self.run_once(silent_first=True)
    #     while True:
    #         time.sleep(interval)
    #         self.run_once(silent_first=False)


if __name__ == "__main__":
    import os

    RAW_COOKIE = os.getenv("RAW_COOKIE")
    MONITOR_UID = os.getenv("MONITOR_UID")
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")

    if not all([RAW_COOKIE, MONITOR_UID, WECHAT_WEBHOOK]):
        logger.error("缺少必要环境变量: RAW_COOKIE, MONITOR_UID, WECHAT_WEBHOOK")
        sys.exit(1)

    monitor = XueqiuMonitor(RAW_COOKIE, MONITOR_UID, WECHAT_WEBHOOK)

    # 单次执行，状态由 monitor_state.json 自动管理
    monitor.run_once()
    logger.info("单次检查完成")
