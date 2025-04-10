import {createApp} from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router';
import {createPinia} from "pinia";
import {useUserstore} from "@/store/user"; // 新增导入

const app = createApp(App)
const pinia = createPinia()

app.use(ElementPlus)
app.use(router)
app.use(pinia)

// 在挂载应用前初始化store
const initializeStore = () => {
  const userStore = useUserstore();
  // 检查localStorage中是否有登录信息
  const storedInfo = localStorage.getItem('loginInfo');
  if (storedInfo) {
    try {
      const info = JSON.parse(storedInfo);
      const now = new Date().getTime();
      // 验证是否在有效期内（1小时）
      if (now - info.timestamp < 3600000) {
        userStore.userName = info.userName;
        userStore.token = info.token; // 重要：存储token而不是密码
      }
    } catch (e) {
      console.error('恢复登录状态失败', e);
    }
  }
};

// 初始化store
initializeStore();

app.mount('#app')