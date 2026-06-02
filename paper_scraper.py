"""
学术论文爬取与摘要工具
支持来源：arxiv (cs.DB / cs.DC / cs.NI / cs.CR / cs.PL)、papers.cool
         DB顶会：VLDB / SIGMOD / ICDE
         分布式顶会：OSDI / SOSP / NSDI / USENIX ATC / EuroSys
         Web3安全：IEEE S&P / ACM CCS / FC（via DBLP API）

依赖：pip install requests beautifulsoup4 anthropic
用法示例：
  python paper_scraper.py --max 20
  python paper_scraper.py --max 10 --proxy http://127.0.0.1:7890
  python paper_scraper.py --max 50 --no-confs         # 只爬 arxiv + papers.cool
  python paper_scraper.py --domain-only                # 只保留数据库/分布式/Web3 相关论文
"""

from __future__ import annotations

import re
import json
import time
import argparse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ── 常量 ─────────────────────────────────────────────────────────────────────

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_NS = "http://www.w3.org/2005/Atom"
ARXIV_CATEGORIES = [
    "cs.DB",   # 数据库
    "cs.DC",   # 分布式、并行计算
    "cs.NI",   # 网络与互联网架构
    "cs.CR",   # 密码学与安全（含 Web3 安全）
    "cs.PL",   # 编程语言（含智能合约分析）
    "cs.SE",   # 软件工程
]

PAPERSCOOL_CATEGORIES = [
    "cs.DB", "cs.DC", "cs.NI", "cs.CR",
]

# 会议配置（DB顶会 + 分布式系统顶会 + Web3安全顶会），通过 DBLP TOC API 爬取
CONF_BASES = [
    # ── 数据库顶会 ──
    {"name": "VLDB",      "dblp_prefix": "conf/vldb/vldb",     "source_prefix": "db:vldb",     "abstract_url_tpl": None},
    {"name": "SIGMOD",    "dblp_prefix": "conf/sigmod/sigmod",  "source_prefix": "db:sigmod",   "abstract_url_tpl": None},
    {"name": "ICDE",      "dblp_prefix": "conf/icde/icde",      "source_prefix": "db:icde",     "abstract_url_tpl": None},
    # ── 分布式系统顶会 ──
    {"name": "OSDI",      "dblp_prefix": "conf/osdi/osdi",      "source_prefix": "dist:osdi",   "abstract_url_tpl": "https://www.usenix.org/conference/osdi{year2}/technical-sessions"},
    {"name": "SOSP",      "dblp_prefix": "conf/sosp/sosp",      "source_prefix": "dist:sosp",   "abstract_url_tpl": None},
    {"name": "NSDI",      "dblp_prefix": "conf/nsdi/nsdi",      "source_prefix": "dist:nsdi",   "abstract_url_tpl": "https://www.usenix.org/conference/nsdi{year2}/technical-sessions"},
    {"name": "USENIX ATC","dblp_prefix": "conf/usenix/usenix",  "source_prefix": "dist:atc",    "abstract_url_tpl": "https://www.usenix.org/conference/atc{year2}/technical-sessions"},
    {"name": "EuroSys",   "dblp_prefix": "conf/eurosys/eurosys","source_prefix": "dist:eurosys","abstract_url_tpl": None},
    # ── Web3 / 安全顶会 ──
    {"name": "IEEE S&P",  "dblp_prefix": "conf/sp/sp",          "source_prefix": "sec:sp",      "abstract_url_tpl": None},
    {"name": "ACM CCS",   "dblp_prefix": "conf/ccs/ccs",        "source_prefix": "sec:ccs",     "abstract_url_tpl": None},
    {"name": "Financial Cryptography", "dblp_prefix": "conf/fc/fc", "source_prefix": "web3:fc", "abstract_url_tpl": None},
]

# 数据库 / 分布式 / Web3 / 网络 相关关键词（匹配标题或摘要，不区分大小写）
DOMAIN_KEYWORDS = [
    # 数据库
    "database", "SQL", "query optimization", "query processing", "transaction",
    "ACID", "NoSQL", "key-value", "relational", "index", "B-tree", "LSM-tree",
    "storage engine", "OLAP", "OLTP", "data warehouse", "columnar",
    "distributed database", "NewSQL", "HTAP", "time series", "graph database",
    "data model", "query language", "query compiler", "data lakehouse",
    # 分布式系统
    "distributed", "consensus", "Raft", "Paxos", "fault tolerance", "replication",
    "consistency", "availability", "partition tolerance", "CAP", "CRDT",
    "sharding", "load balancing", "microservices", "serverless", "cloud native",
    "Byzantine", "distributed ledger", "distributed storage", "cluster",
    # Web3 / 区块链
    "blockchain", "smart contract", "Ethereum", "DeFi", "decentralized",
    "cryptocurrency", "NFT", "Web3", "DAO", "zero-knowledge", "ZK proof",
    "MEV", "layer 2", "rollup", "oracle", "flash loan", "Solidity",
    "EVM", "on-chain", "off-chain", "cross-chain", "interoperability",
    # 网络
    "network protocol", "P2P", "peer-to-peer", "gossip protocol",
]

DBLP_PUBL_API = "https://dblp.org/search/publ/api"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


# ── 数据结构 ──────────────────────────────────────────────────────────────────

@dataclass
class Paper:
    title: str
    authors: list
    abstract: str
    url: str
    pdf_url: str
    published: str
    source: str
    paper_id: str = ""
    summary: str = ""


# ── HTTP 会话（支持代理）─────────────────────────────────────────────────────

def make_session(proxy: str = "") -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


# ── arxiv 爬取 ────────────────────────────────────────────────────────────────

def fetch_arxiv(category: str, max_results: int, session: requests.Session) -> list:
    """通过 arxiv 官方 API 获取最新论文，无需浏览器。失败自动重试 3 次。"""
    params = {
        "search_query": f"cat:{category}",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    for attempt in range(3):
        try:
            resp = session.get(ARXIV_API, params=params, timeout=60)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                raise
            wait = 15 * (attempt + 1)
            print(f"    重试 {attempt + 1}/3（等待 {wait}s）: {e}")
            time.sleep(wait)

    root = ET.fromstring(resp.text)
    papers = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        arxiv_id = entry.findtext(f"{{{ARXIV_NS}}}id", "").split("/abs/")[-1]
        papers.append(Paper(
            title=_clean(entry.findtext(f"{{{ARXIV_NS}}}title", "")),
            authors=[
                a.findtext(f"{{{ARXIV_NS}}}name", "")
                for a in entry.findall(f"{{{ARXIV_NS}}}author")
            ],
            abstract=_clean(entry.findtext(f"{{{ARXIV_NS}}}summary", "")),
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
            published=entry.findtext(f"{{{ARXIV_NS}}}published", "")[:10],
            source=f"arxiv:{category}",
            paper_id=arxiv_id,
        ))

    print(f"  arxiv:{category} — {len(papers)} 篇")
    return papers


# ── papers.cool 爬取 ─────────────────────────────────────────────────────────

def fetch_paperscool(category: str, max_results: int, session: requests.Session) -> list:
    """从 papers.cool 爬取指定 arxiv 分类的当日论文列表。"""
    url = f"https://papers.cool/arxiv/{category}"
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                raise
            wait = 10 * (attempt + 1)
            print(f"    重试 {attempt + 1}/3（等待 {wait}s）: {e}")
            time.sleep(wait)

    soup = BeautifulSoup(resp.text, "html.parser")
    papers = []

    for div in soup.select("div.paper")[:max_results]:
        arxiv_id = div.get("id", "")

        title_tag = div.select_one("a.title-link")
        title = _clean(title_tag.get_text()) if title_tag else ""

        authors = [a.get_text(strip=True) for a in div.select("a.author")]

        summary_tag = div.select_one("p.summary")
        abstract = _clean(summary_tag.get_text()) if summary_tag else ""

        date_tag = div.select_one("p.date")
        published = ""
        if date_tag:
            # "Publish:2026-05-07 17:56:32 UTC" → "2026-05-07"
            m = re.search(r"(\d{4}-\d{2}-\d{2})", date_tag.get_text())
            published = m.group(1) if m else ""

        pdf_tag = div.select_one("a.title-pdf")
        pdf_url = pdf_tag.get("data", f"https://arxiv.org/pdf/{arxiv_id}") if pdf_tag else f"https://arxiv.org/pdf/{arxiv_id}"

        papers.append(Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=pdf_url,
            published=published,
            source=f"paperscool:{category}",
            paper_id=arxiv_id,
        ))

    print(f"  paperscool:{category} — {len(papers)} 篇")
    return papers


# ── DB / 分布式 / Web3 顶会爬取 ──────────────────────────────────────────────

def fetch_conf(conf: dict, max_results: int, session: requests.Session) -> list:
    """通过 DBLP TOC API 获取顶会论文，并尝试补充开放摘要（USENIX 类型会议）。"""
    papers = _fetch_dblp_toc(conf, max_results, session)
    if not papers:
        return []

    # 尝试从会议网站补充摘要
    abstract_url = conf.get("abstract_url")
    if abstract_url:
        try:
            if "usenix.org" in abstract_url:
                ab_map = _fetch_usenix_abstracts(abstract_url, session)
            else:
                ab_map = {}
            if ab_map:
                matched = _merge_abstracts(papers, ab_map)
                print(f"    补充摘要：{matched}/{len(papers)} 篇")
        except Exception as e:
            print(f"    摘要补充跳过（{e}）")

    return papers


def _fetch_dblp_toc(conf: dict, max_results: int, session: requests.Session) -> list:
    """调用 DBLP TOC API，返回 Paper 列表（无摘要）。"""
    name = conf["name"]
    dblp_key = conf["dblp_key"]
    source = conf["source"]
    year = conf["year"]

    # DBLP TOC 查询：toc:db/<key>.bht:
    params = {
        "q": f"toc:db/{dblp_key}.bht:",
        "format": "json",
        "h": max_results,
        "f": 0,
    }
    for attempt in range(3):
        try:
            resp = session.get(DBLP_PUBL_API, params=params, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                print(f"  {name} DBLP 失败：{e}")
                return []
            wait = 10 * (attempt + 1)
            print(f"    重试 {attempt + 1}/3（等待 {wait}s）: {e}")
            time.sleep(wait)

    hits = resp.json().get("result", {}).get("hits", {}).get("hit", [])
    if not isinstance(hits, list):
        hits = [hits] if hits else []

    papers = []
    for hit in hits:
        info = hit.get("info", {})
        title = _clean(info.get("title", ""))
        if not title or title.lower().startswith("proceedings of"):
            continue

        # 作者：可能是 dict 或 list
        authors_raw = info.get("authors", {}).get("author", [])
        if isinstance(authors_raw, dict):
            authors_raw = [authors_raw]
        authors = [
            (a.get("text", "") if isinstance(a, dict) else str(a))
            for a in authors_raw
        ]

        # 优先用 ee（electronic edition URL），其次 doi，再 dblp url
        ee = info.get("ee", "")
        if isinstance(ee, list):
            ee = ee[0] if ee else ""
        doi = info.get("doi", "")
        url = ee or (f"https://doi.org/{doi}" if doi else
                     f"https://dblp.org/rec/{info.get('key', '')}")

        papers.append(Paper(
            title=title,
            authors=authors,
            abstract="",
            url=url,
            pdf_url="",
            published=year,
            source=source,
            paper_id=info.get("key", ""),
        ))

    print(f"  {name} — {len(papers)} 篇（via DBLP）")
    return papers


def _fetch_usenix_abstracts(url: str, session: requests.Session) -> dict:
    """爬取 USENIX 会议技术日程页，返回 {title_lower: abstract} 映射。"""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    ab_map: dict = {}

    # USENIX 页面结构：article.node-paper 或 div.paper
    for node in soup.select("article.node--type-paper, article.node-paper, div.paper-record"):
        # 标题
        t_tag = node.select_one("h3 a, h2 a, .paper-title a, .field--name-title a")
        if not t_tag:
            continue
        title = _clean(t_tag.get_text())

        # 摘要：多种选择器兼容
        ab_tag = node.select_one(
            ".field--name-field-paper-description, "
            ".paper-abstract, "
            ".field-name-field-paper-description, "
            "div.abstract"
        )
        abstract = _clean(ab_tag.get_text()) if ab_tag else ""
        if title:
            ab_map[title.lower()] = abstract

    return ab_map


def _fetch_ndss_abstracts(url: str, session: requests.Session) -> dict:
    """爬取 NDSS accepted-papers 页，返回 {title_lower: abstract} 映射。"""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    ab_map: dict = {}

    # NDSS 页面：每篇用 <div class="paper-title"> + <div class="abstract-text">
    for entry in soup.select("div.accepted-paper, article.paper, div.paper-entry"):
        t_tag = entry.select_one(".paper-title a, h3 a, h4 a, .entry-title a")
        if not t_tag:
            # 尝试直接找标题文本
            t_tag = entry.select_one(".paper-title, h3, h4")
        if not t_tag:
            continue
        title = _clean(t_tag.get_text())

        ab_tag = entry.select_one(".abstract-text, .abstract, p.abstract")
        abstract = _clean(ab_tag.get_text()) if ab_tag else ""
        if title:
            ab_map[title.lower()] = abstract

    # 备用：如果上面选择器没匹配到，尝试更通用的结构
    if not ab_map:
        for h in soup.select("h3, h4"):
            title = _clean(h.get_text())
            if not title or len(title) < 10:
                continue
            # 找相邻摘要
            sib = h.find_next_sibling()
            abstract = ""
            while sib and sib.name in ("div", "p"):
                text = _clean(sib.get_text())
                if len(text) > 50:
                    abstract = text
                    break
                sib = sib.find_next_sibling()
            ab_map[title.lower()] = abstract

    return ab_map


def _merge_abstracts(papers: list, ab_map: dict) -> int:
    """将 ab_map 中的摘要按标题匹配填入 papers，返回匹配数。
    容忍末尾标点差异（DBLP 标题常带句点）。"""
    matched = 0
    for p in papers:
        key = p.title.lower().strip().rstrip(".")
        if key in ab_map and ab_map[key]:
            p.abstract = ab_map[key]
            matched += 1
            continue
        # 带点版本也试一次
        key_dot = key + "."
        if key_dot in ab_map and ab_map[key_dot]:
            p.abstract = ab_map[key_dot]
            matched += 1
    return matched


# ── Claude 中文摘要（可选）───────────────────────────────────────────────────

def summarize_with_claude(papers: list, api_key: str) -> None:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    for p in papers:
        if not p.abstract:
            continue
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": (
                        f"用中文一句话总结这篇论文的核心贡献（50字以内）：\n\n"
                        f"标题：{p.title}\n摘要：{p.abstract[:800]}"
                    ),
                }],
            )
            p.summary = msg.content[0].text.strip()
        except Exception as e:
            print(f"  摘要失败 {p.paper_id}: {e}")
        time.sleep(0.3)


# ── 保存结果 ──────────────────────────────────────────────────────────────────

def save_results(papers: list, output_dir: str) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")

    (out / f"papers_{stamp}.json").write_text(
        json.dumps([asdict(p) for p in papers], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    md_path = out / f"papers_{stamp}.md"
    lines = [f"# 论文汇总 {stamp}\n\n共 {len(papers)} 篇\n"]
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors[:5]) + ("等" if len(p.authors) > 5 else "")
        lines += [
            f"## {i}. {p.title}",
            f"**来源**：{p.source}  |  **时间**：{p.published}",
            f"**作者**：{authors_str}",
            f"**链接**：[摘要]({p.url})  |  [PDF]({p.pdf_url})",
        ]
        if p.summary:
            lines.append(f"**核心贡献**：{p.summary}")
        lines.append(f"\n> {p.abstract[:300]}{'...' if len(p.abstract) > 300 else ''}\n")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def deduplicate(papers: list) -> list:
    """按 paper_id 去重，保留首次出现的那篇。"""
    seen: set = set()
    result = []
    for p in papers:
        key = p.paper_id or p.url
        if key not in seen:
            seen.add(key)
            result.append(p)
    removed = len(papers) - len(result)
    if removed:
        print(f"  去重：移除 {removed} 篇重复论文，剩余 {len(result)} 篇")
    return result


def _seen_papers_path(output_dir: str) -> Path:
    return Path(output_dir) / ".seen_papers.json"


def _load_seen_ids(output_dir: str) -> set:
    p = _seen_papers_path(output_dir)
    if not p.exists():
        return set()
    return set(json.loads(p.read_text(encoding="utf-8")))


def _save_seen_ids(seen: set, output_dir: str) -> None:
    p = _seen_papers_path(output_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")


def filter_new_only(papers: list, output_dir: str) -> list:
    """只保留跨运行首次出现的论文，并将新论文 ID 写入持久化文件。"""
    seen = _load_seen_ids(output_dir)
    new_papers = []
    for p in papers:
        key = p.paper_id or p.url
        if key not in seen:
            seen.add(key)
            new_papers.append(p)
    removed = len(papers) - len(new_papers)
    if removed:
        print(f"  跨运行去重：移除 {removed} 篇已见论文，剩余 {len(new_papers)} 篇新论文")
    _save_seen_ids(seen, output_dir)
    return new_papers


def filter_by_keywords(papers: list, keywords: list) -> list:
    """保留标题或摘要中包含任意关键词的论文（大小写不敏感）。"""
    if not keywords:
        return papers
    patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]

    def matches(p) -> bool:
        text = p.title + " " + p.abstract
        return any(pat.search(text) for pat in patterns)

    result = [p for p in papers if matches(p)]
    print(f"  关键词过滤：{len(papers)} → {len(result)} 篇")
    return result


# ── 会议状态追踪（避免重复爬取静态论文集）────────────────────────────────────

def _conf_state_path(output_dir: str) -> Path:
    return Path(output_dir) / ".conf_state.json"


def _load_conf_state(output_dir: str) -> dict:
    """加载已爬取的会议记录，结构：{conf_id: "YYYY-MM-DD"}"""
    p = _conf_state_path(output_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _save_conf_state(state: dict, output_dir: str) -> None:
    p = _conf_state_path(output_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 会议最新年份自动探测 ──────────────────────────────────────────────────────

def _dblp_latest_year(dblp_prefix: str, session: requests.Session,
                      years_back: int = 2) -> int | None:
    """探测 DBLP 上该前缀最新有论文的年份（向前探测 years_back 年，含重试）"""
    cur = datetime.now().year
    for year in range(cur, cur - years_back - 1, -1):
        params = {"q": f"toc:db/{dblp_prefix}{year}.bht:", "format": "json", "h": "1"}
        for attempt in range(3):
            try:
                r = session.get(DBLP_PUBL_API, params=params, timeout=20)
                r.raise_for_status()
                total = int(r.json().get("result", {}).get("hits", {}).get("@total", "0"))
                if total > 0:
                    return year
                break  # 请求成功但无结果，不必重试
            except Exception:
                if attempt < 2:
                    time.sleep(8 * (attempt + 1))
        time.sleep(2)
    return None


# DBLP 不可用时的兜底年份（每年年初手动更新一次，或等 DBLP 恢复后自动探测）
_CONF_FALLBACK_YEARS: dict[str, int] = {
    "conf/vldb/vldb":      2024,
    "conf/sigmod/sigmod":  2025,
    "conf/icde/icde":      2025,
    "conf/osdi/osdi":      2024,
    "conf/sosp/sosp":      2023,
    "conf/nsdi/nsdi":      2025,
    "conf/usenix/usenix":  2024,
    "conf/eurosys/eurosys": 2025,
    "conf/sp/sp":          2025,
    "conf/ccs/ccs":        2024,
    "conf/fc/fc":          2025,
}


def _resolve_conf(base: dict, session: requests.Session) -> dict | None:
    """将 CONF_BASES 条目解析为含具体年份的完整配置，找不到则返回 None"""
    year = _dblp_latest_year(base["dblp_prefix"], session)
    if year is None:
        year = _CONF_FALLBACK_YEARS.get(base["dblp_prefix"])
        if year is None:
            return None
        print(f"    {base['name']}: DBLP 探测超时，使用兜底年份 {year}")
    year2 = str(year)[2:]
    ab_tpl = base.get("abstract_url_tpl")
    abstract_url = (
        ab_tpl.replace("{year}", str(year)).replace("{year2}", year2)
        if ab_tpl else None
    )
    return {
        "name":         f"{base['name']} {year}",
        "dblp_key":     f"{base['dblp_prefix']}{year}",
        "abstract_url": abstract_url,
        "source":       f"{base['source_prefix']}{year}",
        "year":         str(year),
    }


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="数据库/分布式/Web3 学术论文爬取工具")
    parser.add_argument("--max", type=int, default=20, help="每个来源最多抓取篇数")
    parser.add_argument("--no-arxiv", action="store_true", help="跳过 arxiv")
    parser.add_argument("--no-paperscool", action="store_true", help="跳过 papers.cool")
    parser.add_argument("--no-confs", action="store_true",
                        help="跳过 DB/分布式/Web3 顶会（VLDB / SIGMOD / ICDE / OSDI / SOSP / NSDI / ATC / EuroSys / IEEE S&P / ACM CCS / FC）")
    parser.add_argument("--force-confs", action="store_true",
                        help="强制重新爬取已爬过的会议（忽略状态文件）")
    parser.add_argument("--proxy", default="", help="HTTP 代理，如 http://127.0.0.1:7890")
    parser.add_argument("--claude-key", default="", help="Claude API Key（生成中文摘要）")
    parser.add_argument("--output", default="output/papers", help="输出目录")
    parser.add_argument("--domain-only", action="store_true",
                        help="只保留数据库/分布式/Web3 相关论文（使用内置关键词表）")
    parser.add_argument("--keywords", default="",
                        help="自定义过滤关键词，逗号分隔，如 'Raft,blockchain,query'")
    args = parser.parse_args()

    session = make_session(proxy=args.proxy)
    all_papers = []
    conf_state = _load_conf_state(args.output)
    today = datetime.now().strftime("%Y-%m-%d")

    def _skip(conf_id: str, label: str) -> bool:
        """若已爬过且未强制刷新则跳过，返回 True 表示跳过。"""
        if args.force_confs:
            return False
        crawled_on = conf_state.get(conf_id)
        if crawled_on:
            print(f"  跳过 {label}（已爬取：{crawled_on}，用 --force-confs 强制刷新）")
            return True
        return False

    if not args.no_arxiv:
        print("=== arxiv ===")
        for cat in ARXIV_CATEGORIES:
            try:
                all_papers += fetch_arxiv(cat, args.max, session)
                time.sleep(10)
            except Exception as e:
                print(f"  {cat} 失败：{e}")

    if not args.no_paperscool:
        print("\n=== papers.cool ===")
        for cat in PAPERSCOOL_CATEGORIES:
            try:
                all_papers += fetch_paperscool(cat, args.max, session)
                time.sleep(2)
            except Exception as e:
                print(f"  {cat} 失败：{e}")

    if not args.no_confs:
        print("\n=== DB/分布式/Web3 顶会 ===")
        for base in CONF_BASES:
            conf = _resolve_conf(base, session)
            if not conf:
                print(f"  {base['name']}: DBLP 未找到有效年份，跳过")
                continue
            if _skip(conf["source"], conf["name"]):
                continue
            try:
                papers = fetch_conf(conf, args.max, session)
                all_papers += papers
                if papers:
                    conf_state[conf["source"]] = today
                time.sleep(3)
            except Exception as e:
                print(f"  {conf['name']} 失败：{e}")

    _save_conf_state(conf_state, args.output)

    # 后处理
    print("\n=== 后处理 ===")
    all_papers = deduplicate(all_papers)
    all_papers = filter_new_only(all_papers, args.output)

    keywords = []
    if args.domain_only:
        keywords = DOMAIN_KEYWORDS
    elif args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if keywords:
        all_papers = filter_by_keywords(all_papers, keywords)

    if args.claude_key:
        print(f"\n=== 生成中文摘要（共 {len(all_papers)} 篇）===")
        summarize_with_claude(all_papers, args.claude_key)

    md_path = save_results(all_papers, args.output)
    print(f"\n完成！{len(all_papers)} 篇论文 → {md_path.parent}/")


if __name__ == "__main__":
    main()
