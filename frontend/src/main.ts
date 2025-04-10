import {createApp} from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router';
import {createPinia} from "pinia";
import {useUserstore} from "@/store/user"; 
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)
const pinia = createPinia()

app.use(ElementPlus)
app.use(router)
app.use(pinia)

// 初始化store
const initializeStore = () => {
  const userStore = useUserstore();
  // 检查localStorage中是否有登录信息
  const storedInfo = localStorage.getItem('loginInfo');
  if (storedInfo) {
    try {
      const info = JSON.parse(storedInfo);
      const now = new Date().getTime();
      // 验证是否在有效期内（1小时）且未手动登出
      if (now - info.timestamp < 3600000 && !info.manualLogout && info.token) {
        userStore.userName = info.userName;
        userStore.token = info.token;
      } else if (now - info.timestamp >= 3600000) {
        // 如果已过期，删除token但保留用户名
        localStorage.setItem('loginInfo', JSON.stringify({
          userName: info.userName,
          timestamp: info.timestamp,
          manualLogout: true
        }));
      }
    } catch (e) {
      console.error('恢复登录状态失败', e);
    }
  }
};

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 初始化store
initializeStore();

app.mount('#app')