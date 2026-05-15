/**
 * 路由守卫 - 检查用户是否已同意隐私协议
 * 注：根据设计规范V2.0，不需要隐私协议弹窗，用户直接使用即代表同意
 * 此文件保留但功能已禁用
 */
(function() {
  // 公开页面列表
  const PUBLIC_PAGES = [];  // 无需验证的页面

  function checkRouteGuard() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // 已禁用路由守卫 - 按设计规范，用户直接使用即代表同意
    // if (PUBLIC_PAGES.includes(currentPage)) { return; }
    // if (consentGiven !== 'true') { window.location.href = 'privacy-consent.html'; }
    return;
  }

  // 检查（已禁用）
  checkRouteGuard();

  // 监听路由变化（已禁用）
  // window.addEventListener('popstate', checkRouteGuard);
})();
