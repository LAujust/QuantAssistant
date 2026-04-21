# AKShare 网络连接异常及代理错误解决方案

## 问题描述

用户在使用 `akshare` 库获取数据时，经常遇到以下两类错误：

1. **网络连接异常**：`网络连接异常，请检查网络后重试`

1. **代理错误**：`HTTPSConnectionPool(host='push2his.eastmoney.com', port=443): Max retries exceeded with url: ... (Caused by ProxyError('Unable to connect to proxy', RemoteDisconnected('Remote end closed connection without response')))`

这些错误通常指向网络连接问题，特别是当系统中存在不正确或不必要的代理配置时，`akshare` 内部使用的 `requests` 库可能无法正确连接到数据源。

## 错误原因分析

`akshare` 库底层依赖 `requests` 库进行网络请求。当系统或环境中配置了代理服务器时，`requests` 会尝试通过这些代理进行连接。如果代理服务器配置不正确、不可用，或者目标网站（如东方财富的 `push2his.eastmoney.com`）不需要通过代理访问，就会导致 `ProxyError`。`RemoteDisconnected` 错误通常表示远程服务器在完成响应之前关闭了连接，这可能是代理问题、网络不稳定或服务器端问题导致的。

## 解决方案

针对上述问题，主要解决方案是确保 `akshare` 在进行网络请求时能够直接连接到数据源，避免不必要的代理干扰。以下是几种推荐的修复方法：

### 1. 禁用环境变量中的代理设置（推荐）

这是最常见且有效的解决方案。如果您的系统或开发环境中设置了 `HTTP_PROXY`、`HTTPS_PROXY`、`http_proxy`、`https_proxy` 等环境变量 ，并且这些代理不是 `akshare` 访问国内数据源所必需的，那么禁用它们可以解决问题。

**操作步骤：**

- **临时禁用（当前会话有效）：**

   在运行 `akshare` 脚本的终端中执行以下命令：

   ```bash
   unset HTTP_PROXY
   unset HTTPS_PROXY
   unset http_proxy
   unset https_proxy
   ```

- **在 Python 代码中禁用（推荐用于脚本 ）：**

   在 `akshare` 相关的 Python 脚本开头添加以下代码，确保在执行任何 `akshare` 或 `requests` 请求之前执行：

   ```python
   import os
   
   # 彻底移除代理环境变量
   os.environ.pop('HTTP_PROXY', None)
   os.environ.pop('HTTPS_PROXY', None)
   os.environ.pop('http_proxy', None )
   os.environ.pop('https_proxy', None )
   
   # 可选：如果需要通过代理访问某些国外服务，但国内服务直连，可以使用 NO_PROXY
   # os.environ['NO_PROXY'] = "eastmoney.com,sina.com.cn,127.0.0.1,localhost"
   ```

   **示例代码 (****`akshare_no_proxy_demo.py`****)：**

   ```python
   import os
   import akshare as ak
   
   def setup_no_proxy():
       """在代码中强制禁用代理"""
       print("Setting up NO_PROXY environment...")
       os.environ.pop('HTTP_PROXY', None)
       os.environ.pop('HTTPS_PROXY', None)
       os.environ.pop('http_proxy', None )
       os.environ.pop('https_proxy', None )
       # 针对特定域名禁用代理，确保国内数据源直连
       os.environ['NO_PROXY'] = "eastmoney.com,sina.com.cn,127.0.0.1,localhost"
   
   if __name__ == "__main__":
       # 模拟用户环境：假设存在一个错误的代理
       os.environ['HTTP_PROXY'] = "http://invalid-proxy:8888"
       os.environ['HTTPS_PROXY'] = "http://invalid-proxy:8888"
       
       print("Current state: Proxy is set to invalid address." )
       
       # 应用修复
       setup_no_proxy()
       
       # 尝试获取数据
       print("\nTesting AKShare after proxy cleanup...")
       try:
           # 使用一个常见的 AKShare 接口进行测试
           df = ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20230101", end_date="20230131")
           print("Success! Data retrieved.")
           print(df.head())
       except Exception as e:
           print(f"Failed to retrieve data: {type(e).__name__}: {e}")
   ```

### 2. 检查网络连接和防火墙

确保您的设备能够正常访问互联网，并且没有防火墙或安全软件阻止 `akshare` 的网络请求。可以尝试 `ping push2his.eastmoney.com` 来检查连通性。

### 3. 增加请求超时和重试机制

虽然 `akshare` 内部通常会处理这些，但如果网络环境不稳定，可以考虑在 `requests` 层面增加超时和重试。这对于 `akshare` 用户来说，通常意味着需要等待 `akshare` 库的更新或在自定义请求时使用。

### 4. 检查 `akshare` 版本

确保您使用的是最新版本的 `akshare`。开发者会不断修复 bug 并优化网络请求逻辑。可以通过 `pip install --upgrade akshare` 进行更新。

## 总结

`ProxyError` 和 `RemoteDisconnected` 错误在使用 `akshare` 时，最常见的原因是系统或环境中存在不正确的代理配置。通过在 Python 代码中彻底移除代理环境变量，可以有效地解决这类问题，确保 `akshare` 能够直连数据源。如果问题依然存在，则需要进一步检查网络环境和 `akshare` 的版本。

## 参考文献

- [1] [东财接口异常· Issue #7069 · akfamily/akshare - GitHub](https://github.com/akfamily/akshare/issues/7069)

- [2] [使用Akshare获取数据时出现urllib3.exceptions.MaxRetryError如何 ... - CSDN](https://ask.csdn.net/questions/8364955)

- [3] [AKShare获取数据时频繁报错“ConnectionError”如何解决？ - CSDN](https://ask.csdn.net/questions/9344567)

- [4] [TradingAgents-CN/.env.example at main - GitHub](https://github.com/hsliuping/TradingAgents-CN/blob/main/.env.example)

- [5] [Stock MCP Server - LobeHub](https://lobehub.com/zh/mcp/yourusername-stock-mcp-server)