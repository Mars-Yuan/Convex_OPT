# OPT Convex Strategy Dashboard (V5.3 / V3 Hybrid)

<p align="center">
   <img src="https://img.shields.io/badge/version-V5.3-orange" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/streamlit-1.28%2B-red" alt="Streamlit Version">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

## 📖 项目简介

OPT Convex Strategy Dashboard 是一个基于 **OPT Convex 单标的仓位控制框架** 的可视化仪表板，当前版本为 **V5.3 / V3 Hybrid**。系统通过 Streamlit 构建，使用 Yahoo Finance 数据源，对单一标的执行趋势滤波、状态诊断、目标仓位求解与回测展示。

### 核心功能

- 🎯 **V3 Hybrid 单标的回测**: 面向单一股票或 ETF 的正式区间回测与预热扩展
- 📊 **OPT Convex 仓位求解**: 基于 alpha、alpha_accel、状态分数与波动率生成目标仓位
- 📈 **趋势与均线可视化**: 展示 Close、EMA 21、EMA 60、L1 Trend、目标仓位，并与 ADX 共用时间轴对齐
- 🔔 **交易明细展示**: 直观显示每次调仓的方向、状态、当日仓位与仓位变化
- 📉 **风险指标监控**: Sharpe Ratio、最大回撤、年化波动率等

## 🖥️ 系统要求

### 最低要求
- **操作系统**: macOS 10.15+ / Windows 10+
- **Python**: 3.9 或更高版本
- **内存**: 4GB RAM
- **存储**: 500MB 可用空间
- **网络**: 需要互联网连接（用于获取行情数据）

### 推荐配置
- **Python**: 3.10+
- **内存**: 8GB RAM
- **浏览器**: Chrome、Firefox、Edge（最新版本）

## 🚀 快速开始

### ⚡ 一键下载安装（推荐）

无需手动下载，一条命令完成所有安装步骤：

#### macOS
```bash
# 打开终端，复制粘贴以下命令:
curl -fsSL https://raw.githubusercontent.com/Mars-Yuan/Convex_OPT/main/scripts/quick_install_mac.sh | bash
```

#### Windows
```powershell
# 以管理员身份打开 PowerShell，复制粘贴以下命令:
irm https://raw.githubusercontent.com/Mars-Yuan/Convex_OPT/main/scripts/quick_install_windows.ps1 | iex
```

> 💡 **提示**: 若 `irm` 被网络策略拦截，可改用：
> `curl.exe -L "https://raw.githubusercontent.com/Mars-Yuan/Convex_OPT/main/scripts/quick_install_windows.ps1" -o "$env:TEMP\quick_install_windows.ps1"; powershell -NoProfile -ExecutionPolicy Bypass -File "$env:TEMP\quick_install_windows.ps1"`

### 🆙 Windows 升级指引

适用于已安装旧版本并希望升级到最新版本的 Windows 用户：

```powershell
# 以管理员身份运行 PowerShell:
$url = "https://raw.githubusercontent.com/Mars-Yuan/Convex_OPT/main/scripts/upgrade_windows.ps1"
$code = (Invoke-WebRequest -Uri $url -UseBasicParsing).Content
& ([ScriptBlock]::Create($code))
```

如提示权限不足，请以“管理员身份运行 PowerShell”后重试。

### 🌐 访问地址

安装完成后，程序会立即在后台启动一次，并注册为 Windows 开机后台自启动，但不会自动打开浏览器。请手动访问：

```
http://localhost:8501
```

> 📌 **注意**: 服务默认运行在本地 8501 端口，仅本机可访问。

---

### 📦 使用 GitHub Actions 发布/安装软件包（GitHub Packages）

本项目已配置 GitHub Actions，在 `main` 分支推送或手动触发后，会将该目录打包为 Docker 镜像并发布到 GitHub Packages（`ghcr.io`）。

工作流文件：

```
.github/workflows/publish-streamlit-package.yml
```

镜像地址（默认）：

```
ghcr.io/mars-yuan/ocm-trade-strategy-streamlit:latest
```

安装（拉取）并运行：

```bash
# 1) 登录 ghcr（使用 GitHub 用户名 + Personal Access Token）
echo <YOUR_GITHUB_TOKEN> | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin

# 2) 拉取镜像
docker pull ghcr.io/mars-yuan/ocm-trade-strategy-streamlit:latest

# 3) 运行容器
docker run --rm -p 8501:8501 ghcr.io/mars-yuan/ocm-trade-strategy-streamlit:latest
```

浏览器访问：

```
http://localhost:8501
```

> 说明：若仓库包权限为私有，请确保 token 具备 `read:packages`（安装）和 `write:packages`（发布）权限。

---

### 本地安装（已下载仓库）

#### macOS
```bash
chmod +x scripts/install_mac.sh
./scripts/install_mac.sh
```

#### Windows
```powershell
# 以管理员身份运行 PowerShell
.\scripts\install_windows.ps1
```

### 手动安装

1. **克隆仓库**
```bash
git clone https://github.com/Mars-Yuan/Convex_OPT.git
cd Convex_OPT
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\Activate.ps1  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行应用**
```bash
streamlit run ocm_streamlit_Streamlit.py
```

## 📁 项目结构

```
Convex_OPT/
├── ocm_streamlit_Streamlit.py   # 主应用程序
├── Streamlit_data.json          # 策略数据文件
├── requirements.txt             # Python 依赖
├── README.md                    # 项目文档
├── LICENSE                      # 许可证
├── .gitignore                   # Git 忽略文件
└── scripts/                     # 脚本目录
    ├── quick_install_mac.sh     # macOS 一键下载安装（推荐）
    ├── quick_install_windows.ps1# Windows 一键下载安装（推荐）
    ├── install_mac.sh           # macOS 本地安装
    ├── install_windows.ps1      # Windows 本地安装
    ├── start_mac.sh             # macOS 启动脚本
    ├── start_windows.ps1        # Windows 启动脚本
    ├── stop_mac.sh              # macOS 停止脚本
    ├── stop_windows.ps1         # Windows 停止脚本
    ├── uninstall_mac.sh         # macOS 卸载脚本
    ├── uninstall_windows.ps1    # Windows 卸载脚本
    ├── upgrade_mac.sh           # macOS 升级脚本
    └── upgrade_windows.ps1      # Windows 升级脚本
```

## 🔧 脚本使用说明

### 安装脚本 (一键安装 + 开机后台自启动)
安装脚本会自动完成以下操作：
1. 检测并安装 Python（如未安装）
2. 创建 Python 虚拟环境
3. 安装所有依赖包
4. 配置 Windows 开机后台自启动
5. 安装完成后立即启动一次后台服务
6. 不在安装过程中自动打开浏览器

```bash
# macOS
./scripts/install_mac.sh

# Windows (管理员权限 PowerShell)
.\scripts\install_windows.ps1
```

### 启动/停止脚本
```bash
# macOS
~/.convex_opt/scripts/start_mac.sh   # 启动后台服务
~/.convex_opt/scripts/stop_mac.sh    # 停止后台服务
```

```powershell
# Windows (PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\start_windows.ps1"   # 启动
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\stop_windows.ps1"    # 停止
```

Windows 安装完成后会注册开机触发的计划任务，运行账户为 SYSTEM。系统开机后即使没有用户登录，程序也会在后台启动；安装完成后也会立即启动一次，但需要手动访问 http://localhost:8501。

### 升级脚本
```bash
# macOS
~/.convex_opt/scripts/upgrade_mac.sh

# Windows (PowerShell)
$url = "https://raw.githubusercontent.com/Mars-Yuan/Convex_OPT/main/scripts/upgrade_windows.ps1"
$code = (Invoke-WebRequest -Uri $url -UseBasicParsing).Content
& ([ScriptBlock]::Create($code))
```

### 卸载脚本
```bash
# macOS
~/.convex_opt/scripts/uninstall_mac.sh
```

```powershell
# Windows (管理员权限 PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\uninstall_windows.ps1"
```

## 📊 使用说明

### 仪表板功能

1. **策略信息配置**
   - 输入股票代码（支持 A股: 600519.SS, 美股: AAPL 等）
   - 选择回测起止日期

2. **策略表现概览**
   - 查看 V5.3 / V3 Hybrid vs 买入持有基准的核心指标对比
   - 总收益率、年化收益、Sharpe Ratio、最大回撤

3. **价格·趋势·仓位·ADX 联动图**
   - 展示 Close、EMA 21、EMA 60、L1 Trend、目标仓位与 ADX 指标
   - 价格区与 ADX 区共享日期轴，缩放与悬停同步

4. **累计收益曲线**
   - 对比 OPT Convex 策略与买入持有基准

5. **交易明细**
   - 查看调仓日期、交易方向、市场状态与仓位变化

6. **ADX 指标**
   - 在联动子图中展示 PDI2、MDI2、ADX 和 Buy Signal

### 数据源说明

- 行情数据来源: [Yahoo Finance](https://finance.yahoo.com/)
- 数据更新频率: 每次刷新页面时实时获取
- 支持市场: 美股、港股、A股（通过后缀，如 .SS, .SZ, .HK）

## ⚙️ 后台运行机制

### macOS
- 使用 `launchd` 服务管理器
- 服务配置文件: `~/Library/LaunchAgents/com.marsyuan.convexopt.plist`
- 日志位置: `~/.convex_opt/logs/`

### Windows
- 使用 Windows 任务计划程序
- 任务名称: `Convex_OPT`
- 日志位置: `%USERPROFILE%\.convex_opt\logs\`

## 🐛 故障排除

### 常见问题

**Q: 端口被占用？**
```bash
# 查看端口占用
lsof -i :8501  # macOS
netstat -ano | findstr :8501  # Windows

# macOS - 停止服务后重新启动
~/.convex_opt/scripts/stop_mac.sh && ~/.convex_opt/scripts/start_mac.sh
```

```powershell
# Windows (PowerShell)
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\stop_windows.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\start_windows.ps1"
```

**Q: PowerShell 提示 "running scripts is disabled on this system" （脚本被禁止执行）？**

这是 Windows 默认安全策略限制。最新版脚本已自动处理此问题。如仍遇到，请使用以下命令启动：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.convex_opt\scripts\start_windows.ps1"
```

或者一次性放开当前用户的执行策略：
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
```

**Q: 无法获取行情数据？**
- 检查网络连接
- 确认股票代码格式正确
- 检查 Yahoo Finance 服务可用性

**Q: 开机自启动未生效？**
```bash
# macOS - 检查 launchd 服务状态
launchctl list | grep ocm

# Windows - 检查任务计划程序
schtasks /query /tn "Convex_OPT"
```

**Q: 虚拟环境问题？**
```bash
# macOS - 重新创建虚拟环境
cd ~/.convex_opt
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```powershell
# Windows (PowerShell) - 重新创建虚拟环境
cd $env:USERPROFILE\.convex_opt
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📝 更新日志

### V5.3 (当前版本)
- 主策略说明升级为 OPT Convex 策略 V5.3
- 价格·趋势·仓位 图显示日期坐标，并继续与 ADX 图共享日期轴严格对齐
- 文档与页面文案统一为 V5.3 / V3 Hybrid 版本说明

### V5.1
- 主策略说明升级为 OPT Convex 策略 V5.1
- 价格·趋势·仓位 与 ADX 图表合并为共享日期轴的联动子图
- 交易明细表移除“前一日实际仓位”列，仅保留当日仓位与仓位变化
- 文档与页面文案统一为 V5.1 / V3 Hybrid 版本说明

### V5.0
- 主策略说明升级为 OPT Convex 策略 V5.0
- Streamlit 页面切换为单标的 V3 Hybrid 展示逻辑
- 文档与页面文案统一为 V5.0 / V3 Hybrid 版本说明
- 图表调整为价格、趋势、仓位、ADX 与交易明细结构

### v2.6
- 新增「权重随时间变化图」（堆叠面积图），替代原有的「各周期收益率热力图」
- 权重图显示全部再平衡记录（从开始日期到结束日期的所有记录）
- 优化滚动回测参数：LOOKBACK_DAYS=20, REBALANCE_DAYS=5, MIN_LOOKBACK=15
- 权重历史记录改为保存全部再平衡记录（不再截断）
- 再平衡记录表格显示数量从 10 条增加到 30 条
- 修复短期回测时 weights_history 为空的问题

### v2.5
- 新增滚动回测模式（Rolling Backtest），更接近实盘表现
- 支持自定义回看窗口、再平衡周期、最小回看天数
- 可视化对比：滚动回测 vs 固定权重 vs 等权组合 vs 买入持有
- 新增再平衡权重历史记录与展示

### v2.4
- 新增 Windows 一键升级命令（含脚本存在性检测、自动 Unblock、执行策略兼容）
- 优化 Windows 升级流程的可复制性，降低 PowerShell 执行策略报错概率
- 统一安装后命令提示与 README 升级命令，减少文档与脚本使用差异

### v2.3
- 新增多周期 OCM 策略回测
- 支持 Markowitz 均值-方差优化
- 实时 Yahoo Finance 数据接口
- 交互式 Plotly 图表

### v2.0
- 重构为 Streamlit 架构
- 添加动态日期选择功能

### v1.0
- 初始版本发布

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📬 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [GitHub Issue](https://github.com/Mars-Yuan/Convex_OPT/issues)

---

<p align="center">
  Made with ❤️ by OCM Team
</p>
