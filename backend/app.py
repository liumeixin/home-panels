import os
import json
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__, template_folder='templates')
CORS(app)

# 数据目录 - 通过环境变量或默认路径
DATA_DIR = os.environ.get('DATA_DIR', '/opt/data/hermes')

# ========== Token 模块 ==========

def load_token_plans():
    """加载 Token Plan 配置"""
    path = os.path.join(DATA_DIR, 'tokens', 'plans.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_token_daily():
    """加载每日 Token 用量"""
    daily_dir = os.path.join(DATA_DIR, 'tokens', 'daily')
    result = {}
    if os.path.exists(daily_dir):
        for f in os.listdir(daily_dir):
            if f.endswith('.json'):
                date_key = f.replace('.json', '')
                with open(os.path.join(daily_dir, f), 'r', encoding='utf-8') as fp:
                    result[date_key] = json.load(fp)
    return result

@app.route('/api/tokens/plans')
def get_token_plans():
    """获取 Token Plan 列表"""
    plans = load_token_plans()
    return jsonify(plans)

@app.route('/api/tokens/daily')
def get_token_daily():
    """获取每日 Token 用量"""
    daily = load_token_daily()
    return jsonify(daily)

@app.route('/api/tokens/summary')
def get_token_summary():
    """获取 Token 用量汇总"""
    plans = load_token_plans()
    daily = load_token_daily()
    
    # 汇总
    summary = {}
    for plan_name, plan_info in plans.items():
        total_usage = 0
        for day_data in daily.values():
            if plan_name in day_data:
                total_usage += day_data[plan_name].get('usage', 0)
        summary[plan_name] = {
            'name': plan_info.get('name', plan_name),
            'type': plan_info.get('type', 'unknown'),  # subscription / payg
            'limit': plan_info.get('limit', 0),
            'total_usage': total_usage,
            'remaining': plan_info.get('limit', 0) - total_usage
        }
    
    return jsonify(summary)

# ========== 家庭账本模块 ==========

def load_ledger():
    """加载账本数据"""
    path = os.path.join(DATA_DIR, 'family-ledger', 'daily.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/api/ledger/summary')
def get_ledger_summary():
    """获取账本年度/月度汇总"""
    transactions = load_ledger()
    
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # 年度统计
    year_income = 0
    year_expense = 0
    # 本月统计
    month_income = 0
    month_expense = 0
    # 今日统计
    today_income = 0
    today_expense = 0
    today_details = []
    
    for t in transactions:
        try:
            t_date = datetime.strptime(t.get('date', ''), '%Y-%m-%d').date()
        except:
            continue
        
        amount = t.get('amount', 0)
        t_type = t.get('type', '支出')
        
        # 年度
        if t_date.year == current_year:
            if t_type == '收入':
                year_income += amount
            else:
                year_expense += amount
        
        # 本月
        if t_date.year == current_year and t_date.month == current_month:
            if t_type == '收入':
                month_income += amount
            else:
                month_expense += amount
        
        # 今日
        if t_date == today:
            if t_type == '收入':
                today_income += amount
            else:
                today_expense += amount
            today_details.append(t)
    
    # 按日期排序今日明细
    today_details.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return jsonify({
        'year': {
            'income': year_income,
            'expense': year_expense,
            'balance': year_income - year_expense
        },
        'month': {
            'income': month_income,
            'expense': month_expense,
            'balance': month_income - month_expense
        },
        'today': {
            'income': today_income,
            'expense': today_expense,
            'balance': today_income - today_expense,
            'details': today_details
        }
    })

# ========== 工作任务模块 ==========

def load_tasks():
    """加载工作任务数据"""
    path = os.path.join(DATA_DIR, 'work-todo', 'todos.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/api/tasks/pending')
def get_pending_tasks():
    """获取未完成任务列表"""
    tasks = load_tasks()
    today = date.today()
    
    pending = []
    for t in tasks:
        if t.get('status') != 'completed':
            start = t.get('start')
            deadline = t.get('deadline')
            
            # 计算超期天数
            overdue_days = 0
            if deadline:
                try:
                    dl = datetime.fromisoformat(deadline).date()
                    if dl < today:
                        overdue_days = (today - dl).days
                except:
                    pass
            
            pending.append({
                'id': t.get('id'),
                'content': t.get('content'),
                'start': start,
                'deadline': deadline,
                'progress': t.get('progress', 0),
                'status': t.get('status'),
                'overdue_days': overdue_days
            })
    
    # 按截止时间排序（超期的排前面）
    pending.sort(key=lambda x: (x['overdue_days'] > 0, x['deadline'] or '9999'))
    
    return jsonify(pending)

@app.route('/api/tasks/search', methods=['POST'])
def search_tasks():
    """查询指定日期范围内的任务"""
    data = request.json
    start_range = data.get('start_date')  # YYYY-MM-DD
    end_range = data.get('end_date')      # YYYY-MM-DD
    
    if not start_range or not end_range:
        return jsonify({'error': '需要提供 start_date 和 end_date'}), 400
    
    try:
        start_dt = datetime.strptime(start_range, '%Y-%m-%d')
        end_dt = datetime.strptime(end_range, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': '日期格式错误，应为 YYYY-MM-DD'}), 400
    
    tasks = load_tasks()
    results = []
    
    for t in tasks:
        task_start = t.get('start')
        task_deadline = t.get('deadline')
        task_complete = t.get('completed_at')
        
        # 判断是否有任务时间在查询范围内
        in_range = False
        
        if task_start:
            try:
                s = datetime.fromisoformat(task_start)
                if start_dt <= s <= end_dt:
                    in_range = True
            except:
                pass
        
        if task_deadline:
            try:
                d = datetime.fromisoformat(task_deadline)
                if start_dt <= d <= end_dt:
                    in_range = True
            except:
                pass
        
        if task_complete:
            try:
                c = datetime.fromisoformat(task_complete)
                if start_dt <= c <= end_dt:
                    in_range = True
            except:
                pass
        
        if in_range:
            # 判断是否按时完成
            on_time = None
            if task_deadline and task_complete:
                try:
                    dl = datetime.fromisoformat(task_deadline)
                    ct = datetime.fromisoformat(task_complete)
                    on_time = ct <= dl
                except:
                    pass
            
            results.append({
                'content': t.get('content'),
                'start': task_start,
                'deadline': task_deadline,
                'completed_at': task_complete,
                'on_time': on_time
            })
    
    return jsonify(results)

# ========== 前端页面 ==========

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)