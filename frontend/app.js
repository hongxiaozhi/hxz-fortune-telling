const { createApp, reactive, ref, computed, onMounted } = Vue;

createApp({
  setup() {
    const view = ref("input");
    const showHistory = ref(false);
    const result = reactive({});
    const history = ref([]);
    const errors = reactive({});
    const readingMode = ref("summary");

    const levelLabels = { high: "高", medium: "中", low: "低" };
    const wuxingLabels = { wood: "木", fire: "火", earth: "土", metal: "金", water: "水" };
    const analysisModeLabels = { standard: "标准模式", advanced: "进阶模式" };

    const today = new Date();
    const defaultStart = today.toISOString().slice(0, 10);
    const defaultEnd = new Date(today.getTime() + 29 * 86400000).toISOString().slice(0, 10);

    const form = reactive({
      name: "",
      gender: "",
      calendar_type: "solar",
      birth_date: "",
      birth_time: "",
      birth_place: "",
      has_birth_time: false,
      precision_mode: "standard",
      analysis_mode: "standard",
      start_date: defaultStart,
      end_date: defaultEnd,
    });

    const isSummaryMode = computed(() => readingMode.value === "summary");
    const visibleSegments = computed(() => {
      const segments = result.segments || [];
      return isSummaryMode.value ? segments.slice(0, 3) : segments;
    });

    const inputModeGuide = computed(() => {
      if (form.analysis_mode === "advanced") {
        if (!form.has_birth_time && !form.birth_place.trim()) {
          return "你已切到进阶模式，但当前缺少出生时辰和出生地，只能得到轻量差异提示，结果不会明显细化。";
        }
        if (!form.has_birth_time || !form.birth_place.trim()) {
          return "你已切到进阶模式，补齐出生时辰和出生地后，结果会更容易体现和标准模式的差异。";
        }
        return "当前输入已经适合进阶模式，结果会更强调输入完整度带来的节奏差异与提醒变化。";
      }
      return "标准模式适合先快速看方向，输入不完整时也能先得到可执行建议。";
    });

    const contextSummary = computed(() => {
      const context = result.analysis_context;
      if (!context) return "";
      if (context.analysis_mode === "advanced" && context.has_birth_time && context.birth_place) {
        return "这次使用了进阶模式、出生时辰和出生地，当前结果会比标准模式更细，更强调分段节奏差异。";
      }
      if (context.analysis_mode === "advanced") {
        return "这次使用了进阶模式，但输入仍不完整，所以结果以轻量差异提示为主，不把细节判断说得过满。";
      }
      return "这次使用标准模式，结果以方向性建议为主，适合先建立整体安排顺序。";
    });

    const readingGuide = computed(() => ({
      title: isSummaryMode.value ? "先看能不能马上执行" : "按完整结构逐项判断",
      description: isSummaryMode.value
        ? "简明模式优先保留一句话结论、整体建议和最近几段重点提醒，适合先判断近期安排是收紧还是推进。"
        : "详细模式会保留完整分段、五行分布和维度提示，适合你在知道大方向后继续核对依据和差异。",
    }));

    const riskGuide = computed(() => {
      const hasPrecisionLimit = Boolean(result.precision_note);
      const upgradeVisible = Boolean(result.upgrade_hint?.show);
      const segments = result.segments || [];
      const deviatedCount = segments.filter((segment) => segment.trend_alignment === "deviated").length;

      if (hasPrecisionLimit && deviatedCount > 0) {
        return "当前结果既存在精度限制，也存在阶段波动，适合把它当作提醒清单，而不是确定结论。";
      }
      if (hasPrecisionLimit) {
        return "当前结果带有输入完整度限制，更适合用来提前规避明显风险，不适合做过细的时间点判断。";
      }
      if (deviatedCount > 0) {
        return `当前有 ${deviatedCount} 个分段与整体趋势存在偏移，阅读时要优先看分段提醒，不要只看一句话总结。`;
      }
      if (upgradeVisible) {
        return "当前结果已能给出方向性建议，但如果你需要更细的安排参考，仍建议补齐关键信息后再复看。";
      }
      return "当前结果更适合作为近期安排的参考顺序，而不是替代你对现实条件的判断。";
    });

    const usageGuide = computed(() => {
      if (isSummaryMode.value) {
        return "先把“宜 / 忌 / 提醒”转换成 1 到 2 个可执行动作，再决定这周是否要切到详细模式补看依据。";
      }
      return "详细模式更适合复查：先看整体建议，再看分段差异，最后参考五行和维度信息，不建议跳着读。";
    });

    function clearErrors() {
      Object.keys(errors).forEach((key) => {
        errors[key] = "";
      });
    }

    function resetForm() {
      form.name = "";
      form.gender = "";
      form.calendar_type = "solar";
      form.birth_date = "";
      form.birth_time = "";
      form.birth_place = "";
      form.has_birth_time = false;
      form.precision_mode = "standard";
      form.analysis_mode = "standard";
      form.start_date = defaultStart;
      form.end_date = defaultEnd;
      clearErrors();
    }

    function validate() {
      clearErrors();
      let ok = true;

      if (!form.gender) {
        errors.gender = "请选择性别。";
        ok = false;
      }
      if (!form.birth_date) {
        errors.birth_date = "请选择出生日期。";
        ok = false;
      }
      if (form.birth_place && form.birth_place.trim().length > 30) {
        errors.birth_place = "出生地最多填写 30 个字符。";
        ok = false;
      }
      if (!form.start_date || !form.end_date) {
        errors.date_range = "请选择完整的分析区间。";
        ok = false;
      } else {
        const startDate = new Date(form.start_date);
        const endDate = new Date(form.end_date);
        const diffDays = (endDate - startDate) / 86400000;
        if (startDate > endDate) {
          errors.date_range = "开始日期不能晚于结束日期。";
          ok = false;
        } else if (diffDays > 179) {
          errors.date_range = "分析区间最长为 180 天。";
          ok = false;
        }
      }
      if (form.has_birth_time && !form.birth_time) {
        errors.birth_time = "已勾选出生时辰时，需要填写出生时间。";
        ok = false;
      }
      if (!form.has_birth_time && form.birth_time) {
        errors.birth_time = "未勾选出生时辰时，请清空出生时间。";
        ok = false;
      }
      return ok;
    }

    function normalizePayload() {
      return {
        ...form,
        name: form.name || null,
        birth_time: form.has_birth_time ? form.birth_time : null,
        birth_place: form.birth_place.trim() || null,
      };
    }

    function saveHistory(data) {
      let records = JSON.parse(localStorage.getItem("hxz_fortune_history") || "[]");
      records.unshift(data);
      records = records.slice(0, 5);
      localStorage.setItem("hxz_fortune_history", JSON.stringify(records));
      history.value = records;
    }

    function loadHistoryList() {
      history.value = JSON.parse(localStorage.getItem("hxz_fortune_history") || "[]");
    }

    function applyResult(data) {
      Object.keys(result).forEach((key) => delete result[key]);
      Object.assign(result, data);
    }

    function loadHistory(index) {
      const records = JSON.parse(localStorage.getItem("hxz_fortune_history") || "[]");
      const selected = records[index];
      if (!selected) return;
      applyResult(selected);
      readingMode.value = "summary";
      view.value = "result";
      showHistory.value = false;
    }

    function toggleHistory() {
      showHistory.value = !showHistory.value;
    }

    async function onSubmit() {
      if (!validate()) return;
      view.value = "loading";
      try {
        const response = await axios.post("/api/fortune/analyze", normalizePayload());
        applyResult(response.data);
        saveHistory(response.data);
        readingMode.value = "summary";
        view.value = "result";
      } catch (error) {
        view.value = "input";
        const message = error.response?.data?.message || "分析请求失败，请稍后重试。";
        window.alert(message);
      }
    }

    onMounted(loadHistoryList);

    return {
      analysisModeLabels,
      contextSummary,
      errors,
      form,
      history,
      inputModeGuide,
      isSummaryMode,
      levelLabels,
      loadHistory,
      onSubmit,
      readingGuide,
      readingMode,
      resetForm,
      result,
      riskGuide,
      showHistory,
      toggleHistory,
      usageGuide,
      view,
      visibleSegments,
      wuxingLabels,
    };
  },
}).mount("#app");
