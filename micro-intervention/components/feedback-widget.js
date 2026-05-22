/**
 * 用户意见反馈悬浮球组件
 * 用法：<script src="components/feedback-widget.js"></script>
 * 或在页面底部添加：<div id="feedback-widget"></div><script src="components/feedback-widget.js"></script>
 */

(function() {
  'use strict';

  // ============================================================
  // 页面名称映射（英文 → 中文）
  // ============================================================
  const PAGE_NAME_MAP = {
    'index.html': '首页',
    'input.html': '情境输入',
    'package.html': '任务包确认',
    'training.html': '每日训练',
    'feedback.html': '训练反馈',
    'progress.html': '训练进度',
    'history.html': '训练历史',
    'practice.html': '孩子练习',
    'me.html': '个人中心',
    'about.html': '关于微干预',
    'settings.html': '设置',
    'child-profile.html': '孩子信息',
    'welcome.html': '欢迎页',
    'loading.html': '加载中'
  };

  // ============================================================
  // 用户身份生成（IP + UUID 组合）
  // ============================================================
  function getUserIdentifier() {
    // 优先使用 localStorage 中的 UUID
    let uuid = localStorage.getItem('feedback_uuid');
    if (!uuid) {
      uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
      localStorage.setItem('feedback_uuid', uuid);
    }
    return 'uuid:' + uuid; // 完整标识由后端拼接IP
  }

  // ============================================================
  // 获取当前页面中文名称
  // ============================================================
  function getCurrentPageName() {
    const path = window.location.pathname.split('/').pop() || 'index.html';
    return PAGE_NAME_MAP[path] || path;
  }

  // ============================================================
  // 图片压缩工具
  // ============================================================
  function compressImage(file, maxSizeMB = 4, quality = 0.8) {
    return new Promise((resolve, reject) => {
      const maxSize = maxSizeMB * 1024 * 1024;

      // 如果文件已经小于限制，直接返回
      if (file.size <= maxSize) {
        resolve(file);
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          // 计算压缩后的尺寸
          let width = img.width;
          let height = img.height;
          const aspectRatio = width / height;

          // 如果尺寸过大，等比缩放
          const maxDimension = 1920;
          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              width = maxDimension;
              height = Math.round(width / aspectRatio);
            } else {
              height = maxDimension;
              width = Math.round(height * aspectRatio);
            }
          }

          // 创建 canvas 进行压缩
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // 逐步降低质量直到文件小于限制
          let currentQuality = quality;
          const tryCompress = () => {
            canvas.toBlob((blob) => {
              if (blob.size <= maxSize || currentQuality <= 0.1) {
                resolve(new File([blob], file.name, { type: file.type }));
              } else {
                currentQuality -= 0.1;
                tryCompress();
              }
            }, file.type, currentQuality);
          };
          tryCompress();
        };
        img.onerror = reject;
        img.src = e.target.result;
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  // ============================================================
  // 悬浮球组件样式
  // ============================================================
  const WIDGET_STYLES = `
    /* 悬浮球容器 */
    .feedback-widget {
      position: fixed;
      bottom: 100px;
      right: 16px;
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }

    /* 悬浮球按钮 */
    .feedback-fab {
      width: 52px;
      height: 52px;
      background: linear-gradient(135deg, #34C759 0%, #2DBE48 100%);
      border-radius: 16px;
      box-shadow: 0 4px 20px rgba(52, 199, 89, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      position: relative;
    }

    .feedback-fab:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(52, 199, 89, 0.5);
    }

    .feedback-fab:active {
      transform: scale(0.95);
    }

    .feedback-fab .icon {
      font-size: 24px;
      transition: transform 0.3s ease;
    }

    .feedback-fab .icon-hint {
      position: absolute;
      top: -8px;
      right: -8px;
      width: 18px;
      height: 18px;
      background: #FF3B30;
      border-radius: 50%;
      font-size: 11px;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
      opacity: 0;
      transform: scale(0);
      transition: all 0.2s ease;
    }

    .feedback-fab.has-content .icon-hint {
      opacity: 1;
      transform: scale(1);
    }

    /* 展开状态 */
    .feedback-fab.expanded {
      background: #6B6B6B;
      box-shadow: 0 4px 20px rgba(107, 107, 107, 0.4);
    }

    .feedback-fab.expanded:hover {
      background: #5B5B5B;
      box-shadow: 0 6px 28px rgba(107, 107, 107, 0.5);
    }

    .feedback-fab.expanded .icon-close {
      transform: rotate(0deg);
    }

    /* 反馈面板 */
    .feedback-panel {
      position: absolute;
      bottom: 64px;
      right: 0;
      width: 320px;
      background: #FFFFFF;
      border-radius: 20px;
      box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
      overflow: hidden;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .feedback-panel.visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }

    /* 面板头部 */
    .feedback-panel-header {
      background: linear-gradient(135deg, #34C759 0%, #2DBE48 100%);
      padding: 20px 20px 24px;
      color: white;
    }

    .feedback-panel-title {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .feedback-panel-title .emoji {
      font-size: 20px;
    }

    .feedback-panel-subtitle {
      font-size: 13px;
      opacity: 0.9;
    }

    .feedback-page-tag {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: rgba(255, 255, 255, 0.25);
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      margin-top: 10px;
    }

    /* 面板内容 */
    .feedback-panel-body {
      padding: 20px;
    }

    /* 文字输入 */
    .feedback-textarea-wrapper {
      position: relative;
      margin-bottom: 14px;
    }

    .feedback-textarea {
      width: 100%;
      min-height: 120px;
      background: #F7F4F0;
      border: 2px solid transparent;
      border-radius: 14px;
      padding: 14px;
      font-size: 15px;
      font-family: inherit;
      color: #2D2D2D;
      line-height: 1.6;
      resize: none;
      outline: none;
      transition: all 0.2s ease;
    }

    .feedback-textarea::placeholder {
      color: #ADADAD;
    }

    .feedback-textarea:focus {
      border-color: #34C759;
      background: #FFFFFF;
    }

    .feedback-char-count {
      position: absolute;
      bottom: 10px;
      right: 14px;
      font-size: 11px;
      color: #ADADAD;
    }

    /* 图片上传 */
    .feedback-image-section {
      margin-bottom: 16px;
    }

    .feedback-image-label {
      font-size: 12px;
      color: #6B6B6B;
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .feedback-image-preview {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }

    .feedback-image-item {
      position: relative;
      width: 72px;
      height: 72px;
      border-radius: 10px;
      overflow: hidden;
      background: #F7F4F0;
    }

    .feedback-image-item img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .feedback-image-item .remove-btn {
      position: absolute;
      top: 4px;
      right: 4px;
      width: 20px;
      height: 20px;
      background: rgba(0, 0, 0, 0.6);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      color: white;
      cursor: pointer;
    }

    .feedback-upload-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #F7F4F0;
      border: 2px dashed #E8E4E0;
      border-radius: 10px;
      padding: 10px 16px;
      font-size: 13px;
      color: #6B6B6B;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .feedback-upload-btn:hover {
      border-color: #34C759;
      color: #34C759;
      background: #E8F5E9;
    }

    .feedback-upload-btn input {
      display: none;
    }

    /* 提交按钮 */
    .feedback-submit-btn {
      width: 100%;
      background: linear-gradient(135deg, #34C759 0%, #2DBE48 100%);
      color: white;
      border: none;
      border-radius: 14px;
      padding: 14px;
      font-size: 15px;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(52, 199, 89, 0.35);
      transition: all 0.2s ease;
    }

    .feedback-submit-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(52, 199, 89, 0.45);
    }

    .feedback-submit-btn:active {
      transform: translateY(0);
    }

    .feedback-submit-btn:disabled {
      background: #E0E0E0;
      box-shadow: none;
      cursor: not-allowed;
    }

    /* 加载状态 */
    .feedback-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .feedback-spinner {
      width: 18px;
      height: 18px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: feedback-spin 0.8s linear infinite;
    }

    @keyframes feedback-spin {
      to { transform: rotate(360deg); }
    }

    /* 成功状态 */
    .feedback-success {
      text-align: center;
      padding: 40px 20px;
    }

    .feedback-success-icon {
      width: 64px;
      height: 64px;
      background: #E8F5E9;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 32px;
      margin: 0 auto 16px;
    }

    .feedback-success-title {
      font-size: 18px;
      font-weight: 600;
      color: #2D2D2D;
      margin-bottom: 6px;
    }

    .feedback-success-desc {
      font-size: 13px;
      color: #6B6B6B;
    }

    /* 错误提示 */
    .feedback-error {
      background: #FFEBEE;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 13px;
      color: #E57373;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `;

  // ============================================================
  // 组件 HTML 模板
  // ============================================================
  function createWidgetHTML() {
    return `
      <div class="feedback-widget">
        <!-- 悬浮球按钮 -->
        <div class="feedback-fab" id="feedbackFab">
          <span class="icon">💬</span>
        </div>

        <!-- 反馈面板 -->
        <div class="feedback-panel" id="feedbackPanel">
          <!-- 头部 -->
          <div class="feedback-panel-header">
            <div class="feedback-panel-title">
              <span class="emoji">📝</span>
              意见反馈
            </div>
            <div class="feedback-panel-subtitle">您的每一条反馈都会帮助我们做得更好</div>
            <div class="feedback-page-tag">
              <span>📍</span>
              <span id="feedbackPageName">首页</span>
            </div>
          </div>

          <!-- 内容区域 -->
          <div class="feedback-panel-body" id="feedbackBody">
            <!-- 错误提示 -->
            <div class="feedback-error" id="feedbackError" style="display: none;">
              <span>⚠️</span>
              <span id="feedbackErrorText"></span>
            </div>

            <!-- 文字输入 -->
            <div class="feedback-textarea-wrapper">
              <textarea
                class="feedback-textarea"
                id="feedbackText"
                placeholder="请描述您遇到的问题或建议..."
                maxlength="500"
              ></textarea>
              <span class="feedback-char-count"><span id="charCount">0</span>/500</span>
            </div>

            <!-- 图片上传 -->
            <div class="feedback-image-section">
              <div class="feedback-image-label">📷 添加图片（可选，帮助我们更好地理解问题）</div>
              <div class="feedback-image-preview" id="imagePreview"></div>
              <label class="feedback-upload-btn" id="uploadBtn">
                <input type="file" accept="image/*" multiple id="imageInput">
                <span>+ 添加图片</span>
              </label>
            </div>

            <!-- 提交按钮 -->
            <button class="feedback-submit-btn" id="submitBtn">
              提交反馈
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // ============================================================
  // 主组件类
  // ============================================================
  class FeedbackWidget {
    constructor() {
      this.isExpanded = false;
      this.isSubmitting = false;
      this.selectedImages = [];
      this.maxImages = 3;
      this.maxFileSize = 4 * 1024 * 1024; // 4MB

      this.init();
    }

    init() {
      // 获取 API_BASE（使用默认值避免异步问题）
      this.apiBase = (typeof API_BASE !== 'undefined') ? API_BASE : '';

      // 注入样式
      this.injectStyles();

      // 插入组件
      const container = document.createElement('div');
      container.innerHTML = createWidgetHTML();
      document.body.appendChild(container);

      // 绑定元素
      this.fab = document.getElementById('feedbackFab');
      this.panel = document.getElementById('feedbackPanel');
      this.textarea = document.getElementById('feedbackText');
      this.charCount = document.getElementById('charCount');
      this.imageInput = document.getElementById('imageInput');
      this.imagePreview = document.getElementById('imagePreview');
      this.uploadBtn = document.getElementById('uploadBtn');
      this.submitBtn = document.getElementById('submitBtn');
      this.errorEl = document.getElementById('feedbackError');
      this.errorText = document.getElementById('feedbackErrorText');
      this.pageName = document.getElementById('feedbackPageName');

      // 设置当前页面名称
      this.pageName.textContent = getCurrentPageName();

      // 绑定事件
      this.bindEvents();
    }

    injectStyles() {
      const style = document.createElement('style');
      style.textContent = WIDGET_STYLES;
      document.head.appendChild(style);
    }

    bindEvents() {
      // 点击悬浮球展开/收起
      this.fab.addEventListener('click', () => this.toggle());

      // 文字输入计数
      this.textarea.addEventListener('input', () => {
        this.charCount.textContent = this.textarea.value.length;
        this.updateFabState();
      });

      // 图片选择
      this.imageInput.addEventListener('change', (e) => this.handleImageSelect(e));

      // 提交按钮
      this.submitBtn.addEventListener('click', () => this.submit());

      // 点击外部关闭
      document.addEventListener('click', (e) => {
        if (this.isExpanded &&
            !this.panel.contains(e.target) &&
            !this.fab.contains(e.target)) {
          this.collapse();
        }
      });

      // ESC 关闭
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isExpanded) {
          this.collapse();
        }
      });
    }

    toggle() {
      if (this.isExpanded) {
        this.collapse();
      } else {
        this.expand();
      }
    }

    expand() {
      this.isExpanded = true;
      this.fab.classList.add('expanded');
      this.panel.classList.add('visible');
      this.fab.querySelector('.icon').textContent = '✕';
      setTimeout(() => this.textarea.focus(), 300);
    }

    collapse() {
      this.isExpanded = false;
      this.fab.classList.remove('expanded');
      this.panel.classList.remove('visible');
      this.fab.querySelector('.icon').textContent = '💬';
    }

    updateFabState() {
      const hasContent = this.textarea.value.trim().length > 0 || this.selectedImages.length > 0;
      this.fab.classList.toggle('has-content', hasContent);
    }

    async handleImageSelect(e) {
      const files = Array.from(e.target.files);

      if (this.selectedImages.length + files.length > this.maxImages) {
        this.showError(`最多只能上传 ${this.maxImages} 张图片`);
        return;
      }

      for (const file of files) {
        if (file.size > this.maxFileSize) {
          try {
            const compressed = await compressImage(file);
            this.addImagePreview(compressed);
          } catch (err) {
            this.showError('图片压缩失败');
          }
        } else {
          this.addImagePreview(file);
        }
      }

      // 清空 input 以支持重复选择同一图片
      this.imageInput.value = '';
      this.updateFabState();
    }

    addImagePreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const item = document.createElement('div');
        item.className = 'feedback-image-item';
        item.dataset.fileName = file.name;
        item.innerHTML = `
          <img src="${e.target.result}" alt="预览图">
          <div class="remove-btn" data-action="remove">×</div>
        `;
        item.querySelector('.remove-btn').addEventListener('click', (e) => {
          e.stopPropagation();
          this.removeImage(item, file);
        });
        this.imagePreview.appendChild(item);
        this.selectedImages.push(file);
      };
      reader.readAsDataURL(file);
    }

    removeImage(item, file) {
      item.remove();
      this.selectedImages = this.selectedImages.filter(f => f !== file);
      this.updateFabState();
    }

    showError(message) {
      this.errorText.textContent = message;
      this.errorEl.style.display = 'flex';
      setTimeout(() => {
        this.errorEl.style.display = 'none';
      }, 3000);
    }

    async submit() {
      if (this.isSubmitting) return;

      const text = this.textarea.value.trim();
      if (!text) {
        this.showError('请输入反馈内容');
        return;
      }

      this.isSubmitting = true;
      this.submitBtn.disabled = true;
      this.submitBtn.innerHTML = `
        <div class="feedback-loading">
          <div class="feedback-spinner"></div>
          <span>提交中...</span>
        </div>
      `;

      try {
        // 将图片转换为 base64
        const images = [];
        for (const file of this.selectedImages.slice(0, 3)) {
          const dataUrl = await this.fileToBase64(file);
          // 移除 data URL 前缀，只保留纯 base64
          const base64 = dataUrl.split(',')[1] || dataUrl;
          images.push(base64);
        }

        const payload = {
          user_identifier: getUserIdentifier(),
          page_source: getCurrentPageName(),
          feedback_text: text,
          images: images
        };

        // 使用 AbortController 实现超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15秒超时

        let response;
        try {
          response = await fetch(this.apiBase + '/api/feedback/suggestion', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            signal: controller.signal
          });
        } finally {
          clearTimeout(timeoutId);
        }

        if (!response.ok) {
          if (response.status >= 500) {
            throw new Error('服务器繁忙，请稍后重试');
          } else if (response.status >= 400) {
            throw new Error('请求参数有误');
          } else {
            throw new Error('提交失败，请检查网络');
          }
        }

        const result = await response.json();

        if (result.code === 0) {
          this.showSuccess();
        } else {
          throw new Error(result.message || '提交失败');
        }
      } catch (err) {
        // 区分错误类型
        if (err.name === 'AbortError') {
          this.showError('请求超时，请检查网络连接');
        } else if (err.message.includes('Failed to fetch') || err.message.includes('网络')) {
          this.showError('网络连接失败，请检查网络');
        } else {
          this.showError(err.message);
        }
      } finally {
        this.isSubmitting = false;
        this.submitBtn.disabled = false;
        this.submitBtn.textContent = '提交反馈';
      }
    }

    // 将 File 对象转换为 base64
    fileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    showSuccess() {
      this.panel.querySelector('.feedback-panel-body').innerHTML = `
        <div class="feedback-success">
          <div class="feedback-success-icon">✓</div>
          <div class="feedback-success-title">感谢您的反馈！</div>
          <div class="feedback-success-desc">我们已收到您的意见，会尽快处理</div>
        </div>
      `;

      setTimeout(() => {
        this.collapse();
        // 重置面板状态
        this.resetPanel();
      }, 2000);
    }

    resetPanel() {
      // 恢复原始面板内容
      const body = this.panel.querySelector('.feedback-panel-body');
      body.innerHTML = `
        <div class="feedback-error" id="feedbackError" style="display: none;">
          <span>⚠️</span>
          <span id="feedbackErrorText"></span>
        </div>
        <div class="feedback-textarea-wrapper">
          <textarea
            class="feedback-textarea"
            id="feedbackText"
            placeholder="请描述您遇到的问题或建议..."
            maxlength="500"
          ></textarea>
          <span class="feedback-char-count"><span id="charCount">0</span>/500</span>
        </div>
        <div class="feedback-image-section">
          <div class="feedback-image-label">📷 添加图片（可选，帮助我们更好地理解问题）</div>
          <div class="feedback-image-preview" id="imagePreview"></div>
          <label class="feedback-upload-btn" id="uploadBtn">
            <input type="file" accept="image/*" multiple id="imageInput">
            <span>+ 添加图片</span>
          </label>
        </div>
        <button class="feedback-submit-btn" id="submitBtn">
          提交反馈
        </button>
      `;

      // 重新绑定元素（带空值检查）
      this.textarea = document.getElementById('feedbackText');
      this.charCount = document.getElementById('charCount');
      this.imageInput = document.getElementById('imageInput');
      this.imagePreview = document.getElementById('imagePreview');
      this.submitBtn = document.getElementById('submitBtn');
      this.errorEl = document.getElementById('feedbackError');
      this.errorText = document.getElementById('feedbackErrorText');

      this.selectedImages = [];

      // 绑定事件（带空值检查）
      if (this.textarea) {
        this.textarea.addEventListener('input', () => {
          this.charCount.textContent = this.textarea.value.length;
          this.updateFabState();
        });
      }

      if (this.imageInput) {
        this.imageInput.addEventListener('change', (e) => this.handleImageSelect(e));
      }

      if (this.submitBtn) {
        this.submitBtn.addEventListener('click', () => this.submit());
      }
    }
  }

  // ============================================================
  // 自动初始化
  // ============================================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new FeedbackWidget());
  } else {
    new FeedbackWidget();
  }

  // 暴露给全局，方便手动控制
  window.FeedbackWidget = FeedbackWidget;
})();