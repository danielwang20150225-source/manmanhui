/**
 * API 基础路径工具函数
 * 处理 file:// 和 http:// 协议的 API 调用
 */

// 获取完整的 API 基础路径
function getApiBase() {
  if (window.location.protocol === 'file:') {
    return 'http://localhost:8000';
  }
  return '';
}

// 暴露到全局
window.getApiBase = getApiBase;