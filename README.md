# HomePanels - 家庭数字仪表盘

一个整合 Token 用量、家庭账本、工作任务的统一管理面板。

## 快速开始

```bash
# 1. 构建并启动
cd /opt/data/workspace/Projects/home-panels
docker-compose up -d

# 2. 访问
http://<NAS-IP>:18090
```

## 功能

### 1. Token 仪表盘
- 显示各供应商 Token Plan 的每日用量和总用量
- 支持订阅制和按量付费两种类型
- 提供 Token 优化建议

### 2. 家庭账本
- 本年度收支概况
- 本月收支概况  
- 今日收支详单

### 3. 工作任务
- 未完成任务列表（含超期天数）
- 任务时间范围查询

## 数据目录

```
/opt/data/hermes/
├── tokens/
│   ├── daily/              # 每日用量 JSON 文件（YYYY-MM-DD.json）
│   └── plans.json          # Token Plan 配置
├── family-ledger/          # 家庭账本数据（自动复用）
└── work-todo/              # 工作任务数据（自动复用）
```

## Token 用量数据格式

### plans.json
```json
{
  "key-name": {
    "name": "显示名称",
    "type": "subscription" 或 "payg",
    "limit": 限额
  }
}
```

### daily/YYYY-MM-DD.json
```json
{
  "key-name": {"usage": 用量}
}
```

## 开发

```bash
# 本地运行
cd backend
pip install flask flask-cors
python app.py

# 构建镜像
docker build -t ghcr.io/liumeixin/home-panels:latest .
docker push ghcr.io/liumeixin/home-panels:latest
```

## 目录结构

```
home-panels/
├── Dockerfile
├── docker-compose.yml
├── README.md
├── backend/
│   ├── app.py              # Flask API
│   └── templates/
│       └── index.html      # 前端页面
└── frontend/               # 预留前端目录
```