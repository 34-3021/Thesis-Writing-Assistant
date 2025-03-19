<script setup lang="ts">
import AsideNavBar from "@/components/AsideNavBar.vue";
import Header from "@/components/Header.vue";
</script>

<template>
  <div class="common-layout">
    <el-container class="index-container">
      <el-header>
        <Header></Header>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <AsideNavBar></AsideNavBar>
        </el-aside>
        <el-container class="main-container">
          <el-main>
            <router-view></router-view>
            <!-- 新增宣传区域，采用flex布局，右侧放置放大的商标 -->
            <div class="info-banner">
              <div class="info-text">
                <h2>探索无限可能，体验智能论文写作新纪元！</h2>
                <p>使用海平AI，释放您的创意潜能，实现高效论文创作与脑力风暴，带您走进智能科技的新时代！</p>
              </div>
              <img src="@/assets/images/trademark.jpg" alt="trademark" class="brand-right" />
            </div>
          </el-main>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.common-layout {
  background-image: url('@/assets/images/index-bg.jpg');
  background-size: cover;
  background-position: center;
  min-height: 100vh;
}
.index-container {
  background-color: rgba(255, 255, 255, 0.9);
  margin: 20px;
  border-radius: 10px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
}
.main-container {
  margin-top: 30px;
}
/* 宣传区域采用flex布局 */
.info-banner {
  margin-top: 40px;
  padding: 20px;
  background-color: rgba(240, 240, 240, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.info-text {
  max-width: 70%;
}
.info-banner h2 {
  font-size: 32px;
  color: #333;
  margin-bottom: 10px;
}
.info-banner p {
  font-size: 18px;
  color: #666;
}
/* 右侧商标样式：尺寸放大 */
.brand-right {
  height: 100px;
}
</style>