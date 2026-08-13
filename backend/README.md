# 党建云题目提取（云端版）· CloudStudio 工作区部署

把本地 `127.0.0.1:8000` 的全部功能（检测打钩 / 提取题目 / 推送手机端题库）搬到
CloudStudio 工作区，得到**固定外网网址**，手机随时访问、随时修改 rx_token。

> 为什么必须保留后端：党建平台「题目详情」接口 `queryTestInfo` 跨域被拦截（HTTP 403），
> 浏览器取不到题目，必须由后端代理。本目录即为这个轻后端 + 管理界面（单文件 `cnpc_app.py`）。

## 文件清单
- `cnpc_app.py`：Web 服务 + 手机自适应管理界面（rx_token 存浏览器本地，可随时改）
- `cnpc_extract.py`：题目提取（含 RSA / AES 解密）
- `requirements.txt`：依赖 `pycryptodome`
- `Procfile` / `start.sh`：启动命令
- `gh_repo.txt`：目标仓库 `fpq139909/cnpc-tiku @ main`（手机端题库来源）

> 安全：本目录**不含 GitHub token**。token 通过 CloudStudio 环境变量 `GITHUB_TOKEN` 注入
> （见下方步骤），不写进公开仓库。

## 部署步骤（CloudStudio 工作区）

1. 打开 CloudStudio，新建工作区 → **「从 Git 仓库创建」**，填入
   `https://github.com/fpq139909/cnpc-tiku`（仓库里本目录为 `backend/`）。
   等待工作区克隆完成、进入 Web IDE。
2. 在 Web IDE 终端进入后端目录：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. 配置 GitHub token（**环境变量**，不落盘）：
   - 在 CloudStudio 工作区设置里添加环境变量 `GITHUB_TOKEN`，值为你的
     `ghp_...` 个人访问令牌（需 `repo` 权限）。
   - 或在终端临时执行：`export GITHUB_TOKEN=ghp_你的token`
4. 启动服务：
   ```bash
   python cnpc_app.py
   ```
   看到「已启动：http://0.0.0.0:8000/」即成功。
5. 点击 CloudStudio 顶部 **「端口预览 / 访问」**，选择端口 `8000` → 得到**固定公网网址**。
6. 手机浏览器打开该网址 → 输入 rx_token → 点「检测打钩状态」或「🔄 强制更新手机端题库」。
   约 20~40 秒后手机端题库自动更新（无需重部署）。

## 注意事项
- 工作区长时间无操作可能**休眠**，访问链接会暂时不可用；回 Web IDE 重新 `python cnpc_app.py`
  一次即可恢复（端口预览地址通常不变）。
- rx_token 在网页随时可改（存手机浏览器本地）；先锋党建登录态过期后重新粘贴即可。
- 手机端题库页（已部署的 CloudStudio 静态站）照常读取 GitHub 题库，无需改动。
- 若要彻底不用电脑：可改用 Railway / Render 等后端托管（见 `Procfile`），但需注册账号、
  国内访问可能偏慢。
