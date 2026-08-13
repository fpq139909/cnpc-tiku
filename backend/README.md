# 党建云题目提取（云端版）· 永不休眠固定网址部署

把本地 `127.0.0.1:8000` 的全部功能（检测打钩 / 提取题目 / 推送手机端题库）搬到
**常驻云平台**，得到固定外网网址：电脑关机、不在身边，手机随时打开、随时改 rx_token、随时同步。

> 为什么必须保留后端：党建平台「题目详情」接口 `queryTestInfo` 跨域被拦截（HTTP 403），
> 浏览器取不到题目，必须由后端代理。本目录即这个轻后端 + 手机自适应管理界面
> （单文件 `cnpc_app.py`）。

## 文件清单
- `cnpc_app.py`：Web 服务 + 管理界面（rx_token 存浏览器本地，可随时改）
- `cnpc_extract.py`：题目提取（含 RSA / AES 解密）
- `requirements.txt`：依赖 `pycryptodome`
- `Dockerfile` / `Procfile` / `start.sh`：容器与启动命令
- `gh_repo.txt`：目标仓库 `fpq139909/cnpc-tiku @ main`（手机端题库来源）

> 安全：本目录**不含 GitHub token**。token 通过平台环境变量 `GITHUB_TOKEN` 注入（见各步骤），
> 不写进公开仓库。

---

## 关于「永不休眠」的实话

常驻服务要持续占用算力，平台才有成本，因此：
- **免费方案几乎都会休眠**（空闲几分钟~几十分钟后停服，下次访问需冷启动数秒~数十秒）。
- **真正永不休眠** = 付费常驻，或国内「云函数/云托管」（按量、空闲不占进程但随时可唤醒，
  基本等价于永不掉线，且有免费额度）。

下面三个平台都能拿到**固定网址**，区别在「国内速度 / 是否要付费 / 上手难度」。

| 平台 | 国内速度 | 永不休眠条件 | 上手 | 固定网址 |
|------|----------|--------------|------|----------|
| **晃晃云 CloudBase 云托管**（推荐） | 快（腾讯系） | 云托管常驻/按量，空闲不休眠 | 中（需腾讯云账号+实名） | `*.apigw.tencentcs.com` 可绑自定义域名 |
| **Render** | 偏慢（海外） | 付费 $7/月 不休眠；免费版休眠 | 最简单 | `*.onrender.com` |
| **Railway** | 偏慢（海外） | 付费常驻；免费额度有限 | 简单 | `*.up.railway.app` |

---

## A. 晃晃云 CloudBase 云托管（推荐：国内快、不休眠、腾讯生态契合）

适合：人在国内、要稳定常驻、愿意用腾讯云账号（先锋党建本就是腾讯系，大概率已有/易有）。

1. 注册并登录 [晃晃云](https://cloud.tencent.com)（需实名认证）。
2. 进入 **云开发 CloudBase** → 新建环境（选「按量计费」或「基础版」，均可长期在线）。
3. 左侧 **云托管** → **新建服务**，命名如 `cnpc-tiku`，来源选「代码仓库 / GitHub」并授权
   绑定 `fpq139909/cnpc-tiku`；或选「本地代码」稍后手动上传本 `backend/` 目录。
4. 新建**版本**：
   - 运行环境：选择 backend 目录（或上传目录）。
   - 构建方式：使用 `Dockerfile`（本目录已提供）。
   - 启动命令留空（Dockerfile 的 `CMD` 会自动 `python cnpc_app.py`）。
   - 监听端口填 `8000`（代码已监听 `0.0.0.0:PORT`，平台会注入 `PORT`）。
5. 版本配置里加**环境变量**：`GITHUB_TOKEN` = 你的 `ghp_...`（需 `repo` 权限）。
6. 部署并「设为默认流量」→ 得到固定访问地址（形如 `*.apigw.tencentcs.com`）。
7. 手机浏览器打开该地址 → 输入 rx_token → 点「检测打钩状态」或「🔄 强制更新手机端题库」
   → 约 20~40 秒后手机端题库自动更新。

> 费用：云托管按实际 CPU/内存/流量计费，空闲时几乎不计费；基础版/按量有免费额度，
> 日常个人使用成本极低甚至为 0，且**不休眠**。

---

## B. Render（最简单，海外、付费不休眠）

1. 注册 [render.com](https://render.com)（可用 GitHub 登录）。
2. **New** → **Web Service** → 连接 GitHub 仓库 `fpq139909/cnpc-tiku`。
3. 配置：
   - **Root Directory**：`backend`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`python cnpc_app.py`
   - **Instance Type**：选 **Starter ($7/月)** 才**不休眠**；免费版会休眠。
4. **Environment** 里加 `GITHUB_TOKEN` = 你的 `ghp_...`。
5. Deploy → 得到固定 `*.onrender.com` 网址。

---

## C. Railway（简单，海外、付费常驻）

1. 注册 [railway.app](https://railway.app)（可用 GitHub 登录）。
2. **New Project** → **Deploy from GitHub repo** → 选 `fpq139909/cnpc-tiku`。
3. Railway 自动识别 `backend/Procfile`（`web: python cnpc_app.py`）。
   - 在 Project 设置里把 **Root Directory** 指定为 `backend`（或加 `railway.json`）。
4. **Variables** 里加 `GITHUB_TOKEN` = 你的 `ghp_...`。
5. Deploy → 固定 `*.up.railway.app` 网址（付费计划不休眠）。

---

## 通用注意事项
- **rx_token 随时可改**：网页里存手机浏览器本地；先锋党建登录态过期后重新粘贴即可。
- **手机端题库页无需改动**：已部署的静态站照常读取 GitHub 题库，自动反映同步结果。
- **token 安全**：`GITHUB_TOKEN` 只在平台环境变量里填一次，不进代码/仓库；如泄露，
  去 GitHub → Settings → Developer settings → Personal access tokens 撤销并重发。
- **换 GitHub token**：在平台环境变量改 `GITHUB_TOKEN` 值并重新部署一次即可。
