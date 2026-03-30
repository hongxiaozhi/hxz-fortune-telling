const { createApp, reactive, ref, onMounted } = Vue;

createApp({
  setup() {
    const view = ref("input");
    const showHistory = ref(false);
    const result = reactive({});
    const history = ref([]);
    const errors = reactive({});

    const levelLabels = {
      high: "高",
      medium: "中",
      low: "低",
    };

    const wuxingLabels = {
      wood: "木",
      fire: "火",
      earth: "土",
      metal: "金",
      water: "水",
    };

    const today = new Date();
    const defaultStart = today.toISOString().slice(0, 10);
    const defaultEnd = new Date(today.getTime() + 29 * 86400000).toISOString().slice(0, 10);

    const form = reactive({
      name: "",
      gender: "",
      calendar_type: "solar",
      birth_date: "",
      birth_time: "",
      has_birth_time: false,
      precision_mode: "standard",
      start_date: defaultStart,
      end_date: defaultEnd,
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
      form.has_birth_time = false;
      form.precision_mode = "standard";
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

    function loadHistory(index) {
      const records = JSON.parse(localStorage.getItem("hxz_fortune_history") || "[]");
      const selected = records[index];
      if (!selected) {
        return;
      }

      Object.keys(result).forEach((key) => {
        delete result[key];
      });
      Object.assign(result, selected);
      view.value = "result";
      showHistory.value = false;
    }

    function toggleHistory() {
      showHistory.value = !showHistory.value;
    }

    async function onSubmit() {
      if (!validate()) {
        return;
      }

      view.value = "loading";

      try {
        const payload = normalizePayload();
        const response = await axios.post("/api/fortune/analyze", payload);

        Object.keys(result).forEach((key) => {
          delete result[key];
        });
        Object.assign(result, response.data);

        saveHistory(response.data);
        view.value = "result";
      } catch (error) {
        view.value = "input";
        const message =
          error.response?.data?.message || "分析请求失败，请稍后重试。";
        window.alert(message);
      }
    }

    onMounted(loadHistoryList);

    return {
      errors,
      form,
      history,
      levelLabels,
      loadHistory,
      onSubmit,
      resetForm,
      result,
      showHistory,
      toggleHistory,
      view,
      wuxingLabels,
    };
  },
}).mount("#app");
