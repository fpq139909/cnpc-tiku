# 党建云题目提取（云端版）· 容器镜像
# 适配：晃晃云 CloudBase 云托管 / Render / Railway 等支持 Docker 的常驻平台
FROM python:3.11-slim

WORKDIR /app

# 依赖（pycryptodome 等）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 业务代码
COPY . .

# 平台会通过环境变量 PORT 注入端口，服务监听 0.0.0.0:PORT
# GITHUB_TOKEN 同样通过平台环境变量注入（不写进镜像 / 公开仓库）
EXPOSE 8000

CMD ["python", "cnpc_app.py"]
