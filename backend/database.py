"""
政策文档分析结果数据库
"""
import sqlite3
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'policy_docs.db')
DATA_DIR = os.path.dirname(DB_PATH)


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            score REAL NOT NULL,
            summary TEXT,
            source_url TEXT,
            publish_org TEXT,
            publish_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_score ON analysis_results(score)')
    conn.commit()
    conn.close()


def scan_analyze_results():
    """扫描 analyze_result/ 目录，导入分析结果"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    result_dir = os.path.join(base_dir, 'analyze_result')

    if not os.path.exists(result_dir):
        print(f"目录不存在: {result_dir}")
        return []

    conn = get_connection()
    cursor = conn.cursor()
    imported = []

    for root, dirs, files in os.walk(result_dir):
        for filename in files:
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(root, filename)

            # 解析文件名
            name = filename.replace('.md', '')
            score_match = re.search(r'_分析结果_(\d+\.?\d*)', name)
            score = float(score_match.group(1)) if score_match else 0.0
            title = re.sub(r'_分析结果_\d+\.?\d*$', '', name).replace('_', ' ')

            # 读取文件
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                print(f"读取失败: {filename}")
                continue

            # 提取内容
            summary_match = re.search(r'### 全文概要\s*\n(.+?)(?=\n> \*\*总分\*\*|\n###|\Z)', content, re.DOTALL)
            summary = summary_match.group(1).strip() if summary_match else ''

            url_match = re.search(r'原文链接[：:]\s*(https?://\S+)', content)
            source_url = url_match.group(1) if url_match else ''

            org_match = re.search(r'发布机构[：:]\s*(.+)', content)
            publish_org = org_match.group(1).strip() if org_match else ''

            date_match = re.search(r'发布日期[：:]\s*(.+)', content)
            publish_date = date_match.group(1).strip() if date_match else ''

            # 存在则替换，不存在则新增
            cursor.execute('SELECT id FROM analysis_results WHERE title = ?', (title,))
            if cursor.fetchone():
                cursor.execute('''
                    UPDATE analysis_results SET
                        score = ?, summary = ?, source_url = ?,
                        publish_org = ?, publish_date = ?, created_at = ?
                    WHERE title = ?
                ''', (score, summary, source_url, publish_org, publish_date,
                      datetime.now().isoformat(), title))
                imported.append({'file': filename, 'action': 'updated'})
            else:
                cursor.execute('''
                    INSERT INTO analysis_results
                    (title, score, summary, source_url, publish_org, publish_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, score, summary, source_url, publish_org, publish_date,
                      datetime.now().isoformat()))
                imported.append({'file': filename, 'action': 'imported'})

    conn.commit()
    conn.close()
    return imported


def get_all_results():
    """获取所有结果"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analysis_results ORDER BY score DESC')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def search_results(keyword=None, min_score=None):
    """搜索结果"""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM analysis_results WHERE 1=1'
    params = []

    if keyword:
        query += ' AND (title LIKE ? OR summary LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if min_score is not None:
        query += ' AND score >= ?'
        params.append(min_score)

    query += ' ORDER BY score DESC'
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_statistics():
    """统计信息"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as c, AVG(score) as avg FROM analysis_results')
    row = cursor.fetchone()
    conn.close()
    return {'total': row['c'], 'avg_score': round(row['avg'] or 0, 1)}


if __name__ == '__main__':
    init_db()
    print("\n扫描 analyze_result/ 目录...")
    results = scan_analyze_results()

    if results:
        print(f"\n处理了 {len(results)} 个文件:")
        for r in results:
            print(f"  [{r['action']}] {r['file']}")
    else:
        print("没有找到分析结果文件")

    stats = get_statistics()
    print(f"\n统计: 共 {stats['total']} 条, 平均分 {stats['avg_score']}")


# 兼容旧名称
migrate_existing_files = scan_analyze_results
