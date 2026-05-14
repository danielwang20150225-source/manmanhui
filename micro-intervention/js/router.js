/**
 * 路由守卫 - 检查用户是否已同意隐私协议
 */
(function() {
  const PUBLIC_PAGES = ['privacy-consent.html'];
  
  function checkRouteGuard() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    // 如果是公开页面，放行
    if (PUBLIC_PAGES.includes(currentPage)) {
      return;
    }
    
    // 检查是否已同意隐私协议
    const consentGiven = localStorage.getItem('consent_given');
    if (consentGiven !== 'true') {
      // 未同意，跳转到隐私协议页
      window.location.href = 'privacy-consent.html';
    }
  }
  
  // 页面加载时检查
  checkRouteGuard();
  
  // 监听路由变化（支持浏览器前进后退）
  window.addEventListener('popstate', checkRouteGuard);
})();
