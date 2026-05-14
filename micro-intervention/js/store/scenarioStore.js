/**
 * 情境状态管理
 * 管理首页情境列表的状态
 */
const scenarioStore = {
  // 状态
  state: {
    scenarios: [],
    loading: false,
    error: null
  },
  
  // 监听器列表
  listeners: [],

  // 获取情境列表
  async fetchScenarios() {
    this.state.loading = true;
    this.state.error = null;
    this.notify();

    try {
      const response = await fetch(`${getApiBase()}/api/scenarios`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const data = await response.json();
      // API返回格式: {code: 0, message: "ok", data: {scenarios: [], ...}}
      const raw = (data.data && data.data.scenarios) ? data.data.scenarios : [];
      // 字段映射: API返回package_name/title，模板期望scenario_title/scenario_emoji
      this.state.scenarios = raw.map(s => ({
        ...s,
        scenario_id: s.id || s.scenario_id,
        scenario_title: s.package_name || s.title || s.scenario_title || '未命名情境',
        scenario_emoji: s.emoji || s.package_emoji || this._guessEmoji(s.package_name || s.title || ''),
        total_days: s.total_days || (s.days_data && Array.isArray(s.days_data.days) ? s.days_data.days.length : 14),
      }));
      this.state.loading = false;
      // 注意：不再设置error，即使没有数据也显示空状态
      this.notify();

      return this.state.scenarios;
    } catch (error) {
      console.error('获取情境列表失败:', error);
      // 区分网络错误和其他错误
      if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
        this.state.error = 'server_offline';  // 特殊标记：后端未启动
      } else {
        this.state.error = error.message;
      }
      this.state.loading = false;
      this.notify();
      return [];
    }
  },
  
  // 添加监听器
  subscribe(listener) {
    this.listeners.push(listener);
    // 返回取消订阅函数
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  },
  
  // 根据情境名称推断 emoji
  _guessEmoji(name) {
    const map = {
      '地铁': '🚇', '公交': '🚌', '公共交通': '🚌',
      '穿衣': '👕', '穿衣服': '👕', '穿搭': '👕',
      '情绪': '😊', '情绪管理': '😊', '情绪崩溃': '😢',
      '社交': '👥', '社交回避': '👥',
      '叫名字': '📣', '名字': '📣',
      '眼神': '🙈', '对视': '🙈',
      '刻板': '🔄', '重复': '🔄',
      '上学': '🏫', '学校': '🏫',
      '吃饭': '🍽️', '用餐': '🍽️',
      '洗手': '🧼', '卫生': '🧼',
    };
    for (const [kw, emoji] of Object.entries(map)) {
      if (name.includes(kw)) return emoji;
    }
    return '📋';
  },

  // 通知所有监听器
  notify() {
    this.listeners.forEach(listener => listener(this.state));
  },
  
  // 获取当前状态
  getState() {
    return this.state;
  }
};

// 暴露到全局
window.scenarioStore = scenarioStore;
