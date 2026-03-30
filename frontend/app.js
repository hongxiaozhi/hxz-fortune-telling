// HXZ Fortune v1.1 前端主逻辑
const { createApp, ref, reactive, onMounted } = Vue;

createApp({
  setup() {
    const view = ref('input');
    const showHistory = ref(false);
    const result = reactive({});
    const errors = reactive({});
    const history = ref([]);
    const today = new Date();
    const defaultStart = today.toISOString().slice(0,10);
    const defaultEnd = new Date(today.getTime() + 29*86400000).toISOString().slice(0,10);
    const form = reactive({
      name: '',
      gender: '',
      calendar_type: 'solar',
      birth_date: '',
      birth_time: '',
      has_birth_time: false,
      precision_mode: 'standard',
      start_date: defaultStart,
      end_date: defaultEnd
    });
    function resetForm() {
      form.name = '';
      form.gender = '';
      form.calendar_type = 'solar';
      form.birth_date = '';
      form.birth_time = '';
      form.has_birth_time = false;
      form.precision_mode = 'standard';
      form.start_date = defaultStart;
      form.end_date = defaultEnd;
      Object.keys(errors).forEach(k=>errors[k]='');
    }
    function validate() {
      let ok = true;
      errors.gender = form.gender ? '' : '请选择性别';
      errors.birth_date = form.birth_date ? '' : '请选择出生日期';
      // 日期区间校验
      if (!form.start_date || !form.end_date) {
        errors.date_range = '请选择分析区间';
        ok = false;
      } else {
        const sd = new Date(form.start_date), ed = new Date(form.end_date);
        if (sd > ed) {
          errors.date_range = '起始日期不能晚于结束日期';
          ok = false;
        } else if ((ed - sd) / 86400000 > 179) {
          errors.date_range = '区间最多180天';
          ok = false;
        } else {
          errors.date_range = '';
        }
      }
      if (!form.has_birth_time && form.birth_time) {
        errors.birth_time = '未勾选“有出生时辰”时，时辰应留空';
        ok = false;
      } else {
        errors.birth_time = '';
      }
      return ok;
    }
    async function onSubmit() {
      if (!validate()) return;
      view.value = 'loading';
        try {
          const payload = { ...form };
          if (!form.has_birth_time) payload.birth_time = null;
          // use relative path so the frontend works behind the same origin (Traefik)
          const { data } = await axios.post('/api/fortune/analyze', payload);
          Object.assign(result, data);
          saveHistory(data);
          view.value = 'result';
        } catch (e) {
          view.value = 'input';
          alert(e.response?.data?.message || '请求失败');
        }
    }
    function saveHistory(data) {
      let arr = JSON.parse(localStorage.getItem('hxz_fortune_history') || '[]');
      arr.unshift(data);
      if (arr.length > 5) arr = arr.slice(0,5);
      localStorage.setItem('hxz_fortune_history', JSON.stringify(arr));
      history.value = arr;
    }
    function loadHistory(idx) {
      const arr = JSON.parse(localStorage.getItem('hxz_fortune_history') || '[]');
      if (arr[idx]) {
        Object.assign(result, arr[idx]);
        view.value = 'result';
        showHistory.value = false;
      }
    }
    function loadHistoryList() {
      history.value = JSON.parse(localStorage.getItem('hxz_fortune_history') || '[]');
    }
    onMounted(loadHistoryList);
    return { view, showHistory, form, errors, result, onSubmit, resetForm, history, loadHistory };
  }
}).mount('#app');
