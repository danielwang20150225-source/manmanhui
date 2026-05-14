/**
 * 用户状态管理
 * 管理anonymous UUID + localStorage持久化
 */
const userStore = {
  // localStorage key
  USER_ID_KEY: 'manmanhui_user_id',
  RECORDS_KEY: 'manmanhui_training_records',

  // 状态
  state: {
    userId: null,
    trainingRecords: [],
    loading: false
  },

  // 监听器
  listeners: [],

  // 生成UUID
  _generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  },

  // 获取或创建用户ID
  getUserId() {
    if (this.state.userId) return this.state.userId;

    let userId = localStorage.getItem(this.USER_ID_KEY);
    if (!userId) {
      userId = this._generateUUID();
      localStorage.setItem(this.USER_ID_KEY, userId);
    }
    this.state.userId = userId;
    return userId;
  },

  // 获取训练记录
  getTrainingRecords() {
    try {
      const records = localStorage.getItem(this.RECORDS_KEY);
      this.state.trainingRecords = records ? JSON.parse(records) : [];
    } catch (e) {
      this.state.trainingRecords = [];
    }
    return this.state.trainingRecords;
  },

  // 添加训练记录
  addTrainingRecord(record) {
    const newRecord = {
      id: this._generateUUID(),
      user_id: this.getUserId(),
      timestamp: Date.now(),
      date: new Date().toISOString().split('T')[0],
      ...record
    };

    this.state.trainingRecords.push(newRecord);
    this._saveRecords();
    this.notify();

    return newRecord;
  },

  // 保存记录到localStorage
  _saveRecords() {
    try {
      localStorage.setItem(this.RECORDS_KEY, JSON.stringify(this.state.trainingRecords));
    } catch (e) {
      console.error('保存训练记录失败:', e);
    }
  },

  // 获取某个情境的训练记录
  getRecordsByScenario(scenarioId) {
    return this.state.trainingRecords.filter(r => r.scenario_id === scenarioId);
  },

  // 获取最近的训练记录（用于首页展示）
  getRecentRecords(limit = 5) {
    return [...this.state.trainingRecords]
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  },

  // 获取连续训练天数
  getStreakDays() {
    const records = this.getTrainingRecords();
    if (records.length === 0) return 0;

    const dates = [...new Set(records.map(r => r.date))].sort().reverse();
    let streak = 1;
    const today = new Date().toISOString().split('T')[0];

    // 检查今天或昨天是否有训练
    if (dates[0] !== today && dates[0] !== this._getYesterday()) {
      return 0;
    }

    // 计算连续天数
    for (let i = 1; i < dates.length; i++) {
      const prev = new Date(dates[i-1]);
      const curr = new Date(dates[i]);
      const diff = (prev - curr) / (1000 * 60 * 60 * 24);

      if (diff === 1) {
        streak++;
      } else {
        break;
      }
    }

    return streak;
  },

  // 获取昨天的日期
  _getYesterday() {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split('T')[0];
  },

  // 添加监听器
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  },

  // 通知监听器
  notify() {
    this.listeners.forEach(l => l(this.state));
  },

  // 获取状态
  getState() {
    return this.state;
  },

  // 初始化（从localStorage加载）
  init() {
    this.getUserId();
    this.getTrainingRecords();
    this.notify();
  }
};

// 暴露到全局
window.userStore = userStore;
