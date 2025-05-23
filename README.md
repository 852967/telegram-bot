# Telegram群管机器人

基于Python和python-telegram-bot框架开发的群组管理机器人，提供成员管理、签到系统、发言统计等功能。

## 功能特性

- 成员签到系统
- 成员管理（封禁/禁言）
- 发言次数统计
- 新人欢迎系统
- 入群鉴权机制

## 安装指南

1. 克隆项目：
   ```bash
   git clone <项目地址>
   ```

2. 创建并激活虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 配置环境变量：
   - 复制`.env.example`为`.env`
   - 修改`.env`中的配置项

## 运行项目

```bash
python src/main.py
```

## 项目结构

```
├── src/            # 源代码
├── tests/          # 测试代码
├── config/         # 配置文件
├── venv/           # 虚拟环境
├── README.md       # 项目文档
└── .gitignore      # Git忽略规则
```

## 开发说明

- 遵循PEP8编码规范
- 使用类型注解
- 所有功能需包含单元测试