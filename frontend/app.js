const { createApp, reactive, ref, computed, onMounted } = Vue;

createApp({
  setup() {
    const view = ref("input");
    const showHistory = ref(false);
    const result = reactive({});
    const history = ref([]);
    const errors = reactive({});
    const readingMode = ref("summary");
    const compareRecord = ref(null);

    const levelLabels = { high: "高", medium: "中", low: "低" };
    const wuxingLabels = { wood: "木", fire: "火", earth: "土", metal: "金", water: "水" };
    const analysisModeLabels = { standard: "标准模式", advanced: "进阶模式" };
    const HISTORY_KEY = "hxz_fortune_history";

    function formatDate(date) {
      return date.toISOString().slice(0, 10);
    }

    function getRange(days) {
      const start = new Date();
      const end = new Date(start.getTime() + (days - 1) * 86400000);
      return {
        start: formatDate(start),
        end: formatDate(end),
      };
    }

    const defaultRange = getRange(30);

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
      start_date: defaultRange.start,
      end_date: defaultRange.end,
    });

    const isSummaryMode = computed(() => readingMode.value === "summary");
    const visibleSegments = computed(() => {
      const segments = result.segments || [];
      return isSummaryMode.value ? segments.slice(0, 3) : segments;
    });

    const historyStats = computed(() => {
      const records = history.value;
      const advancedCount = records.filter((item) => item.meta?.analysis_mode === "advanced").length;
      return {
        total: records.length,
        advanced: advancedCount,
        standard: records.length - advancedCount,
      };
    });

    const currentRecordId = computed(() => result.request_id || null);

    const compareSummary = computed(() => {
      if (!compareRecord.value || !result.request_id) {
        return null;
      }

      const currentContext = result.analysis_context || {};
      const targetContext = compareRecord.value.analysis_context || {};
      const currentMode = analysisModeLabels[currentContext.analysis_mode] || "标准模式";
      const targetMode = analysisModeLabels[targetContext.analysis_mode] || "标准模式";
      const currentBirthPlace = currentContext.birth_place || "未提供";
      const targetBirthPlace = targetContext.birth_place || "未提供";
      const currentRange = `${result.segments?.[0]?.start_date || "-"} 至 ${result.segments?.at(-1)?.end_date || "-"}`;
      const targetRange = `${compareRecord.value.segments?.[0]?.start_date || "-"} 至 ${compareRecord.value.segments?.at(-1)?.end_date || "-"}`;

      const highlights = [];
      if (currentMode !== targetMode) {
        highlights.push(`这次使用${currentMode}，对比记录使用${targetMode}。`);
      } else {
        highlights.push(`两次都使用${currentMode}，更适合直接看输入完整度和建议差异。`);
      }

      if (currentBirthPlace !== targetBirthPlace) {
        highlights.push(`出生地输入发生变化：当前为${currentBirthPlace}，对比记录为${targetBirthPlace}。`);
      }

      if ((currentContext.has_birth_time || false) !== (targetContext.has_birth_time || false)) {
        highlights.push("两次记录的出生时辰完整度不同，分段提醒的细化程度会随之变化。");
      }

      if ((result.overall_advice?.suitable || "") !== (compareRecord.value.overall_advice?.suitable || "")) {
        highlights.push("整体建议已发生变化，说明当前输入条件或分析模式影响了建议方向。");
      }

      if ((result.segments?.[0]?.suitable || "") !== (compareRecord.value.segments?.[0]?.suitable || "")) {
        highlights.push("首段建议不同，近期执行节奏需要按当前结果重新排序。");
      }

      if (!highlights.length) {
        highlights.push("当前结果与对比记录整体接近，可优先复用原有安排。");
      }

      return {
        currentMode,
        targetMode,
        currentBirthPlace,
        targetBirthPlace,
        currentRange,
        targetRange,
        currentSuitable: result.overall_advice?.suitable || "",
        targetSuitable: compareRecord.value.overall_advice?.suitable || "",
        currentSegment: result.segments?.[0]?.suitable || "",
        targetSegment: compareRecord.value.segments?.[0]?.suitable || "",
        highlights,
      };
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
      form.start_date = defaultRange.start;
      form.end_date = defaultRange.end;
      clearErrors();
    }

    function setQuickRange(days) {
      const range = getRange(days);
      form.start_date = range.start;
      form.end_date = range.end;
      errors.date_range = "";
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

    function buildHistoryRecord(data, payload) {
      return {
        ...data,
        meta: {
          created_at: new Date().toISOString(),
          name: payload.name || "",
          analysis_mode: payload.analysis_mode,
          birth_place: payload.birth_place,
          has_birth_time: payload.has_birth_time,
          start_date: payload.start_date,
          end_date: payload.end_date,
        },
      };
    }

    function readHistory() {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    }

    function writeHistory(records) {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(records));
      history.value = records;
    }

    function saveHistory(data, payload) {
      let records = readHistory();
      records.unshift(buildHistoryRecord(data, payload));
      records = records.slice(0, 8);
      writeHistory(records);
    }

    function loadHistoryList() {
      history.value = readHistory();
    }

    function applyResult(data) {
      Object.keys(result).forEach((key) => delete result[key]);
      Object.assign(result, data);
    }

    function loadHistory(index) {
      const records = readHistory();
      const selected = records[index];
      if (!selected) return;
      applyResult(selected);
      readingMode.value = "summary";
      view.value = "result";
      showHistory.value = false;
    }

    function setCompareRecord(index) {
      const records = readHistory();
      compareRecord.value = records[index] || null;
      if (compareRecord.value) {
        view.value = "result";
      }
    }

    function clearCompareRecord() {
      compareRecord.value = null;
    }

    function removeHistory(index) {
      const records = readHistory();
      const removed = records[index];
      if (!removed) return;
      records.splice(index, 1);
      writeHistory(records);
      if (compareRecord.value?.request_id === removed.request_id) {
        compareRecord.value = null;
      }
    }

    function clearHistory() {
      writeHistory([]);
      compareRecord.value = null;
    }

    function toggleHistory() {
      showHistory.value = !showHistory.value;
    }

    function formatHistoryTitle(item) {
      return item.meta?.name || item.overall_advice?.suitable || "查看分析结果";
    }

    function formatHistoryMeta(item) {
      const mode = analysisModeLabels[item.meta?.analysis_mode] || "标准模式";
      const range = item.meta?.start_date && item.meta?.end_date
        ? `${item.meta.start_date} 至 ${item.meta.end_date}`
        : "未记录区间";
      const place = item.meta?.birth_place || "未提供出生地";
      return `${mode} · ${place} · ${range}`;
    }

    async function onSubmit() {
      if (!validate()) return;
      view.value = "loading";
      try {
        const payload = normalizePayload();
        const response = await axios.post("/api/fortune/analyze", payload);
        applyResult(response.data);
        saveHistory(response.data, payload);
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
      clearCompareRecord,
      clearHistory,
      compareRecord,
      compareSummary,
      contextSummary,
      currentRecordId,
      errors,
      form,
      formatHistoryMeta,
      formatHistoryTitle,
      history,
      historyStats,
      inputModeGuide,
      isSummaryMode,
      levelLabels,
      loadHistory,
      onSubmit,
      readingGuide,
      readingMode,
      removeHistory,
      resetForm,
      result,
      riskGuide,
      setCompareRecord,
      setQuickRange,
      showHistory,
      toggleHistory,
      usageGuide,
      view,
      visibleSegments,
      wuxingLabels,
    };
  },
}).mount("#app");
