/**
 * 训练状态管理
 * 管理每日训练页面的状态
 */
const trainingStore = {
  // 状态
  state: {
    scenarioId: null,
    day: 1,
    totalDays: 14,
    dayTheme: null,       // 今日任务名称
    todayGoal: null,
    todayTip: null,
    observePrompt: null,  // 观察重点
    steps: [],
    currentStep: 0,
    loading: false,
    error: null
  },

  // 监听器列表
  listeners: [],

  // localStorage key前缀
  STORAGE_KEY_PREFIX: 'training_progress_',

  // 初始化训练数据
  init(scenarioId, day) {
    this.state.scenarioId = scenarioId;
    this.state.day = day || 1;
    this.notify();
  },

  // 获取训练进度（从localStorage）
  getProgress() {
    if (!this.state.scenarioId) return null;
    const key = this.STORAGE_KEY_PREFIX + this.state.scenarioId;
    const saved = localStorage.getItem(key);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return null;
      }
    }
    return null;
  },

  // 保存训练进度（到localStorage）
  saveProgress() {
    if (!this.state.scenarioId) return;
    const key = this.STORAGE_KEY_PREFIX + this.state.scenarioId;
    const progressData = {
      scenarioId: this.state.scenarioId,
      day: this.state.day,
      currentStep: this.state.currentStep,
      savedAt: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(progressData));
  },

  // 清除训练进度
  clearProgress() {
    if (!this.state.scenarioId) return;
    const key = this.STORAGE_KEY_PREFIX + this.state.scenarioId;
    localStorage.removeItem(key);
  },

  // 从API获取当日训练数据
  async fetchTodayTraining(scenarioId, day) {
    this.state.loading = true;
    this.state.error = null;
    this.state.scenarioId = scenarioId;
    this.state.day = day || 1;
    this.notify();

    try {
      const response = await fetch(`${getApiBase()}/api/scenarios/${scenarioId}/days/${day}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.code === 0 && data.data) {
        const trainingData = data.data;
        this.state.dayTheme = trainingData.day_theme || trainingData.theme || '';
        this.state.todayGoal = trainingData.today_goal || '';
        this.state.todayTip = trainingData.today_tip || '';
        this.state.observePrompt = trainingData.observe_prompt || trainingData.observation_point || '';
        this.state.steps = trainingData.steps || [];
        this.state.totalDays = trainingData.total_days || 14;
        
        // 恢复保存的进度
        const savedProgress = this.getProgress();
        if (savedProgress && savedProgress.day === this.state.day) {
          this.state.currentStep = savedProgress.currentStep || 0;
        } else {
          this.state.currentStep = 0;
        }
      } else {
        throw new Error(data.message || '获取训练数据失败');
      }

      this.state.loading = false;
      this.notify();
      return this.state;

    } catch (error) {
      console.error('获取训练数据失败:', error);
      this.state.error = error.message;
      this.state.loading = false;
      this.notify();
      return null;
    }
  },

  // 更新当前步骤
  setCurrentStep(stepIndex) {
    this.state.currentStep = stepIndex;
    this.saveProgress();
    this.notify();
  },

  // 下一步
  nextStep() {
    if (this.state.currentStep < this.state.steps.length - 1) {
      this.state.currentStep++;
      this.saveProgress();
      this.notify();
      return true;
    }
    return false;
  },

  // 上一步
  prevStep() {
    if (this.state.currentStep > 0) {
      this.state.currentStep--;
      this.saveProgress();
      this.notify();
      return true;
    }
    return false;
  },

  // 获取当前步骤
  getCurrentStep() {
    return this.state.currentStep;
  },

  // 获取总步骤数
  getTotalSteps() {
    return this.state.steps.length;
  },

  // 添加监听器
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  },

  // 通知所有监听器
  notify() {
    this.listeners.forEach(listener => listener(this.state));
  },

  // 获取当前状态
  getState() {
    return this.state;
  },

  // 获取当前task_id（从localStorage的trainingProgress读取）
  getCurrentTaskId() {
    if (!this.state.scenarioId) return null;
    const key = this.STORAGE_KEY_PREFIX + this.state.scenarioId;
    const saved = localStorage.getItem(key);
    if (saved) {
      try {
        const progress = JSON.parse(saved);
        return progress.taskId || null;
      } catch (e) {
        return null;
      }
    }
    return null;
  }
};

// 暴露到全局
window.trainingStore = trainingStore;