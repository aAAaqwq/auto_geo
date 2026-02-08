<template>
  <div class="page-container">
    
    <!-- 左侧：控制台 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <div class="logo-box"><el-icon :size="20" color="#fff"><Platform /></el-icon></div>
        <div class="header-text"><h2>全能建站工坊</h2><p>AI 驱动 · 即时渲染</p></div>
      </div>

      <div class="form-scroll-area">
        <el-form :model="formData" label-position="top" class="dark-form">
          <!-- 默认展开前两项：0=模版选择, 1=品牌视觉 -->
          <el-collapse v-model="activeNames" class="minimal-collapse">
            
            <!-- [核心新增] 0. 模版选择 -->
            <el-collapse-item name="0">
              <template #title><div class="section-title"><span class="bar"></span><h3>选择模版 (Templates)</h3></div></template>
              <div class="form-section-content">
                <div class="template-grid">
                  <!-- 模版 A: 商务 -->
                  <div 
                    class="template-card" 
                    :class="{ active: formData.template_id === 'corporate' }"
                    @click="formData.template_id = 'corporate'"
                  >
                    <div class="preview-box bg-[#0f172a]">
                      <div class="mini-nav"></div>
                      <div class="mini-hero text-white">Corp</div>
                    </div>
                    <div class="template-info">
                      <span class="name">商务旗舰版</span>
                      <span class="tag">稳重</span>
                    </div>
                    <div class="check-mark" v-if="formData.template_id === 'corporate'"><el-icon><Check /></el-icon></div>
                  </div>

                  <!-- 模版 B: Cowboy -->
                  <div 
                    class="template-card" 
                    :class="{ active: formData.template_id === 'cowboy' }"
                    @click="formData.template_id = 'cowboy'"
                  >
                    <div class="preview-box bg-[#fdfbf7] border border-gray-600">
                      <div class="mini-nav-light"></div>
                      <div class="mini-hero text-black">Modern</div>
                    </div>
                    <div class="template-info">
                      <span class="name">现代生活版</span>
                      <span class="tag">极简</span>
                    </div>
                    <div class="check-mark" v-if="formData.template_id === 'cowboy'"><el-icon><Check /></el-icon></div>
                  </div>
                </div>
              </div>
            </el-collapse-item>

            <!-- 1. 品牌与配色 -->
            <el-collapse-item name="1">
              <template #title><div class="section-title"><span class="bar"></span><h3>品牌视觉</h3></div></template>
              <div class="form-section-content">
                <el-form-item label="公司全称"><el-input v-model="formData.company_name" /></el-form-item>
                <el-form-item label="品牌主色"><el-color-picker v-model="formData.theme_color_primary" show-alpha /></el-form-item>
                <el-form-item label="强调色"><el-color-picker v-model="formData.theme_color_accent" show-alpha /></el-form-item>
              </div>
            </el-collapse-item>

            <!-- 2. 首屏 -->
            <el-collapse-item name="2">
              <template #title><div class="section-title"><span class="bar"></span><h3>首屏 (Hero)</h3></div></template>
              <div class="form-section-content">
                <el-form-item label="标签"><el-input v-model="formData.hero_badge_text" /></el-form-item>
                <el-form-item label="标语"><el-input v-model="formData.company_slogan_hero" type="textarea" :rows="2" /></el-form-item>
                <el-form-item label="描述"><el-input v-model="formData.company_description_hero" type="textarea" :rows="3" /></el-form-item>
                <el-form-item label="背景图"><FileUpload :imageUrl="formData.image_hero_bg" @success="(url)=>formData.image_hero_bg=url" tip="1920x1080"/></el-form-item>
              </div>
            </el-collapse-item>

            <!-- 3. 数据 -->
            <el-collapse-item name="3">
              <template #title><div class="section-title"><span class="bar"></span><h3>数据 (Stats)</h3></div></template>
              <div class="form-section-content">
                <div v-for="(s,i) in formData.stats" :key="i" class="list-item-card">
                  <div class="flex-row gap-2"><el-input v-model="s.value" style="width:80px"/><el-input v-model="s.unit" style="width:60px"/><el-input v-model="s.label"/></div>
                  <el-icon class="delete-icon" @click="formData.stats.splice(i,1)"><Delete/></el-icon>
                </div>
                <el-button class="w-full mt-2 btn-dashed" size="small" @click="addStat" icon="Plus">添加指标</el-button>
              </div>
            </el-collapse-item>

            <!-- 4. 服务 -->
            <el-collapse-item name="4">
              <template #title><div class="section-title"><span class="bar"></span><h3>服务 (Services)</h3></div></template>
              <div class="form-section-content">
                <div v-for="(s,i) in formData.services" :key="i" class="list-item-card">
                  <div class="flex-col w-full">
                    <div class="flex-row gap-2 mb-2"><el-input v-model="s.icon" style="width:120px"><template #prefix>fa-</template></el-input><el-input v-model="s.title"/></div>
                    <el-input v-model="s.desc" type="textarea" :rows="2"/>
                  </div>
                  <el-icon class="delete-icon" @click="formData.services.splice(i,1)"><Delete/></el-icon>
                </div>
                <el-button class="w-full mt-2 btn-dashed" size="small" @click="addService" icon="Plus">添加服务</el-button>
              </div>
            </el-collapse-item>

            <!-- 5. 关于 -->
            <el-collapse-item name="5">
              <template #title><div class="section-title"><span class="bar"></span><h3>关于 (About)</h3></div></template>
              <div class="form-section-content">
                <el-form-item label="标题"><el-input v-model="formData.company_about_title"/></el-form-item>
                <el-form-item label="简介"><el-input v-model="formData.company_about_intro" type="textarea" :rows="4"/></el-form-item>
                <el-form-item label="核心优势列表">
                  <div v-for="(feat, i) in formData.company_features" :key="i" class="list-item-card">
                    <el-input v-model="formData.company_features[i]" />
                    <el-icon class="delete-icon ml-2" @click="formData.company_features.splice(i,1)"><Delete/></el-icon>
                  </div>
                  <el-button class="w-full mt-2 btn-dashed" size="small" @click="addFeature" icon="Plus">添加优势</el-button>
                </el-form-item>
                <el-form-item label="配图"><FileUpload :imageUrl="formData.image_about_team" @success="(url)=>formData.image_about_team=url" tip="竖向图片"/></el-form-item>
              </div>
            </el-collapse-item>

            <!-- 6. 资质 -->
            <el-collapse-item name="8">
              <template #title><div class="section-title"><span class="bar"></span><h3>资质 (Quals)</h3></div></template>
              <div class="form-section-content">
                <div v-for="(q,i) in formData.qualifications" :key="i" class="list-item-card">
                  <div class="flex-col w-full"><el-input v-model="q.title" class="mb-2 font-bold"/><el-input v-model="q.desc" size="small"/></div>
                  <el-icon class="delete-icon" @click="formData.qualifications.splice(i,1)"><Delete/></el-icon>
                </div>
                <el-button class="w-full mt-2 btn-dashed" size="small" @click="addQual" icon="Plus">添加资质</el-button>
              </div>
            </el-collapse-item>

            <!-- 7. 案例 -->
            <el-collapse-item name="6">
              <template #title><div class="section-title"><span class="bar"></span><h3>案例 (Cases)</h3></div></template>
              <div class="form-section-content">
                <div v-for="(c,i) in formData.cases" :key="i" class="list-item-card column-layout">
                  <div class="card-header"><span class="badge">#{{i+1}}</span><el-icon class="delete-icon-static" @click="formData.cases.splice(i,1)"><Delete/></el-icon></div>
                  <el-form-item label="封面"><FileUpload :imageUrl="c.image" @success="(url)=>c.image=url" height="100px"/></el-form-item>
                  <div class="flex-row gap-2 mb-2"><el-input v-model="c.tag" style="width:40%"/><el-input v-model="c.title" style="width:60%"/></div>
                  <el-input v-model="c.desc" type="textarea" :rows="2"/>
                </div>
                <el-button class="w-full mt-2 btn-dashed" size="small" @click="addCase" icon="Plus">添加案例</el-button>
              </div>
            </el-collapse-item>

            <!-- 8. 联系 -->
            <el-collapse-item name="7">
              <template #title><div class="section-title"><span class="bar"></span><h3>联系 (Contact)</h3></div></template>
              <div class="form-section-content">
                <el-form-item label="地址"><el-input v-model="formData.contact_address" prefix-icon="Location"/></el-form-item>
                <el-form-item label="电话"><el-input v-model="formData.contact_phone" prefix-icon="Phone"/></el-form-item>
                <el-form-item label="邮箱"><el-input v-model="formData.contact_email" prefix-icon="Message"/></el-form-item>
              </div>
            </el-collapse-item>

          </el-collapse>
        </el-form>
      </div>
      <div class="sidebar-footer">
        <el-button class="btn-refresh" size="large" @click="refresh" :icon="Refresh">刷新</el-button>
        <el-button class="btn-deploy" type="primary" size="large" @click="openDeployDialog">立即部署</el-button>
      </div>
    </div>

    <!-- 右侧：预览 -->
    <div class="preview-area">
      <div class="preview-container">
        <div class="browser-header">
          <div class="dots"><span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span></div>
          <div class="address-bar"><el-icon><Lock /></el-icon><span>{{ url || 'Ready...' }}</span></div>
          <el-icon class="refresh-icon" @click="refresh"><RefreshRight /></el-icon>
        </div>
        <div class="iframe-box">
          <iframe v-if="url" :src="url"></iframe>
          <div v-if="loading" class="loading-mask"><el-icon class="is-loading" size="30"><Loading /></el-icon></div>
          <div v-if="!url && !loading" class="empty-state"><el-icon size="50"><Platform /></el-icon><p>AI 引擎已就绪</p></div>
        </div>
      </div>
    </div>

    <!-- 部署弹窗 -->
    <el-dialog v-model="showDeployDialog" title="发布上线配置" width="500px" custom-class="deploy-dialog">
      <el-tabs v-model="deployMethod" class="deploy-tabs">
        <el-tab-pane label="远程服务器 (SFTP)" name="sftp">
          <div class="p-2">
            <el-alert title="请确保服务器已安装 Nginx" type="info" :closable="false" show-icon class="mb-4"/>
            <el-form label-position="left" label-width="110px">
              <el-form-item label="主机 IP"><el-input v-model="deployConfig.sftp_host"/></el-form-item>
              <el-form-item label="SSH 端口"><el-input v-model="deployConfig.sftp_port" placeholder="22"/></el-form-item>
              <el-form-item label="用户名"><el-input v-model="deployConfig.sftp_user"/></el-form-item>
              <el-form-item label="密码"><el-input v-model="deployConfig.sftp_pass" type="password" show-password/></el-form-item>
              <el-form-item label="上传路径"><el-input v-model="deployConfig.sftp_path"/></el-form-item>
              <el-form-item label="Web 访问域名">
                <el-input v-model="deployConfig.custom_domain" placeholder="选填, http://...">
                   <template #append><el-tooltip content="如 SSH 端口与 HTTP 端口不一致时必填" placement="top"><el-icon><InfoFilled /></el-icon></el-tooltip></template>
                </el-input>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        <el-tab-pane label="云对象存储 (OSS/S3)" name="s3">
          <div class="p-2">
            <el-form label-position="left" label-width="100px">
              <el-form-item label="Endpoint"><el-input v-model="deployConfig.s3_endpoint"/></el-form-item>
              <el-form-item label="Bucket"><el-input v-model="deployConfig.s3_bucket"/></el-form-item>
              <el-form-item label="AccessKey"><el-input v-model="deployConfig.s3_access_key"/></el-form-item>
              <el-form-item label="SecretKey"><el-input v-model="deployConfig.s3_secret_key" type="password" show-password/></el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDeployDialog = false">取消</el-button>
          <el-button type="primary" @click="handleDeploy" :loading="deployLoading">🚀 确认发布</el-button>
        </span>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, defineComponent, h } from 'vue';
import axios from 'axios';
import { debounce } from 'lodash';
import { ElMessage, ElUpload, ElIcon } from 'element-plus';
import { Platform, RefreshRight, Lock, Picture, Delete, Refresh, Loading, Location, Phone, Message, Plus, Promotion, Check, InfoFilled } from '@element-plus/icons-vue';

const FileUpload = defineComponent({
  props: ['imageUrl', 'tip', 'height'], emits: ['success'],
  setup(props, { emit }) {
    const backendBase = 'http://localhost:8001';
    return () => h(ElUpload, {
      class: 'simple-uploader', action: `${backendBase}/api/upload`, showFileList: false,
      onSuccess: (res) => { if(res.url) emit('success', res.url); }
    }, { default: () => [
      props.imageUrl 
        ? h('img', { src: props.imageUrl.startsWith('http') ? props.imageUrl : `${backendBase}${props.imageUrl}`, class: 'uploaded-img', style: { height: props.height||'120px' } })
        : h('div', { class: 'uploader-placeholder', style: { height: props.height||'120px' } }, [h(ElIcon, { size: 24 }, () => h(Picture)), h('span', null, props.tip||'点击上传')])
    ]});
  }
});

const activeNames = ref(['0','1','2']);
const loading = ref(false);
const dLoading = ref(false);
const url = ref("");
const showDeployDialog = ref(false);
const deployLoading = ref(false);
const deployMethod = ref("sftp");
const currentSiteId = ref("");

const deployConfig = reactive({
  sftp_host: "", sftp_port: "22", sftp_user: "root", sftp_pass: "", sftp_path: "/var/www/html", custom_domain: "",
  s3_endpoint: "", s3_bucket: "", s3_access_key: "", s3_secret_key: ""
});

const formData = reactive({
  template_id: "corporate", // 默认为商务风
  meta_title: "极速物流", company_name: "Turbo Logistics", theme_color_primary: "#0f172a", theme_color_accent: "#ef4444",
  hero_badge_text: "Global Leader", company_slogan_hero: "连接全球<br>极速送达", company_description_hero: "提供比传统物流快 30% 的服务。",
  image_hero_bg: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d",
  stats: [{ value: "15", unit: "+", label: "年经验" }, { value: "200", unit: "个", label: "覆盖国家" }],
  services: [{ icon: "robot", title: "自动化", desc: "无人化操作" }, { icon: "plane", title: "航空速运", desc: "全球次日达" }],
  qualifications: [{ title: "ISO 9001", desc: "质量认证" }],
  company_about_title: "为什么选择我们？", company_about_intro: "拥有超过50名高级工程师...", image_about_team: "https://images.unsplash.com/photo-1556761175-5973dc0f32e7",
  company_features: ["行业领先的技术解决方案", "7x24小时 全球化支持"],
  cases: [{ title: "黑五保障", tag: "电商", desc: "0 爆仓", image: "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088" }],
  contact_address: "上海市浦东新区", contact_phone: "400-888-6666", contact_email: "support@turbo.com"
});

const addStat = () => formData.stats.push({ value: "0", unit: "", label: "新指标" });
const addService = () => formData.services.push({ icon: "star", title: "新服务", desc: "描述" });
const addQual = () => formData.qualifications.push({ title: "证书", desc: "描述" });
const addCase = () => formData.cases.push({ title: "案例", tag: "行业", desc: "描述", image: "" });
const addFeature = () => formData.company_features.push("新优势特性");

const generate = debounce(async () => {
  loading.value = true;
  try {
    const res = await axios.post('http://localhost:8001/sites/build', { 
      name: formData.company_name, 
      config: formData,
      template_id: formData.template_id // 传给后端
    });
    if (res.data.code === 200) {
      currentSiteId.value = res.data.data.site_id;
      url.value = `http://localhost:8001${res.data.data.preview_url}?t=${Date.now()}`;
    }
  } catch(e) { console.error(e); } finally { setTimeout(() => loading.value = false, 500); }
}, 800);

watch(formData, () => generate(), { deep: true });
onMounted(() => generate());
const refresh = generate;
const openDeployDialog = () => { if(!currentSiteId.value) return ElMessage.warning('请先等待预览生成'); showDeployDialog.value = true; }

const handleDeploy = async () => {
  deployLoading.value = true;
  try {
    const payload = { site_id: currentSiteId.value, method: deployMethod.value, project_name: formData.company_name, ...deployConfig };
    const res = await axios.post('http://localhost:8001/sites/deploy', payload);
    if (res.data.code === 200) {
      ElMessage.success('🎉 部署成功！');
      showDeployDialog.value = false;
      if (res.data.data && res.data.data.url) window.open(res.data.data.url, '_blank');
    }
  } catch (error) { ElMessage.error(error.response?.data?.detail || '部署失败'); } finally { deployLoading.value = false; }
}
</script>

<style scoped>
/* 保持原有深色 CSS 样式 */
.page-container { display: flex; height: 100vh; background: #020617; font-family: sans-serif; overflow: hidden; }
.sidebar { width: 440px; min-width: 440px; background: #0f172a; border-right: 1px solid #1e293b; display: flex; flex-direction: column; z-index: 10; box-shadow: 4px 0 20px rgba(0,0,0,0.3); }
.sidebar-header { padding: 20px; border-bottom: 1px solid #1e293b; display: flex; gap: 12px; align-items: center; }
.logo-box { width: 36px; height: 36px; background: #3b82f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.header-text h2 { margin: 0; font-size: 16px; color: #f8fafc; font-weight: 700; }
.header-text p { margin: 0; font-size: 12px; color: #94a3b8; }
.form-scroll-area { flex: 1; overflow-y: auto; padding: 0; background: #0f172a; }
.sidebar-footer { padding: 16px 20px; border-top: 1px solid #1e293b; display: flex; gap: 12px; background: #0f172a; }
.btn-refresh { flex: 1; border-color: #334155; color: #cbd5e1; background: #1e293b; }
.btn-deploy { flex: 2; background: #2563eb; border: none; font-weight: 600; letter-spacing: 0.5px; }
.preview-area { flex: 1; background: #020617; display: flex; align-items: center; justify-content: center; padding: 40px; }
.preview-container { width: 100%; height: 100%; max-width: 1400px; background: #fff; border-radius: 8px; box-shadow: 0 0 30px rgba(0,0,0,0.5); display: flex; flex-direction: column; border: 1px solid #334155; overflow: hidden; }
.browser-header { height: 42px; background: #1e293b; border-bottom: 1px solid #0f172a; display: flex; align-items: center; px: 16px; gap: 12px; padding: 0 16px; }
.dots { display: flex; gap: 6px; } .dot { width: 10px; height: 10px; border-radius: 50%; } .dot.red { background: #ff5f57; } .dot.yellow { background: #febc2e; } .dot.green { background: #28c840; }
.address-bar { flex: 1; height: 28px; background: #0f172a; border: 1px solid #334155; border-radius: 4px; display: flex; align-items: center; padding: 0 10px; font-size: 12px; color: #94a3b8; gap: 8px; }
.iframe-box { flex: 1; position: relative; }
iframe { width: 100%; height: 100%; border: none; }
.loading-mask { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.9); display: flex; justify-content: center; align-items: center; z-index: 20; color: white; }
.empty-state { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #64748b; gap: 10px; background: #020617; }

/* 模版选择卡片 */
.template-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.template-card { border: 2px solid #334155; border-radius: 8px; cursor: pointer; transition: all 0.2s; position: relative; overflow: hidden; }
.template-card:hover { border-color: #64748b; }
.template-card.active { border-color: #2563eb; background: rgba(37, 99, 235, 0.1); }
.preview-box { height: 60px; position: relative; }
.mini-nav { height: 8px; background: rgba(255,255,255,0.1); margin-bottom: 4px; }
.mini-nav-light { height: 8px; background: rgba(0,0,0,0.1); margin-bottom: 4px; }
.mini-hero { display: flex; align-items: center; justify-content: center; height: 100%; font-size: 10px; font-weight: bold; }
.template-info { padding: 8px; display: flex; justify-content: space-between; align-items: center; }
.name { color: #f8fafc; font-size: 12px; font-weight: bold; }
.tag { font-size: 10px; color: #94a3b8; background: #1e293b; padding: 2px 6px; border-radius: 4px; }
.check-mark { position: absolute; top: 4px; right: 4px; background: #2563eb; color: white; border-radius: 50%; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; font-size: 10px; }

/* 复用之前的样式... */
:deep(.el-collapse) { border: none; }
:deep(.el-collapse-item__header) { background-color: #0f172a; color: #e2e8f0; border-bottom: 1px solid #1e293b; padding-left: 20px; font-weight: 600; }
:deep(.el-collapse-item__content) { background-color: #020617; padding: 20px; color: #cbd5e1; border-bottom: 1px solid #1e293b; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) { background-color: #1e293b !important; box-shadow: 0 0 0 1px #334155 inset !important; color: #f1f5f9 !important; }
:deep(.el-form-item__label) { color: #94a3b8 !important; }
.section-title { display: flex; align-items: center; gap: 10px; } .section-title h3 { margin: 0; font-size: 14px; color: #f8fafc; } .bar { width: 4px; height: 14px; background-color: #3b82f6; border-radius: 2px; }
.color-picker-row { display: flex; gap: 10px; align-items: center; } .color-dot { width: 24px; height: 24px; border-radius: 50%; cursor: pointer; border: 2px solid #334155; }
.list-item-card { background: #1e293b; border: 1px solid #334155; padding: 12px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.list-item-card.column-layout { flex-direction: column; align-items: flex-start; }
.flex-row { display: flex; gap: 8px; width: 100%; } .flex-col { display: flex; flex-direction: column; width: 100%; }
.btn-dashed { border: 1px dashed #475569; color: #94a3b8; background: transparent; } .btn-dashed:hover { border-color: #60a5fa; color: #60a5fa; }
.delete-icon { cursor: pointer; color: #475569; } .delete-icon:hover { color: #ef4444; }
.card-header { width: 100%; display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 4px; }
.badge { font-size: 11px; background: #334155; padding: 2px 8px; border-radius: 10px; color: #94a3b8; }
:deep(.simple-uploader .el-upload) { width: 100%; border: 1px dashed #475569; border-radius: 6px; cursor: pointer; background: #1e293b; overflow: hidden; }
.uploaded-img { width: 100%; object-fit: cover; display: block; }
.uploader-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #94a3b8; font-size: 12px; gap: 8px; height: 100%; }
</style>
