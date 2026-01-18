# stop_web.bat 修复说明

## 问题诊断

### 原始问题
- `stop_web.bat` 无法正常运行
- 双击运行后窗口立即关闭，没有输出

### 根本原因
1. **批处理语法错误：** `for /f` 循环中的 `netstat` 和 `find` 命令组合不正确
2. **字符串解析失败：** netstat 输出的格式与 find 命令的匹配模式不兼容
3. **变量作用域问题：** 在批处理循环中设置的变量无法正确传递

## 解决方案

### 架构变更
采用 **批处理 + PowerShell** 混合架构：

```
stop_web.bat (批处理)
    ↓
stop_web.ps1 (PowerShell 脚本)
    ↓
执行进程停止操作
```

### 文件清单

#### 1. `stop_web.bat` (批处理文件)
**功能：**
- 调用 PowerShell 脚本
- 设置 UTF-8 编码
- 暂停以显示输出结果

**代码：**
```batch
@echo off
SETLOCAL
chcp 65001 >nul
set PYTHONUTF8=1

powershell.exe -ExecutionPolicy Bypass -File "%~dp0stop_web.ps1"

pause
ENDLOCAL
EXIT /B %ERRORLEVEL%
```

#### 2. `stop_web.ps1` (PowerShell 脚本)
**功能：**
- 查找监听端口 8000 和 8001 的进程
- 显示进程详细信息（PID、进程名、内存占用）
- 停止这些进程
- 提供清晰的操作反馈

**关键命令：**
```powershell
# 查找监听端口的进程
Get-NetTCPConnection -LocalPort 8001 | Select-Object -ExpandProperty OwningProcess

# 获取进程信息
Get-Process -Id $pid | Select-Object Id,ProcessName,WorkingSet

# 停止进程
Stop-Process -Id $pid -Force
```

#### 3. `USAGE.md` (使用说明文档)
详细的使用说明，包括：
- 快速开始指南
- 脚本功能说明
- 故障排除方案
- 技术细节

## 技术优势

### 1. 可靠性
- ✅ 使用 PowerShell 的 `Get-NetTCPConnection` 命令，比 netstat 更可靠
- ✅ 原生 PowerShell 对象处理，避免字符串解析错误
- ✅ 更好的错误处理机制

### 2. 易用性
- ✅ 清晰的输出格式
- ✅ 详细的进程信息显示
- ✅ 操作成功/失败提示

### 3. 兼容性
- ✅ 支持 Windows 10 及以上版本
- ✅ 支持 PowerShell 5.0 及以上版本
- ✅ 使用 UTF-8 编码，支持中文

### 4. 安全性
- ✅ 只终止监听特定端口的进程
- ✅ 不影响其他 Python 应用
- ✅ 透明的进程信息显示

## 测试结果

### 测试场景 1：有进程运行
```powershell
Found processes listening on the following ports:
----------------------------------------
Port 8000 PID: 8720
  Id ProcessName WorkingSet
  -- ----------- ----------
8720 KGService     20979712

Port 8001 PID: 8436
   Id ProcessName WorkingSet
   -- ----------- ----------
8436 python        59482112
----------------------------------------

Stopping processes...
[OK] Stopped process on port 8000 (PID: 8720)
[OK] Stopped process on port 8001 (PID: 8436)
```

### 测试场景 2：无进程运行
```powershell
[INFO] No process found listening on port 8000 or 8001
[INFO] Web service may not be running
```

## 使用方法

### 直接双击运行
1. 双击 `stop_web.bat`
2. 等待 PowerShell 脚本执行
3. 查看输出结果
4. 按任意键关闭窗口

### 命令行运行
```cmd
stop_web.bat
```

### PowerShell 直接运行
```powershell
powershell -ExecutionPolicy Bypass -File stop_web.ps1
```

## 故障排除

### 问题：窗口立即关闭
**原因：** 脚本执行完成，`pause` 命令等待用户输入

**解决：** 这是正常现象，按任意键关闭窗口

### 问题：PowerShell 执行策略错误
**错误信息：** `cannot be loaded because running scripts is disabled`

**解决：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题：无法停止进程
**可能原因：**
1. 进程需要管理员权限
2. 进程已被系统锁定

**解决：**
- 以管理员身份运行
- 使用任务管理器手动终止

## 文件对比

### 修复前
- 纯批处理脚本
- 使用 netstat + find 组合
- 复杂的字符串解析
- 可靠性差

### 修复后
- 批处理 + PowerShell 混合架构
- 使用 Get-NetTCPConnection
- 原生对象处理
- 高可靠性

## 相关文件

- `run_web.bat` - 启动 Web 服务
- `cleanup.bat` - 清理系统
- `init_db.py` - 初始化数据库
- `USAGE.md` - 使用说明

## 版本历史

### v2.0 (当前版本)
- ✅ 修复 stop_web.bat 无法运行的问题
- ✅ 采用 PowerShell 脚本
- ✅ 添加详细的进程信息显示
- ✅ 创建使用说明文档

### v1.0 (原始版本)
- ❌ 纯批处理实现
- ❌ 存在语法错误
- ❌ 无法正常工作

## 总结

通过采用 PowerShell 脚本替代复杂的批处理逻辑，成功修复了 `stop_web.bat` 的问题。新方案具有以下优点：

1. **高可靠性：** 使用 PowerShell 原生命令，避免字符串解析错误
2. **易用性：** 清晰的输出和详细的进程信息
3. **安全性：** 精准停止特定端口的进程
4. **可维护性：** PowerShell 脚本更易于理解和维护

修复完成日期：2026-01-18
