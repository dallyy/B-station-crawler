# cleanup.bat 数据库清理功能说明

## 功能更新

### 新增功能
为 `cleanup.bat` 添加了删除数据库内容的功能，同时保留数据库表结构。

### 核心改进
- **之前：** 直接删除整个数据库文件（`data.sqlite`）
- **现在：** 清空数据库内容，保留表结构和自增序列

## 实现方式

### 新增文件

#### 1. `clear_db.py` - 数据库清理脚本
**功能：**
- 清空 `videos` 表的所有数据
- 清空 `scrape_runs` 表的所有数据
- 重置自增序列（`sqlite_sequence`）
- 保留数据库表结构

**核心代码：**
```python
async def clear_database():
    async with aiosqlite.connect(DB_PATH) as db:
        # Clear videos table
        await db.execute("DELETE FROM videos")
        
        # Clear scrape_runs table
        await db.execute("DELETE FROM scrape_runs")
        
        # Reset auto-increment sequences
        await db.execute("DELETE FROM sqlite_sequence WHERE name IN ('videos', 'scrape_runs')")
        
        await db.commit()
```

#### 2. `cleanup.ps1` - PowerShell 清理脚本
**功能：**
- 使用 PowerShell 执行清理操作
- 调用虚拟环境中的 Python 执行 `clear_db.py`
- 提供清晰的清理进度和结果

**关键改进：**
```powershell
$venvPython = Join-Path $PROJECT_DIR "venv\Scripts\python.exe"
$result = & $venvPython $clearDbScript 2>&1
```

#### 3. `cleanup.bat` (已更新)
**功能：**
- 调用 PowerShell 清理脚本
- 设置 UTF-8 编码
- 暂停以显示输出结果

**更新内容：**
```batch
powershell.exe -ExecutionPolicy Bypass -File "%~dp0cleanup.ps1"
pause
```

## 清理步骤

cleanup.bat 执行 5 个清理步骤：

1. **清理 Python 缓存文件**
   - 删除 `src/bili_scraper/__pycache__` 目录

2. **清理日志文件**
   - 清空 `logs/` 目录中的所有 `.log` 文件

3. **清理锁文件**
   - 删除 `run.lock` 文件

4. **清理临时文件**
   - 删除所有 `.tmp` 和 `.bak` 文件

5. **清理数据库内容** ⭐ 新增
   - 清空 `videos` 表
   - 清空 `scrape_runs` 表
   - 重置自增序列
   - 保留数据库表结构

## 使用方法

### 双击运行
1. 双击 `cleanup.bat`
2. 等待清理完成
3. 查看清理结果
4. 按任意键关闭窗口

### 命令行运行
```cmd
cleanup.bat
```

### PowerShell 直接运行
```powershell
powershell -ExecutionPolicy Bypass -File cleanup.ps1
```

### 仅清理数据库
```cmd
venv\Scripts\python.exe clear_db.py
```

## 执行结果示例

```
========================================
      Bili Scraper - Cleanup Tool
========================================

Performing cleanup operations...

[1/5] Cleaning Python cache files...
[OK] Deleted __pycache__ directory
[2/5] Cleaning log files...
[OK] Cleared logs directory
[3/5] Cleaning lock file...
[OK] Deleted lock file
[4/5] Cleaning temporary files...
[OK] Cleaned temporary files
[5/5] Clearing database content...
[OK] Cleared database content

========================================
      Cleanup Complete
========================================

Cleaned items:
  - Python cache files
  - Log files
  - Lock file
  - Temporary files
  - Database content

Note: Database structure is preserved. To reuse, run scraper first.
```

## 数据库清理详情

### clear_db.py 输出示例
```
INFO:__main__:Clearing database content...
INFO:__main__:Database cleared successfully:
INFO:__main__:  - Deleted 41 videos
INFO:__main__:  - Deleted 2 scrape runs
INFO:__main__:  - Reset auto-increment sequences
```

### 数据库状态验证

清理前：
```sql
SELECT COUNT(*) FROM videos;          -- 41
SELECT COUNT(*) FROM scrape_runs;      -- 2
```

清理后：
```sql
SELECT COUNT(*) FROM videos;          -- 0
SELECT COUNT(*) FROM scrape_runs;      -- 0
```

表结构保留：
- ✅ `videos` 表结构完整
- ✅ `scrape_runs` 表结构完整
- ✅ `sqlite_sequence` 表存在（但已清空）

## 技术优势

### 1. 数据结构保留
- **之前：** 删除整个数据库文件，需要重新初始化
- **现在：** 保留表结构，Web 服务可直接使用

### 2. 性能优化
- 不需要重新创建表结构
- 下次启动时无需初始化数据库
- 自增序列已重置，从 1 开始

### 3. 安全性
- 使用虚拟环境的 Python 执行
- 详细的错误处理和日志
- 如果清空失败，自动降级为删除文件

### 4. 可靠性
- PowerShell 脚本比批处理更可靠
- 使用 `venv\Scripts\python.exe` 确保环境正确
- 完整的错误处理机制

## 文件对比

### 修改前
```
cleanup.bat (纯批处理）
  └─ del data.sqlite  # 删除整个文件
```

### 修改后
```
cleanup.bat
  └─ cleanup.ps1 (PowerShell)
       └─ venv\Scripts\python.exe
            └─ clear_db.py (Python）
                 ├─ DELETE FROM videos
                 ├─ DELETE FROM scrape_runs
                 └─ DELETE FROM sqlite_sequence
```

## 故障排除

### 问题：数据库清理失败
**错误信息：**
```
[WARN] Failed to clear database, trying to delete file
```

**可能原因：**
1. 数据库文件被锁定（Web 服务正在运行）
2. 数据库文件损坏
3. 虚拟环境 Python 路径错误

**解决方法：**
1. 先运行 `stop_web.bat` 停止 Web 服务
2. 然后重新运行 `cleanup.bat`

### 问题：找不到虚拟环境
**错误信息：**
```
[WARN] Virtual environment Python not found, skipping database cleanup
```

**解决方法：**
1. 检查 `venv/Scripts/python.exe` 是否存在
2. 如果不存在，重新创建虚拟环境：
   ```cmd
   python -m venv venv
   venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

### 问题：清理后 Web 服务报错
**可能原因：**
- 数据库表结构被意外删除

**解决方法：**
运行 `init_db.py` 重新初始化数据库：
```cmd
venv\Scripts\python.exe init_db.py
```

## 注意事项

### 数据备份
- 清理操作不可撤销
- 建议在清理前备份数据库文件：
  ```cmd
  copy data.sqlite data.sqlite.backup
  ```

### 运行时清理
- 不建议在 Web 服务运行时清理数据库
- 可能导致数据不一致或错误
- 建议先停止服务，再执行清理

### 权限要求
- 需要对项目目录的读写权限
- 需要对数据库文件的读写权限
- 建议以管理员身份运行

## 相关脚本

| 脚本 | 功能 | 调用方式 |
|------|------|---------|
| `cleanup.bat` | 完整清理（包括数据库）| 双击或命令行 |
| `cleanup.ps1` | PowerShell 清理核心 | 被 cleanup.bat 调用 |
| `clear_db.py` | 仅清理数据库内容 | `venv\Scripts\python.exe clear_db.py` |
| `init_db.py` | 初始化数据库表结构 | `venv\Scripts\python.exe init_db.py` |
| `stop_web.bat` | 停止 Web 服务 | 双击或命令行 |

## 版本历史

### v2.0 (当前版本)
- ✅ 添加数据库内容清理功能
- ✅ 保留数据库表结构
- ✅ 重置自增序列
- ✅ 使用 PowerShell 脚本替代纯批处理
- ✅ 支持虚拟环境 Python

### v1.0 (原始版本)
- ❌ 直接删除数据库文件
- ❌ 纯批处理实现
- ❌ 丢失表结构

## 总结

通过添加 `clear_db.py` 脚本和更新 `cleanup.bat`，实现了以下改进：

1. **功能增强：** 可以清空数据库内容而不删除文件
2. **性能优化：** 保留表结构，无需重新初始化
3. **可靠性：** 使用 PowerShell + Python 混合架构
4. **易用性：** 清晰的输出和错误处理

清理功能更新完成日期：2026-01-18
