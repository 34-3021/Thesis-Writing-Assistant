<script setup lang="ts">
import LoginForm from "@/components/LoginForm.vue";
</script>

<template>
  <div class="container">
    <div class="overlay">
      <!-- 标题区域，增加商标图标 -->
      <div class="login-header">
        <div class="header-title">
          <h1>海平AI 3.7</h1>
          <img src="@/assets/images/trademark.jpg" alt="trademark" class="trademark-icon" />
        </div>
        <h2 class="sub-title">论文写作助手</h2>
      </div>
      <!-- 登录表单 -->
      <div class="background">
        <LoginForm class="form-container"></LoginForm>
      </div>
      <!-- 页脚居中小字 -->
      <div class="footer-text">春——七宝中学</div>
    </div>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}
.container {
  /* 使用新背景图 */
  background-image: url('@/assets/images/new-background2.jpg');
  background-size: cover;
  background-position: center;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}
.overlay {
  position: relative;
  width: 100%;
  height: 100%;
}
/* 标题区域 */
.login-header {
  position: absolute;
  top: 10%;
  width: 100%;
  text-align: center;
  z-index: 2;
}
.header-title {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.header-title h1 {
  font-size: 48px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #fdfdfd;
  text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
  margin: 0 10px 0 0;
}
/* 为商标图标设置高度 */
.trademark-icon {
  height: 48px;
}
.sub-title {
  font-size: 28px;
  font-family: 'Georgia', serif;
  color: #F5A9B8; /* 稍柔和的颜色 */
  text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
  margin: 5px 0 20px;
}
/* 登录框背景，透明白色 */
.background {
  background-color: rgba(255, 255, 255, 0.8);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 0 10px rgba(0,0,0,0.1);
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -45%);
  width: 420px;
}
.form-container {
  width: 100%;
}
/* 按钮区域居中对称排列 */
.form-container .el-form-item:last-child {
  display: flex;
  justify-content: space-around;
}
/* 页脚文本 */
.footer-text {
  position: absolute;
  bottom: 8%;
  width: 100%;
  text-align: center;
  font-size: 18px; /* 稍大一点，便于阅读 */
  font-family: "楷体", "行楷", sans-serif;
  font-weight: bold;
  color: coral;
  text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
}
</style>