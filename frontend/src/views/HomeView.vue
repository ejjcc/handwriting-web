<template>
  <div class="hw-app">
    <!-- TOP TOOLBAR -->
    <div class="hw-toolbar">
      <div class="hw-toolbar-section hw-toolbar-left">
        <button class="hw-icon-btn hw-sidebar-toggle" @click="toggleSidebar"
          :title="showSidebar ? '收起设置' : '展开设置'">
          {{ showSidebar ? '◀' : '☰' }}
        </button>
        <span class="hw-title">手写生成器</span>
      </div>

      <div class="hw-toolbar-section hw-toolbar-center">
        <button class="hw-btn hw-btn-sm" @click="triggerTextUpload"
          :title="$t('message.orUploadDocument') + ' (.doc/.docx/.pdf/.txt/.rtf)'">
          📄 上传文档
        </button>
        <button class="hw-btn hw-btn-sm hw-btn-letter" @click="openLetterFormatter">
          <span class="hw-btn-letter-mark" aria-hidden="true">信</span>
          {{ $t('message.formatChineseLetter') }}
        </button>
        <button v-if="letterFormatBackup !== null" class="hw-btn hw-btn-sm hw-btn-ghost"
          @click="undoLetterFormatting">
          {{ $t('message.letterUndo') }}
        </button>
        <span v-if="uploadedFileName" class="hw-filename hw-toolbar-filename" :title="uploadedFileName">
          {{ uploadedFileName }}
        </span>
      </div>

      <div class="hw-toolbar-section hw-toolbar-right">
        <button class="hw-btn hw-btn-primary" @click="generateHandwriting(preview = true)"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.preview') }}
        </button>
        <button v-if="isDevEnv" class="hw-btn hw-btn-ghost" @click="toggleFullPreview"
          :disabled="shouldDisableButtons">
          全量预览：{{ enableFullPreview ? '开' : '关' }}
        </button>
        <button class="hw-btn hw-btn-success" @click="generateHandwriting(preview = false)"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.generateFullHandwritingImage') }}
        </button>
        <button class="hw-btn hw-btn-success" @click="generateHandwriting(preview = false, pdf_save = true)"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.generatePdf') }}
        </button>
        <router-link to="/Feedback" class="hw-btn hw-btn-ghost">{{ $t('message.feedback') }}</router-link>
        <button class="hw-icon-btn hw-help-btn" @click="showHelp = true" title="语法帮助">?</button>
      </div>
    </div>

    <ChineseLetterFormatter v-if="showLetterFormatter" :source-text="text"
      @close="showLetterFormatter = false" @apply="applyLetterFormatting" />

    <!-- HELP MODAL -->
    <div v-if="showHelp" class="hw-modal-overlay" @click.self="showHelp = false">
      <div class="hw-modal">
        <div class="hw-modal-header">
          <span class="hw-modal-title">语法帮助</span>
          <button class="hw-icon-btn" @click="showHelp = false" title="关闭">×</button>
        </div>
        <div class="hw-modal-body">
          <p class="hw-help-intro">在文字编辑区里可以用以下标记控制排版：</p>

          <div class="hw-help-item">
            <div class="hw-help-syntax"><code>---</code></div>
            <div class="hw-help-desc">
              <strong>分页符</strong>：独占一行的三个或更多连字符，会从这里强制换到下一页。
              <pre class="hw-help-example">第一页的内容
---
第二页的内容</pre>
            </div>
          </div>

          <div class="hw-help-item">
            <div class="hw-help-syntax"><code>&gt;&gt;&gt;</code></div>
            <div class="hw-help-desc">
              <strong>右对齐</strong>：以 <code>&gt;&gt;&gt;</code> 开头的行，该行内容靠右边距对齐（常用于落款、日期）。
              <pre class="hw-help-example">正文左对齐
&gt;&gt;&gt;祝大家新年快乐
&gt;&gt;&gt;写于丙午年初一</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ALERT MESSAGES -->
    <div v-if="message || uploadMessage" class="hw-alerts">
      <div v-if="message" class="alert alert-info hw-alert">{{ message }}</div>
      <div v-if="uploadMessage" class="alert alert-info hw-alert">{{ uploadMessage }}</div>
    </div>

    <!-- 3-PANE BODY -->
    <div class="hw-split">
      <!-- LEFT: SETTINGS SIDEBAR (collapsible) -->
      <aside v-if="showSidebar" class="hw-pane hw-sidebar">
        <div class="hw-sidebar-header">
          <span class="hw-sidebar-title">设置</span>
          <button class="hw-icon-btn" @click="toggleSidebar" title="收起">◀</button>
        </div>

        <section class="hw-section">
          <h3 class="hw-section-title">预设</h3>
          <div class="hw-field">
            <select v-model="selectedPreset" @change="applyPreset" class="hw-select hw-select-grow">
              <option value="">{{ $t('message.presetNone') }}</option>
              <option value="smallUnderlined">{{ $t('message.presetSmallUnderlined') }}</option>
            </select>
          </div>
          <div class="hw-row hw-row-tight">
            <button class="hw-btn hw-btn-sm" @click="loadPreset">{{ $t('message.loadSettings') }}</button>
            <button class="hw-btn hw-btn-sm" @click="savePreset">{{ $t('message.saveSettings') }}</button>
            <button class="hw-btn hw-btn-sm" @click="resetSettings">{{ $t('message.resetSettings') }}</button>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">字体 &amp; 背景</h3>

          <div class="hw-field">
            <label class="hw-field-label">{{ $t('message.fontFile') }}</label>
            <div class="hw-field-control hw-row">
              <button class="hw-btn hw-btn-sm" @click="triggerFontFileInput">{{ $t('message.chooseFile') }}</button>
              <input type="file" ref="fontFileInput" @change="onFontChange" style="display: none;" />
              <select v-model="selectedOption" class="hw-select hw-select-grow">
                <option v-for="option in options" :value="option.value" :key="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>
          </div>

          <div class="hw-field">
            <label class="hw-field-label">{{ $t('message.backgroundImageFile') }}</label>
            <div class="hw-field-control hw-row">
              <button class="hw-btn hw-btn-sm" @click="triggerImageFileInput"
                :class="{ 'button-disabled': isDimensionSpecified }"
                :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
                {{ $t('message.chooseFile') }}
                <span v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                  <span class="clear-button-line"></span>
                  <span class="clear-button-line"></span>
                </span>
              </button>
              <span class="hw-filename" v-if="selectedImageFileName">{{ selectedImageFileName }}</span>
              <input type="file" ref="imageFileInput" @change="onBackgroundImageChange" style="display: none;" />
              <span v-if="isLoading" class="loader">{{ $t('message.loading') }}...</span>
            </div>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">页面与样式</h3>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.width') }}</label>
            <input class="hw-input" type="number" v-model="width" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
          </div>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.height') }}</label>
            <input class="hw-input" type="number" v-model="height" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
            <button type="button" class="hw-icon-btn" title="清空宽高" @click="clearDimensions">×</button>
          </div>

          <div class="hw-field hw-field-checkbox">
            <input type="checkbox" id="optionUnderline" v-model="isUnderlined" />
            <label for="optionUnderline">增加下划线</label>
          </div>

          <div class="hw-field hw-field-checkbox">
            <input type="checkbox" id="optionEnglishSpacing" v-model="enableEnglishSpacing" />
            <label for="optionEnglishSpacing">{{ $t('message.enableEnglishSpacing') }}</label>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">字号与间距</h3>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.fontSize') }}</label>
            <input class="hw-input" type="number" v-model="fontSize" placeholder="recommend > 100" />
          </div>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.lineSpacing') }}</label>
            <input class="hw-input" type="number" v-model="lineSpacing" />
          </div>

          <div class="hw-grid-2">
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.topMargin')">上</label>
              <input class="hw-input" type="number" v-model="marginTop" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.bottomMargin')">下</label>
              <input class="hw-input" type="number" v-model="marginBottom" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.leftMargin')">左</label>
              <input class="hw-input" type="number" v-model="marginLeft" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.rightMargin')">右</label>
              <input class="hw-input" type="number" v-model="marginRight" />
            </div>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title hw-section-toggle" @click="toggleCollapse">
            <span>高级参数</span>
            <span class="hw-caret">{{ isExpanded ? '▼' : '▶' }}</span>
          </h3>

          <div v-if="isExpanded" class="hw-section-body">
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.lineSpacingSigma') }}</label>
              <input class="hw-input" type="number" v-model="lineSpacingSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.fontSizeSigma') }}</label>
              <input class="hw-input" type="number" v-model="fontSizeSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.wordSpacingSigma') }}</label>
              <input class="hw-input" type="number" v-model="wordSpacingSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.perturbXSigma') }}</label>
              <input class="hw-input" type="number" v-model="perturbXSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.perturbYSigma') }}</label>
              <input class="hw-input" type="number" v-model="perturbYSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.perturbThetaSigma') }}</label>
              <input class="hw-input" type="number" v-model="perturbThetaSigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.wordSpacing') }}</label>
              <input class="hw-input" type="number" v-model="wordSpacing" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.strikethrough_length_sigma') }}</label>
              <input class="hw-input" type="text" v-model="strikethrough_length_sigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.strikethrough_angle_sigma') }}</label>
              <input class="hw-input" type="number" v-model="strikethrough_angle_sigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.strikethrough_width_sigma') }}</label>
              <input class="hw-input" type="number" v-model="strikethrough_width_sigma" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.strikethrough_probability') }}</label>
              <input class="hw-input" type="number" v-model="strikethrough_probability" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.strikethrough_width') }}</label>
              <input class="hw-input" type="number" v-model="strikethrough_width" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label">{{ $t('message.ink_depth_sigma') }}</label>
              <input class="hw-input" type="number" v-model="ink_depth_sigma" />
            </div>
          </div>
        </section>
      </aside>

      <!-- MIDDLE: EDITOR (text input) -->
      <main class="hw-pane hw-editor">
        <TextInput slim ref="textInputComp"
          @childEvent="(eventData) => { this.text = eventData }"
          @manual-input="clearLetterFormatBackup"
          @file-uploaded="handleTextFileUploaded"></TextInput>
      </main>

      <!-- RIGHT: PREVIEW -->
      <aside class="hw-pane hw-pane-preview">
        <div class="hw-preview-header">
          <h2 class="hw-preview-title">{{ $t('message.preview') }}</h2>
          <span v-if="previewImages && previewImages.length > 1" class="hw-preview-page-info">
            共 {{ previewImages.length }} 页
          </span>
        </div>

        <div class="hw-preview-body">
          <div v-if="isProductionSite() && text && text.length > 0" class="hw-page-hint">
            预计生成 <strong>{{ estimatePageCount() }}</strong> 页
            <span v-if="estimatePageCount() > 10" class="hw-page-hint-warn">
              （线上限制最多 10 页，超出部分将被截断）
            </span>
          </div>

          <div class="hw-preview-images">
            <template v-if="previewImages && previewImages.length > 0">
              <div v-for="(img, idx) in previewImages" :key="idx" class="hw-preview-image-item">
                <img :src="img" :alt="$t('message.previewImage') + ' ' + (idx + 1)" />
                <div v-if="previewImages.length > 1" class="hw-preview-page-label">
                  第 {{ idx + 1 }} 页 / 共 {{ previewImages.length }} 页
                </div>
              </div>
            </template>
            <div v-else class="hw-preview-image-item">
              <img :src="previewImage" :alt="$t('message.previewImage')" />
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- STATUS BAR -->
    <div class="hw-statusbar">
      <div class="hw-statusbar-left">
        <span class="hw-status-item" v-if="text">字数: {{ text.length }}</span>
        <span class="hw-status-item" v-if="text && text.length > 0">预计页数: {{ estimatePageCount() }}</span>
        <span class="hw-status-item hw-status-generating" v-if="isGenerating">🔄 生成中…</span>
        <span class="hw-status-item hw-status-cooldown" v-else-if="isInCooldownPeriod">
          ⏳ 冷却中 {{ remainingCooldown }}s
        </span>
        <span class="hw-status-item hw-status-idle" v-else>就绪</span>
      </div>
      <div class="hw-statusbar-right">
        <span class="hw-status-item">{{ $t('message.projectAddress') }}:
          <a href="https://github.com/14790897/handwriting-web" class="hw-link">GitHub</a>
        </span>
        <span class="hw-status-item hw-status-tip">{{ $t('message.freeprompt') }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import TextInput from './TextInput.vue';
import ChineseLetterFormatter from '../components/ChineseLetterFormatter.vue';
import Swal from 'sweetalert2';



export default {
  // props: {
  //   login_delete_message: {
  //     type: Boolean,
  //     default: false
  //   }
  // },
  components: {
    TextInput,
    ChineseLetterFormatter,

  },

  data() {
    return {
      text: "",
      fontFile: null,
      backgroundImage: null,
      fontSize: 124,
      lineSpacing: 200,
      fill: "(0, 0, 0, 255)",
      width: 2481,
      height: 3507,
      marginTop: 50,
      marginBottom: 50,
      marginLeft: 50,
      marginRight: 50,
      previewImage: "/default1.webp", // 添加一个新的数据属性来保存预览图片的 URL
      previewImages: [], // 用于存储多页预览图片的数组
      currentPreviewIndex: 0, // 当前预览的图片索引
      preview: false,
      lineSpacingSigma: 0,
      fontSizeSigma: 2,
      wordSpacingSigma: 2,
      perturbXSigma: 3,
      perturbYSigma: 3,
      perturbThetaSigma: 0.05,
      wordSpacing: 1,
      endChars: '',
      errorMessage: '',  // 错误消息
      message: '',  // 提示消息
      uploadMessage: '',  // 上传提示消息
      selectedFontFileName: '',
      selectedImageFileName: '',
      //字体下拉选框
      selectedOption: '1',  // 当前选中的选项
      options: '',  // 下拉选项
      isLoading: false, //7.6
      strikethrough_length_sigma: 2,
      strikethrough_angle_sigma: 2,
      strikethrough_width_sigma: 2,
      strikethrough_probability: 0.005,
      strikethrough_width: 8,
      ink_depth_sigma: 30,
      isUnderlined: true,
      enableEnglishSpacing: false,
      isExpanded: false,
      // 生成状态控制
      isGenerating: false,
      lastGenerateTime: 0,
      generateCooldown: 3000, // 3秒冷却时间
      cooldownTimer: null,
      remainingCooldown: 0,
      isInCooldownPeriod: false,
      // 队列满倒计时
      queueFullCountdown: 0,        // 当前剩余秒数，>0 时展示提示
      queueFullTotal: 0,            // 初始等待秒数，用于计算进度条
      queueFullTimer: null,         // setInterval 句柄
      enableFullPreview: false,
      showSidebar: true,
      showHelp: false,
      showLetterFormatter: false,
      letterFormatBackup: null,
      uploadedFileName: '',
      localStorageItems: ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma', 'isUnderlined', 'enableEnglishSpacing'],
      persistentUiItems: ['selectedPreset', 'enableFullPreview'],
      selectedPreset: '',
      builtinPresets: {
        smallUnderlined: {
          fontName: '云烟体.ttf',
          values: {
            fontSize: 70,
            lineSpacing: 100,
            width: 2481,
            height: 3507,
            marginTop: 150,
            marginBottom: 150,
            marginLeft: 150,
            marginRight: 150,
            lineSpacingSigma: 1,
            fontSizeSigma: 1,
            wordSpacingSigma: 2,
            perturbXSigma: 1,
            perturbYSigma: 1,
            perturbThetaSigma: 0.05,
            wordSpacing: 2,
            strikethrough_length_sigma: 2,
            strikethrough_angle_sigma: 2,
            strikethrough_width_sigma: 2,
            strikethrough_probability: 0,
            strikethrough_width: 8,
            ink_depth_sigma: 30,
            isUnderlined: true,
            enableEnglishSpacing: false,
          },
        },
      },
    };
  },
  created() {

    // const localStorageItems = ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing'];//, 'backgroundImage', 'selectedImageFileName'

    [...this.localStorageItems, ...this.persistentUiItems].forEach(item => {
      const value = localStorage.getItem(item);
      if (value !== null && value !== "undefined") {
        try {
          this[item] = JSON.parse(value);
          console.log('成功加载localStorage项目:', item, '值:', this[item]);
        } catch (error) {
          console.error('解析localStorage项目失败:', item, '原始值:', value, '错误:', error);
        }
      } else {
        console.log('localstorage缺失item:' + item)
      }
    });

    if (
      typeof this.selectedPreset !== 'string' ||
      (this.selectedPreset && !this.builtinPresets[this.selectedPreset])
    ) {
      this.selectedPreset = '';
    }
    if (typeof this.enableFullPreview !== 'boolean') {
      this.enableFullPreview = false;
    }

    this.$http.get('/api/fonts_info').then(response => {
      this.options = response.data.map((font, index) => {
        return { value: String(index + 1), text: font };
      });
    }).catch(error => {
      if (error.response && error.response.data) {
        this.errorMessage = error.response.data.error;
        this.message = '';
        this.uploadMessage = '';
      } else {
        this.errorMessage = error;
        this.message = '';
        this.uploadMessage = '';
      }
    });
    console.log('options' + this.options)
  },
  computed: {
    isDimensionSpecified() {
      // 当宽度或高度有值时，返回 true，这会禁用背景图片输入框
      return !!(this.width || this.height);
    },
    isBackgroundImageSpecified() {
      // 当有背景图片时，返回 true，这会禁用宽度和高度输入框
      return !!this.backgroundImage;
    },

    // 按钮是否应该被禁用
    shouldDisableButtons() {
      return this.isGenerating || this.isInCooldownPeriod || this.queueFullCountdown > 0;
    },

    // 队列满进度条（从100%倒减到0%）
    queueFullBarPercent() {
      if (this.queueFullTotal <= 0) return 0;
      return Math.max(0, (this.queueFullCountdown / this.queueFullTotal) * 100);
    },

    // 按钮显示文本
    buttonText() {
      if (this.isGenerating) {
        return '生成中...';
      } else if (this.isInCooldownPeriod) {
        return `请等待 ${this.remainingCooldown}s`;
      }
      return null; // 使用默认文本
    },
    isDevEnv() {
      return process.env.NODE_ENV === 'development';
    },

    //vuex中的login_delete_message，下面使用watch监控这个值  7.13
    ...mapState(['login_delete_message']),
  },
  watch: {
    login_delete_message(newVal) {
      if (newVal) {
        // this.message = '';
        // this.uploadMessage = '';
        console.log('已进入watch，错误消息已经清空');
      }
    },
    errorMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'error',
          title: newVal,
          showConfirmButton: false,
          timer: 5000,
          timerProgressBar: true,
        });
      }
    },
    message(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'success',
          title: newVal,
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true,
        });
      }
    },
    uploadMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'info',
          title: newVal,
          showConfirmButton: false,
          timer: false, // 上传提示保持显示
          showClass: { popup: 'swal2-show' },
          hideClass: { popup: 'swal2-hide' },
        });
      }
    },
    queueFullCountdown(newVal) {
      if (newVal > 0) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'warning',
          title: `服务器繁忙，队列已满，预计 ${newVal} 秒后可重试`,
          showConfirmButton: false,
          timer: newVal * 1000,
          timerProgressBar: true,
          didOpen: (toast) => {
            const progressBar = toast.querySelector('.swal2-timer-progress-bar');
            if (progressBar && this.queueFullTotal > 0) {
              // 更新进度条
              const updateProgress = () => {
                if (this.queueFullCountdown > 0 && progressBar) {
                  const percent = (this.queueFullCountdown / this.queueFullTotal) * 100;
                  progressBar.style.width = percent + '%';
                  requestAnimationFrame(updateProgress);
                }
              };
              requestAnimationFrame(updateProgress);
            }
          },
        });
      }
    },
    text: {
      handler(newVal) {
        localStorage.setItem('text', JSON.stringify(newVal));
      },
      deep: true
    },
    fontFile: {
      handler(newVal) {
        localStorage.setItem('fontFile', JSON.stringify(newVal));
      },
      deep: true
    },
    // backgroundImage: {
    //   handler(newVal) {
    //     localStorage.setItem('backgroundImage', JSON.stringify(newVal));
    //   },
    //   deep: true
    // },
    fontSize: {
      handler(newVal) {
        localStorage.setItem('fontSize', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacing: {
      handler(newVal) {
        localStorage.setItem('lineSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    fill: {
      handler(newVal) {
        localStorage.setItem('fill', JSON.stringify(newVal));
      },
      deep: true
    },
    width: {
      handler(newVal) {
        localStorage.setItem('width', JSON.stringify(newVal));
      },
      deep: true
    },
    height: {
      handler(newVal) {
        localStorage.setItem('height', JSON.stringify(newVal));
      },
      deep: true
    },
    marginTop: {
      handler(newVal) {
        localStorage.setItem('marginTop', JSON.stringify(newVal));
      },
      deep: true
    },
    marginBottom: {
      handler(newVal) {
        localStorage.setItem('marginBottom', JSON.stringify(newVal));
      },
      deep: true
    },
    marginLeft: {
      handler(newVal) {
        localStorage.setItem('marginLeft', JSON.stringify(newVal));
      },
      deep: true
    },
    marginRight: {
      handler(newVal) {
        localStorage.setItem('marginRight', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedFontFileName: {
      handler(newVal) {
        localStorage.setItem('selectedFontFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedImageFileName: {
      handler(newVal) {
        localStorage.setItem('selectedImageFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedOption: {
      handler(newVal) {
        localStorage.setItem('selectedOption', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('lineSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    fontSizeSigma: {
      handler(newVal) {
        localStorage.setItem('fontSizeSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('wordSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbXSigma: {
      handler(newVal) {
        localStorage.setItem('perturbXSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbYSigma: {
      handler(newVal) {
        localStorage.setItem('perturbYSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbThetaSigma: {
      handler(newVal) {
        localStorage.setItem('perturbThetaSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacing: {
      handler(newVal) {
        localStorage.setItem('wordSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_length_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_length_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_angle_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_angle_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_probability: {
      handler(newVal) {
        localStorage.setItem('strikethrough_probability', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width', JSON.stringify(newVal));
      },
      deep: true
    },
    ink_depth_sigma: {
      handler(newVal) {
        localStorage.setItem('ink_depth_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    isUnderlined: {
      handler(newVal) {
        localStorage.setItem('isUnderlined', JSON.stringify(newVal));
      },
      deep: true
    },
    enableEnglishSpacing: {
      handler(newVal) {
        localStorage.setItem('enableEnglishSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedPreset(newVal) {
      localStorage.setItem('selectedPreset', JSON.stringify(newVal));
    },
    enableFullPreview(newVal) {
      localStorage.setItem('enableFullPreview', JSON.stringify(newVal));
    },
  },

  methods: {
    prevPage() {
      if (this.currentPreviewIndex > 0) {
        this.currentPreviewIndex--;
      }
    },
    nextPage() {
      if (this.currentPreviewIndex < this.previewImages.length - 1) {
        this.currentPreviewIndex++;
      }
    },
    toggleCollapse() {
      this.isExpanded = !this.isExpanded;
    },
    toggleFullPreview() {
      this.enableFullPreview = !this.enableFullPreview;
    },
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
    },
    triggerTextUpload() {
      const tx = this.$refs.textInputComp;
      if (tx && typeof tx.triggerTextFileInput === 'function') {
        tx.triggerTextFileInput();
      }
    },
    openLetterFormatter() {
      if (!this.text || !this.text.trim()) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'info',
          title: this.$t('message.letterTextRequired'),
          showConfirmButton: false,
          timer: 2200,
        });
        return;
      }
      this.showLetterFormatter = true;
    },
    applyLetterFormatting(formattedText) {
      const tx = this.$refs.textInputComp;
      if (!tx || typeof tx.replaceText !== 'function') return;

      this.letterFormatBackup = this.text;
      tx.replaceText(formattedText);
      this.showLetterFormatter = false;
      this.message = this.$t('message.letterFormatApplied');
    },
    undoLetterFormatting() {
      const tx = this.$refs.textInputComp;
      if (!tx || typeof tx.replaceText !== 'function' || this.letterFormatBackup === null) return;

      const previousText = this.letterFormatBackup;
      this.letterFormatBackup = null;
      tx.replaceText(previousText);
    },
    clearLetterFormatBackup() {
      this.letterFormatBackup = null;
    },
    handleTextFileUploaded(name) {
      this.uploadedFileName = name;
      this.letterFormatBackup = null;
    },
    startQueueFullCountdown(seconds) {
      // 清掉旧计时器
      if (this.queueFullTimer) {
        clearInterval(this.queueFullTimer);
        this.queueFullTimer = null;
      }
      this.queueFullTotal = seconds;
      this.queueFullCountdown = seconds;
      this.queueFullTimer = setInterval(() => {
        this.queueFullCountdown -= 1;
        if (this.queueFullCountdown <= 0) {
          this.queueFullCountdown = 0;
          clearInterval(this.queueFullTimer);
          this.queueFullTimer = null;
        }
      }, 1000);
    },
    updateTaskUploadMessage(taskData, taskId) {
      const taskStatus = taskData?.task_status;
      const taskMessage = taskData?.task_message || '任务处理中';
      const taskProgress = taskData?.task_progress;
      const queuePendingCount = taskData?.queue_pending_count;
      const queueAheadCount = taskData?.queue_ahead_count;
      const processingCount = taskData?.processing_count;
      if (taskStatus === 'pending' && typeof queuePendingCount === 'number' && typeof queueAheadCount === 'number') {
        if (typeof processingCount === 'number') {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人，处理中 ${processingCount} 人） Task ID: ${taskId}`;
        } else {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人） Task ID: ${taskId}`;
        }
      } else if (typeof taskProgress === 'number') {
        this.uploadMessage = `${taskMessage}（${taskProgress}%） Task ID: ${taskId}`;
      } else {
        this.uploadMessage = `${taskMessage} Task ID: ${taskId}`;
      }
    },
    async waitForTaskViaWebSocket(taskId, timeoutMs = 5 * 60 * 1000) {
      return new Promise((resolve, reject) => {
        let isSettled = false;
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/api/generate_handwriting/ws/${taskId}`;
        const socket = new WebSocket(wsUrl);

        const timeoutId = setTimeout(() => {
          if (isSettled) return;
          isSettled = true;
          try {
            socket.close();
          } catch (e) {
            // ignore close errors
          }
          reject(new Error('WebSocket任务等待超时'));
        }, timeoutMs);

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data?.status === 'error') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.message || '任务不存在'));
              return;
            }

            this.updateTaskUploadMessage(data, taskId);
            if (data?.task_status === 'completed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              resolve();
            } else if (data?.task_status === 'failed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.error_message || '任务执行失败'));
            }
          } catch (e) {
            // ignore malformed payload
          }
        };

        socket.onerror = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接失败'));
        };

        socket.onclose = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接已关闭'));
        };
      });
    },
    async pollGenerationTask(taskId, timeoutMs = 5 * 60 * 1000, intervalMs = 1500) {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const statusResponse = await this.$http.get(`/api/generate_handwriting/task/${taskId}`);
        const taskStatus = statusResponse.data?.task_status;
        this.updateTaskUploadMessage(statusResponse.data, taskId);
        if (taskStatus === 'completed') {
          return;
        }
        if (taskStatus === 'failed') {
          throw new Error(statusResponse.data?.error_message || '任务执行失败');
        }
        await new Promise(resolve => setTimeout(resolve, intervalMs));
      }
      throw new Error('任务处理超时，请重试');
    },
    filenameFromResponse(response, fallbackExt) {
      const cd = response.headers && (response.headers['content-disposition']
        || response.headers['Content-Disposition']);
      if (cd) {
        const m = /filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i.exec(cd);
        if (m && m[1]) {
          try { return decodeURIComponent(m[1]); } catch (_) { return m[1]; }
        }
      }
      const ts = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      const stamp = `${ts.getFullYear()}${pad(ts.getMonth() + 1)}${pad(ts.getDate())}-` +
        `${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}`;
      return `handwriting-${stamp}.${fallbackExt}`;
    },
    handleGenerationResultResponse(response) {
      const contentType = response.headers['content-type'] || '';
      if (contentType.includes('application/json')) {
        // 处理多页预览图像 (JSON)
        if (response.data && response.data.status === 'success') {
          this.previewImages = response.data.images.map(img => 'data:image/png;base64,' + img);
          this.currentPreviewIndex = 0; // 重置为第一页
          if (this.previewImages.length > 0) {
            this.previewImage = this.previewImages[0]; // 兼容显示第一页
          }
          this.message = '预览图像已加载。';
          this.uploadMessage = '';
          this.errorMessage = '';
        }
      } else if (contentType.includes('image/png')) {
        // 兼容旧的单张图片返回逻辑
        const blobUrl = URL.createObjectURL(response.data);
        // 将预览图像的 URL 保存到数据属性中
        this.previewImage = blobUrl;
        this.previewImages = [blobUrl];
        // 设置提示信息
        this.message = '预览图像已加载。';//显示message时，隐藏其他提示信息
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/zip')) {
        // 处理.zip文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', this.filenameFromResponse(response, 'zip'));
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除，7.5
        document.body.removeChild(link);
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/pdf')) {
        // 处理.pdf文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', this.filenameFromResponse(response, 'pdf'));
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除
        document.body.removeChild(link);
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';
      } else {
        // console.log(text);
        console.error(`Unexpected response type: ${contentType}, ${response.data}`);
      }
    },
    async generateHandwriting(preview = false, pdf_save = false) {
      // console.log('pdf_save', pdf_save)

      // 检查是否正在生成
      if (this.isGenerating) {
        this.$swal.fire({
          icon: 'warning',
          title: '正在生成中，请稍候...',
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 检查冷却时间
      const currentTime = Date.now();
      const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
      if (timeSinceLastGenerate < this.generateCooldown) {
        const remainingTime = Math.ceil((this.generateCooldown - timeSinceLastGenerate) / 1000);
        this.$swal.fire({
          icon: 'warning',
          title: `请等待 ${remainingTime} 秒后再次生成`,
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 设置生成状态
      this.isGenerating = true;
      this.lastGenerateTime = currentTime;

      // 启动冷却时间定时器
      this.startCooldownTimer();

      try {
        // 检查是否为生产环境并进行页数限制
        if (!preview && this.isProductionSite()) {
          const estimatedPages = this.estimatePageCount();
          if (estimatedPages > 15) {
            const confirmed = await this.showPageLimitDialog(estimatedPages);
            if (!confirmed) {
              return; // 用户取消生成
            }
            // 用户确认继续，在前端截断文本到前15页
            this.truncateTextToPages(15);
          }
        }

      // 验证输入
      const Items = ['text', 'backgroundImage', 'fontSize', 'lineSpacing', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma'];
      Items.forEach(item => {
        let value = this[item];
        // if (!value) {
        //   console.error(`Missing value for ${item}`);
        //   return;
        // }
        // 对不同的输入进行不同的验证
        switch (item) {
          case 'text':
            // 验证 text 是否是字符串
            if (typeof value !== 'string') {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入字符串';
            }
            // return;
            break;
          case 'fontSize':
          case 'lineSpacing':
          case 'marginTop':
          case 'marginBottom':
          case 'marginLeft':
          case 'marginRight':
          case 'lineSpacingSigma':
          case 'fontSizeSigma':
          case 'wordSpacingSigma':
          case 'perturbXSigma':
          case 'perturbYSigma':
          case 'perturbThetaSigma':
          case 'wordSpacing':
          case 'strikethrough_length_sigma':
          case 'strikethrough_angle_sigma':
          case 'strikethrough_width_sigma':
          case 'strikethrough_probability':
          case 'strikethrough_width':
          case 'ink_depth_sigma':
            // 验证这些值是否是数字
            if (isNaN(Number(value))) {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入数字';
            }
            // return
            break;
          case 'backgroundImage':
            // 验证 backgroundImage 是否是有效的 URL 或者文件路径
            // 这可能需要更复杂的验证
            break;
          default:
            console.error(`Unknown item: ${item}`);
        }
      });

      if (this.height < this.marginTop + this.lineSpacing + this.marginBottom && this.isDimensionSpecified) {
        this.errorMessage = '上边距、下边距和行间距之和不能大于高度';
        this.message = '';
        this.uploadMessage = '';
        return;
      }
      if (this.fontSize > this.lineSpacing) {
        this.errorMessage = '字体大小不能大于行间距';
        this.message = '';
        this.uploadMessage = '';
        return;
      }

      this.preview = preview;
      // this.pdf_save = pdf_save;
      // 设置提示信息为“内容正在上传…”
      this.uploadMessage = '内容正在上传并处理…（如果长时间没有响应说明服务器崩溃）单次请求最多处理五分钟，超过这个时间则失败';//显示上传提示信息时，隐藏其他提示信息
      console.log('内容正在上传并处理…');
      this.message = '';
      this.errorMessage = '';
      const formData = new FormData();
      formData.append("text", this.text);
      // 只有当用户选择的字体文件名与字体下拉选项中的字体文件名相同时，才上传字体文件7.5
      if (this.options[this.selectedOption - 1].text == this.selectedFontFileName) {
        formData.append("font_file", this.fontFile);
      }
      formData.append("background_image", this.backgroundImage);
      formData.append("font_size", this.fontSize);
      formData.append("line_spacing", this.lineSpacing);
      formData.append("fill", this.fill);
      if (this.width) {
        formData.append("width", this.width);
      }
      if (this.height) {
        formData.append("height", this.height);
      }
      formData.append("top_margin", this.marginTop);
      formData.append("bottom_margin", this.marginBottom);
      formData.append("left_margin", this.marginLeft);
      formData.append("right_margin", this.marginRight);
      formData.append("line_spacing_sigma", this.lineSpacingSigma);
      formData.append("font_size_sigma", this.fontSizeSigma);
      formData.append("word_spacing_sigma", this.wordSpacingSigma);
      formData.append("end_chars", this.endChars);
      formData.append("perturb_x_sigma", this.perturbXSigma);
      formData.append("perturb_y_sigma", this.perturbYSigma);
      formData.append("perturb_theta_sigma", this.perturbThetaSigma);
      formData.append("word_spacing", this.wordSpacing);
      formData.append("preview", this.preview.toString());
      formData.append("font_option", this.options[this.selectedOption - 1].text);
      formData.append("strikethrough_length_sigma", this.strikethrough_length_sigma);
      formData.append("strikethrough_angle_sigma", this.strikethrough_angle_sigma);
      formData.append("strikethrough_width_sigma", this.strikethrough_width_sigma);
      formData.append("strikethrough_probability", this.strikethrough_probability);
      formData.append("strikethrough_width", this.strikethrough_width);
      formData.append("ink_depth_sigma", this.ink_depth_sigma);
      formData.append("pdf_save", pdf_save.toString());
      formData.append("isUnderlined", this.isUnderlined.toString());
      formData.append("enableEnglishSpacing", this.enableEnglishSpacing.toString());
      
      // 根据环境与按钮决定是否启用多页预览
      const isDevEnv = process.env.NODE_ENV === 'development';
      const allowFullPreview = isDevEnv && this.enableFullPreview && preview;
      formData.append("full_preview", allowFullPreview.toString());

      for (let pair of formData.entries()) {
        console.log(pair[0] + ', ' + pair[1]);
      }

      const taskCreateResponse = await this.$http.post(
        '/api/generate_handwriting',
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          withCredentials: true, //在跨域的时候，需要添加这句话，才能发送cookie 6.30
        }
      );

      const taskId = taskCreateResponse.data?.task_id;
      if (!taskId) {
        throw new Error('未获取到任务ID');
      }

      this.uploadMessage = `任务已提交，正在生成中（Task ID: ${taskId}）…`;
      try {
        await this.waitForTaskViaWebSocket(taskId);
      } catch (wsError) {
        console.warn('WebSocket不可用，降级为轮询模式', wsError);
        await this.pollGenerationTask(taskId);
      }

      const resultResponse = await this.$http.get(
        `/api/generate_handwriting/task/${taskId}/result`,
        {
          // 预览模式下：开发环境使用json接收多页图片，生产环境使用blob接收单页图片
          responseType: preview ? (allowFullPreview ? 'json' : 'blob') : 'blob',
          withCredentials: true,
        }
      );
      this.handleGenerationResultResponse(resultResponse);
      } catch (error) {
        if (error.response) {
          // ── 队列已满：503 queue_full ────────────────────────────────
          const errData = error.response.data;
          if (
            error.response.status === 503 &&
            errData?.status === 'queue_full'
          ) {
            const waitSec = errData.estimated_wait_seconds || 30;
            this.startQueueFullCountdown(waitSec);
            this.message = '';
            this.uploadMessage = '';
            this.errorMessage = '';
            return; // 不走通用错误展示
          }
          // ────────────────────────────────────────────────────────────
          // console.log('已进入报错处理程序')
          // 如果服务器返回了一个JSON错误消息
          if (error.response.data instanceof Blob) {
            let reader = new FileReader();
            reader.onload = (e) => {
              try {
                let errorData = JSON.parse(e.target.result);
                this.errorMessage = errorData.message;
              } catch (parseError) {
                // 如果解析失败，直接显示原始信息
                this.errorMessage = e.target.result;
                console.log('非JSON格式的错误数据：', e.target.result);
              }
              this.message = '';
              this.uploadMessage = '';
              console.log('错误信息：', this.errorMessage);
              console.log(error);
            };//注意，这里只能使用箭头函数，不然this指向全局对象window，6.30
            reader.readAsText(error.response.data);
          } else {
            this.errorMessage = error.response.data?.message || '生成失败，请稍后重试';
            // this.errorMessage = error.response.data.message;
            this.message = '';
            this.uploadMessage = '';
          }
        } else {
          // 如果没有从服务器收到响应
          this.errorMessage = error.message || '网络错误，请稍后再试';
          this.message = '';
          this.uploadMessage = '';
        }
      } finally {
        // 重置生成状态，但保持冷却状态
        this.isGenerating = false;
        // 冷却定时器会自动处理冷却状态的重置
      }
    },
    applyPreset() {
      const key = this.selectedPreset;
      if (!key) return;
      const preset = this.builtinPresets[key];
      if (!preset) return;

      Object.keys(preset.values).forEach(k => {
        this[k] = preset.values[k];
      });

      // Match preset font against /api/fonts_info dropdown; clear any
      // uploaded font so the backend uses the built-in via font_option.
      if (preset.fontName && Array.isArray(this.options)) {
        const match = this.options.find(o => o.text === preset.fontName);
        if (match) {
          this.selectedOption = match.value;
          this.fontFile = null;
          this.selectedFontFileName = '';
        }
      }

      this.$swal.fire({
        icon: 'success',
        title: this.$t('message.presetApplied'),
        timer: 1500,
        showConfirmButton: false,
      });
    },
    savePreset() {
      try {
        let data = {};
        this.localStorageItems.forEach(item => {
          data[item] = this[item];
        });
        // 将对象转换为 JSON 格式的字符串
        let dataString = JSON.stringify(data);

        // 将字符串存储到 localStorage 中
        localStorage.setItem('myPreset', dataString);

        this.$swal.fire({
          icon: 'success',
          title: '预设设置保存成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('保存预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '保存预设设置失败',
        });
      }
    },
    resetSettings() {
      // this.text = '';13213不能删除，会导致文字为空，但是输入框没有清除
      this.fontFile = null;
      this.backgroundImage = null;
      this.fontSize = 124;
      this.lineSpacing = 200;
      this.fill = "(0, 0, 0, 255)";
      this.width = 2481;
      this.height = 3507;
      this.marginTop = 50;
      this.marginBottom = 50;
      this.marginLeft = 50;
      this.marginRight = 50;
      this.lineSpacingSigma = 0;
      this.fontSizeSigma = 2;
      this.wordSpacingSigma = 2;
      this.perturbXSigma = 3;
      this.perturbYSigma = 3;
      this.perturbThetaSigma = 0.05;
      this.wordSpacing = 1;
      this.strikethrough_length_sigma = 2;
      this.strikethrough_angle_sigma = 2;
      this.strikethrough_width_sigma = 2;
      this.strikethrough_probability = 0.005;
      this.strikethrough_width = 8;
      this.ink_depth_sigma = 30;
      this.isUnderlined = true;
      this.enableEnglishSpacing = false;
      this.errorMessage = '';
      this.message = '';
      this.uploadMessage = '';
      this.selectedFontFileName = '';
      this.selectedImageFileName = '';
      this.selectedOption = '1';
      this.selectedPreset = '';
      this.previewImage = "/default1.webp";
    },
    loadPreset() {
      try {
        // 从 localStorage 中获取字符串
        let dataString = localStorage.getItem('myPreset');

        if (dataString === null || dataString === "undefined") {
          this.$swal.fire({
            icon: 'info',
            title: '没有找到保存的预设设置',
          });
          return;
        }

        // 将字符串转换回对象
        let data = JSON.parse(dataString);
        Object.keys(data).forEach(item => {
          this[item] = data[item];
        });
        this.selectedPreset = '';

        this.$swal.fire({
          icon: 'success',
          title: '预设设置加载成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('加载预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '加载预设设置失败，请检查保存的数据是否有效',
        });
      }
    },
    onBackgroundImageChange(event) {
      // 当用户选择了一个新的背景图片文件时，更新 selectedImageFileName，由于这边直接触发函数了，所以localstorage可以在这里修改，
      //之前因为文字不能触发函数，所以要放在watch里面
      this.selectedImageFileName = event.target.files[0].name;
      this.backgroundImage = event.target.files[0];
      // 由于文件无法在浏览器存储，所以下面的代码无效 7.15
      // localStorage.setItem('backgroundImage', JSON.stringify(this.backgroundImage));
      // if (localStorage.getItem('backgroundImage')) {
      //   console.log('Data successfully saved to localStorage.');
      // } else {
      //   console.log('Failed to save to localStorage.');
      // }

      this.previewImage = URL.createObjectURL(event.target.files[0]);
      Swal.fire({
        title: '你希望自动识别页面的四周边距吗？（尽量不要上传带有alpha透明通道的图片）',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          let formData = new FormData();
          formData.append('file', this.backgroundImage);  // 'file' 是你在服务器端获取文件数据时的 key
          this.isLoading = true;
          this.$http.post(
            '/api/imagefileprocess',
            formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
            .then(response => {
              this.marginLeft = response.data.marginLeft;
              this.marginRight = response.data.marginRight;
              this.marginTop = response.data.marginTop - this.lineSpacing;
              this.marginBottom = response.data.marginBottom;
              this.lineSpacing = response.data.lineSpacing;
              this.message = '背景图片已加载。';
              this.errorMessage = '';
              this.uploadMessage = '';
              this.isLoading = false;
            })
            .catch(error => {
              console.error(error);
              this.errorMessage = error.response.data.error;
              this.message = '';
              this.uploadMessage = '';
              this.isLoading = false;
            });
        }
      })
    },
    onFontChange(event) {
      // 当用户选择了一个新的字体文件时，更新 selectedFontFileName
      this.selectedFontFileName = event.target.files[0].name;
      this.fontFile = event.target.files[0];
      // 创建一个新的 option 对象
      const newOption = {
        value: String(this.options.length + 1), // 使用 options 数组的长度 + 1 作为新选项的 value
        text: this.selectedFontFileName // 使用字体文件名作为新选项的 text
      };

      // 将新选项添加到 options 数组中
      this.options.push(newOption);

      // 将 selectedOption 设为新选项的 value，这样下拉菜单就会自动更新为新添加的字体
      this.selectedOption = newOption.value;

    },
    triggerImageFileInput() {
      if (!this.isDimensionSpecified) {
        this.$refs.imageFileInput.click();
      }
      else {
        Swal.fire({
          title: '需要先清空高度宽度才能选择图片',
          text: '选择图片后需要点击按钮左下角的X删除图片才能再输入宽度高度',
          icon: 'question',
          showCancelButton: true,
          confirmButtonText: '清空宽度高度',
          cancelButtonText: '取消'
        }).then((result) => {
          if (result.isConfirmed) {
            this.width = null
            this.height = null
            this.$refs.imageFileInput.click();
          }
        })
      }
    },
    triggerFontFileInput() {
      this.$refs.fontFileInput.click();
    },
    //清空图像按钮对应的函数
    clearImage() {
      // 清空存储图像信息的变量
      this.selectedImageFileName = null;
      this.backgroundImage = null;
      // 清空文件输入框
      this.$refs.imageFileInput.value = null;
    },
    clearDimensions() {
      console.log('清空图像尺寸');
      this.width = null
      this.height = null
    },

    // 检查是否为生产网站
    isProductionSite() { // localhost:8080 handwrite.14790897.xyz
      return window.location.hostname === 'handwrite.14790897.xyz';
    },

    // 估算页数
    estimatePageCount() {
      if (!this.text || this.text.length === 0) {
        return 0;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ? 2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数（粗略估算，中文字符按字体大小计算）
      const avgCharWidth = fontSize * 0.8; // 中文字符宽度约为字体大小的0.8倍
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 估算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算页数
      const estimatedPages = Math.ceil(this.text.length / charsPerPage);

      console.log('页数估算:', {
        textLength: this.text.length,
        charsPerLine,
        linesPerPage,
        charsPerPage,
        estimatedPages
      });

      return estimatedPages;
    },

    // 显示页数限制对话框
    async showPageLimitDialog(estimatedPages) {
      try {
        const result = await this.$swal.fire({
          title: '页数限制提醒',
          html: `
            <div style="text-align: left; line-height: 1.6;">
              <p><strong>检测到您的文本预计会生成 ${estimatedPages} 页</strong></p>
              <p>由于服务器资源限制，在 <strong>handwrite.14790897.xyz</strong> 网站上单次最多只能生成 <strong>10页</strong>。</p>
              <p>如果您选择继续：</p>
              <ul style="margin: 10px 0; padding-left: 20px;">
                <li>系统将只生成前 10 页内容</li>
                <li>超出部分将被自动截断</li>
                <li>建议您分批处理长文本</li>
              </ul>
              <p style="color: #666; font-size: 14px;">
                💡 提示：您可以将长文本分成多个部分，分别生成，或者自行搭建本项目来处理更长的文本
              </p>
              <p style="color: #888; font-size: 12px; margin-top: 10px;">
                注：此限制仅适用于 handwrite.14790897.xyz 网站
              </p>
            </div>
          `,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: '继续生成（前10页）',
          cancelButtonText: '取消',
          confirmButtonColor: '#f39c12',
          cancelButtonColor: '#d33',
          width: '500px'
        });

        return result.isConfirmed;
      } catch (error) {
        console.error('SweetAlert2 error:', error);
        // 降级到原生 confirm
        return confirm(`检测到您的文本预计会生成 ${estimatedPages} 页。\n\n由于服务器资源限制，在 handwrite.14790897.xyz 网站上单次最多只能生成 10页。\n\n是否继续生成前10页？`);
      }
    },

    // 截断文本到指定页数
    truncateTextToPages(maxPages) {
      if (!this.text || this.text.length === 0) {
        return;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ?2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数
      const avgCharWidth = fontSize * 0.8;
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 计算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算最大字符数
      const maxChars = charsPerPage * maxPages;

      // 截断文本
      if (this.text.length > maxChars) {
        const originalLength = this.text.length;
        this.text = this.text.substring(0, maxChars);

        console.log('文本截断:', {
          originalLength,
          truncatedLength: this.text.length,
          maxPages,
          charsPerPage,
          maxChars
        });

      }
    },

    // 启动冷却时间定时器
    startCooldownTimer() {
      // 清除现有定时器
      if (this.cooldownTimer) {
        clearInterval(this.cooldownTimer);
      }

      // 设置初始冷却状态
      this.isInCooldownPeriod = true;
      this.remainingCooldown = Math.ceil(this.generateCooldown / 1000);

      // 启动新定时器，每1秒更新一次显示
      this.cooldownTimer = setInterval(() => {
        const currentTime = Date.now();
        const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
        const remaining = this.generateCooldown - timeSinceLastGenerate;

        if (remaining <= 0) {
          // 冷却结束
          this.isInCooldownPeriod = false;
          this.remainingCooldown = 0;
          clearInterval(this.cooldownTimer);
          this.cooldownTimer = null;
        } else {
          // 更新剩余时间
          this.remainingCooldown = Math.ceil(remaining / 1000);
        }
      }, 1000);
    },

  },

  // 组件销毁时清理定时器
  beforeUnmount() {
    if (this.cooldownTimer) {
      clearInterval(this.cooldownTimer);
      this.cooldownTimer = null;
    }
  },

};
</script>


<style scoped>
.container {
  display: grid;
  grid-template-areas:
    "form image"
    "button image"
    "message image";
  grid-template-columns: 1fr 2fr;
}

#message {
  grid-area: message;
  padding: 20px;
  box-sizing: border-box;
  overflow: auto;
  /* box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); */
}

#form {
  grid-area: form;
  flex: 1 0 300px;
  max-width: 650px;
  column-count: auto;
  column-width: 200px;
  column-gap: 1em;
  width: 80vw;
  padding: 20px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: auto;
  box-shadow: 0 -1px 5px rgba(0, 0, 0, 0.1);
}

#form label {
  margin-bottom: 10px;
}

#form input,
#form textarea {
  width: 50%;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  box-sizing: border-box;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}


/* 想让标签和输入在一行显示，但是没有用 7.14 */
.label-container {
  display: flex;
  /* justify-content: center; */
  align-items: center;
}
.buttons{
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
.buttons button {
  grid-area: button;
  padding: 10px 10px;
  border-radius: 5px;
  border: none;
  background: #007BFF;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
  font-weight: bold;
  /* 使文本更粗 */
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  /* 添加阴影效果 */
  outline: none;
  /* 移除默认的焦点轮廓 */
  margin-right: 10px;
  /* 为每个按钮添加右边距 */
  margin-top: 10px;
}

.buttons button:last-child {
  margin-right: 0;
  /* 为最后一个按钮移除右边距，避免额外空间 */
}

.buttons button:hover {
  background: #0056b3;
  transform: scale(1.05);
  /* 悬停时按钮轻微放大 */
}

.buttons button:active {
  background: #003d73;
  /* 按下按钮时更改背景色 */
  transform: scale(0.95);
  /* 按下按钮时按钮轻微缩小 */
}

.buttons button:disabled {
  background: #cccccc;
  /* 禁用按钮时的背景色 */
  cursor: not-allowed;
  /* 禁用按钮时的鼠标样式 */
}


.preview {
  /* flex: 1; */
  padding: 20px;
  box-sizing: border-box;
  grid-area: image;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  min-width: 100px;
  min-height: 200px;

}

.preview img {
  max-width: 100%;
  height: auto;
  object-fit: cover;
  position: sticky;
  top: 0;
}

input[type="number"],
input[type="text"],
input[type="file"] {
  transition: all 0.3s ease;
  /* 过渡效果 */
}

input[type="number"]:hover,
input[type="text"]:hover,
input[type="file"]:hover {
  transform: scale(1.05);
  /* 放大输入框 */
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
  /* 添加阴影效果 */
}

/* >>> .TextInput{ */
.container_file {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: auto;
}

.container_file label {
  font-size: 1.2rem;
  font-weight: 500;
}

.container_file button {
  padding: 10px 5px;
  font-size: 0.9rem;
  color: white;
  background-color: #4285f4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin: 0 auto;
}

.container_file button:disabled {
  background-color: grey;
}

.container_file span {
  /* display: block; */
  margin-top: 5px;
  font-size: 0.9rem;
  color: #444;
}

/* } */
.styled-select {
  padding: 10px;
  border: none;
  border-radius: 5px;
  color: white;
  background-color: #4285f4;
  font-size: 1rem;
  transition: all 0.3s ease-in-out;


}

.styled-select:hover {
  transform: scale(1.05);
  /* 放大输入框 */
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
}

.styled-select:focus {
  outline: none;
}

.button-container {
  display: flex;
  justify-content: space-around;
  position: relative;
}

.clear-button {
  position: relative;
  top: 5px;
  right: 5px;
  width: 12px;
  height: 12px;
  cursor: pointer;
}

.clear-button-line {
  position: absolute;
  left: 1px;
  width: 10px;
  height: 2px;
  background-color: #000;
}

.clear-button-line:first-child {
  top: 5px;
  transform: rotate(45deg);
}

.clear-button-line:last-child {
  top: 5px;
  transform: rotate(-45deg);
}

.font-selection {
  display: flex;
  justify-content: space-around;
}

.loader {
  border: 16px solid #f3f3f3;
  /* Light grey */
  border-top: 16px solid #3498db;
  /* Blue */
  border-radius: 50%;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
  position: absolute;
  /* 设置动画为绝对定位 */
  top: 50%;
  /* 将动画定位在父元素的中心 */
  left: 50%;
  transform: translate(-50%, -50%);
  /* 用 transform 属性将动画元素的中心对准父元素的中心 */
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.image-container {
  /* display: flex;
  justify-content: center;
  align-items: center; */
  position: relative;
  margin-bottom: 15px;
}

.close {
  border: none !important;
}

.button-disabled {
  background-color: #ccc !important;
  color: #666 !important;
  cursor: not-allowed !important;
}

.optionUnderline {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.optionEnglishSpacing {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.freeprompt {
  font-size: 0.8rem;
  color: #e70808;
  text-align: center;
  margin-top: 10px;
}
@media (max-width: 1000px) {
  .container {
    /* flex-direction: column; */
    grid-template-areas:
      "form"
      "button"
      "message"
      "image";
    grid-template-columns: 1fr;
  }

  #form,
  .preview {
    flex: 1 0 100%;
  }
}

/* 生成状态提示样式 */
.generation-status {
  margin: 15px 0;
  padding: 10px;
  border-radius: 5px;
  text-align: center;
  font-weight: bold;
  animation: pulse 2s infinite;
}

.status-generating {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.status-cooldown {
  background-color: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffcc02;
}

/* 队列已满提示 - 已迁移到 Swal Toast */

/* ============================================
   Editor-style split layout (hw-* namespace)
   ============================================ */

.hw-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  background: #fff;
  color: #1f2328;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
    "Microsoft YaHei", sans-serif;
  overflow: hidden;
}

/* ----- Top toolbar ----- */
.hw-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: #f6f8fa;
  border-bottom: 1px solid #d0d7de;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.hw-toolbar-section {
  display: flex;
  align-items: center;
  gap: 6px;
}

.hw-toolbar-left { flex: 0 0 auto; }
.hw-toolbar-center { flex: 0 1 auto; }
.hw-toolbar-right { flex: 1 1 auto; justify-content: flex-end; flex-wrap: wrap; }

.hw-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2328;
  letter-spacing: 0.3px;
}

.hw-toolbar-label {
  font-size: 13px;
  color: #57606a;
  margin: 0;
}

/* ----- Buttons ----- */
.hw-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 30px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
  background: #fff;
  color: #24292f;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.hw-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #afb8c1;
}

.hw-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.hw-btn-sm {
  height: 26px;
  padding: 0 8px;
  font-size: 12px;
}

.hw-btn-primary {
  background: #0969da;
  color: #fff;
  border-color: #0969da;
}
.hw-btn-primary:hover:not(:disabled) {
  background: #0860c7;
  border-color: #0860c7;
}

.hw-btn-success {
  background: #1f883d;
  color: #fff;
  border-color: #1f883d;
}
.hw-btn-success:hover:not(:disabled) {
  background: #1a7234;
  border-color: #1a7234;
}

.hw-btn-ghost {
  background: transparent;
  border-color: transparent;
  color: #57606a;
}
.hw-btn-ghost:hover:not(:disabled) {
  background: #eaeef2;
  color: #1f2328;
}

.hw-btn-letter {
  gap: 6px;
  color: #7f3029;
  background: #fffaf0;
  border-color: #d8b5aa;
}

.hw-btn-letter:hover:not(:disabled) {
  color: #69251f;
  background: #f8ebe5;
  border-color: #bd8175;
}

.hw-btn-letter-mark {
  width: 17px;
  height: 17px;
  display: inline-grid;
  place-items: center;
  color: #fffaf0;
  background: #963b32;
  border-radius: 3px;
  font-family: "Songti SC", "STSong", serif;
  font-size: 11px;
  line-height: 1;
}

.hw-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  font-size: 16px;
  line-height: 1;
  background: transparent;
  color: #57606a;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
}
.hw-icon-btn:hover {
  background: #eaeef2;
  color: #cf222e;
}

/* ----- Form controls ----- */
.hw-input,
.hw-select {
  height: 30px;
  padding: 0 8px;
  font-size: 13px;
  background: #fff;
  color: #1f2328;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.hw-input:focus,
.hw-select:focus {
  border-color: #0969da;
  box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.15);
}

.hw-input:disabled {
  background: #f6f8fa;
  color: #8c959f;
  cursor: not-allowed;
}

.hw-input { width: 120px; }
.hw-select { min-width: 160px; }
.hw-select-grow { flex: 1 1 auto; min-width: 0; }

/* ----- Alerts ----- */
.hw-alerts {
  padding: 8px 16px 0;
  flex-shrink: 0;
}
.hw-alert {
  margin: 0 0 6px;
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
}

/* ----- Split body ----- */
.hw-split {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.hw-pane {
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

/* Sidebar: collapsible settings panel */
.hw-sidebar {
  flex: 0 0 300px;
  padding: 0;
  border-right: 1px solid #d0d7de;
  background: #fafbfc;
  display: flex;
  flex-direction: column;
}

.hw-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #eaeef2;
  background: #f6f8fa;
  flex-shrink: 0;
}

.hw-sidebar-title {
  font-size: 13px;
  font-weight: 600;
  color: #1f2328;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.hw-sidebar .hw-section {
  margin: 0;
  padding: 12px 14px;
  border-bottom: 1px solid #eaeef2;
}
.hw-sidebar .hw-section:last-child { border-bottom: none; }

.hw-sidebar-toggle {
  font-size: 14px;
}

/* Editor: pure text input pane */
.hw-editor {
  flex: 1 1 50%;
  min-width: 0;
  padding: 16px 20px;
  background: #fff;
  border-right: 1px solid #d0d7de;
  display: flex;
  flex-direction: column;
}

.hw-editor > * {
  flex: 1 1 auto;
  min-height: 0;
}

.hw-pane-preview {
  flex: 1 1 50%;
  min-width: 0;
  padding: 20px 24px;
  background: #f6f8fa;
}

/* ----- Form sections ----- */
.hw-section {
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #eaeef2;
}
.hw-section:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.hw-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #57606a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hw-section-toggle {
  cursor: pointer;
  user-select: none;
}
.hw-section-toggle:hover { color: #1f2328; }

.hw-caret {
  font-size: 11px;
  color: #8c959f;
}

.hw-section-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ----- Field (label + control) ----- */
.hw-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}
.hw-field:last-child { margin-bottom: 0; }

.hw-field-inline {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.hw-field-inline .hw-field-label {
  flex: 0 0 96px;
  margin: 0;
  text-align: right;
}

.hw-field-inline .hw-input {
  flex: 1 1 auto;
  width: auto;
  max-width: 220px;
}

.hw-field-label {
  font-size: 13px;
  color: #1f2328;
  font-weight: 500;
}

.hw-field-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hw-field-checkbox {
  flex-direction: row;
  align-items: center;
  gap: 8px;
}
.hw-field-checkbox label {
  font-size: 13px;
  margin: 0;
  cursor: pointer;
}

.hw-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hw-row-tight {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.hw-row-tight .hw-btn {
  flex: 1 1 auto;
}

.hw-grid-2 {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 6px 10px;
  margin-top: 4px;
}

.hw-grid-2 .hw-field-inline {
  min-width: 0;
  gap: 6px;
}

.hw-grid-2 .hw-field-inline .hw-field-label {
  flex: 0 0 auto;
  text-align: right;
}

.hw-grid-2 .hw-field-inline .hw-input {
  min-width: 0;
  flex: 1 1 0;
}

.hw-filename {
  font-size: 12px;
  color: #0969da;
  padding: 2px 6px;
  background: #ddf4ff;
  border-radius: 4px;
  word-break: break-all;
}

.hw-toolbar-filename {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: normal;
}

/* ----- Preview pane ----- */
.hw-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #d0d7de;
}

.hw-preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2328;
  margin: 0;
}

.hw-preview-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hw-preview-page-info {
  font-size: 13px;
  color: #57606a;
  min-width: 60px;
  text-align: center;
}

.hw-preview-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hw-page-hint {
  padding: 8px 12px;
  background: #fff8c5;
  border: 1px solid #d4a72c;
  border-radius: 6px;
  font-size: 13px;
  color: #633c01;
}
.hw-page-hint-warn { color: #cf222e; font-weight: 500; }

.hw-preview-image {
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.hw-preview-image img {
  max-width: 100%;
  height: auto;
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

/* Scrollable multi-page preview */
.hw-preview-images {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.hw-preview-image-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.hw-preview-image-item img {
  max-width: 100%;
  height: auto;
  background: #fff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.hw-preview-page-label {
  font-size: 12px;
  color: #57606a;
  padding: 2px 8px;
  background: #eaeef2;
  border-radius: 10px;
}

/* ----- Status bar ----- */
.hw-statusbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 16px;
  background: #f6f8fa;
  border-top: 1px solid #d0d7de;
  font-size: 12px;
  color: #57606a;
  flex-shrink: 0;
  gap: 16px;
}

.hw-statusbar-left,
.hw-statusbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.hw-status-item { white-space: nowrap; }

.hw-status-generating { color: #0969da; font-weight: 500; }
.hw-status-cooldown { color: #bf8700; font-weight: 500; }
.hw-status-idle { color: #1a7f37; }
.hw-status-tip { color: #8c959f; font-style: italic; }

.hw-link { color: #0969da; text-decoration: none; }
.hw-link:hover { text-decoration: underline; }

/* ----- Help button + modal ----- */
.hw-help-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #d0d7de;
  border-radius: 50%;
  font-weight: 700;
  color: #57606a;
}
.hw-help-btn:hover {
  background: #eaeef2;
  color: #0969da;
  border-color: #0969da;
}

.hw-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.hw-modal {
  width: 520px;
  max-width: calc(100vw - 40px);
  max-height: calc(100vh - 80px);
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hw-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #eaeef2;
  background: #f6f8fa;
}

.hw-modal-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2328;
}

.hw-modal-body {
  padding: 18px;
  overflow-y: auto;
}

.hw-help-intro {
  font-size: 13px;
  color: #57606a;
  margin: 0 0 16px;
}

.hw-help-item {
  display: flex;
  gap: 14px;
  padding: 12px 0;
  border-top: 1px solid #eaeef2;
}

.hw-help-syntax {
  flex: 0 0 64px;
}
.hw-help-syntax code {
  display: inline-block;
  padding: 3px 8px;
  background: #eff1f3;
  border-radius: 5px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 14px;
  color: #cf222e;
  font-weight: 600;
}

.hw-help-desc {
  flex: 1 1 auto;
  font-size: 13px;
  line-height: 1.6;
  color: #1f2328;
}
.hw-help-desc code {
  padding: 1px 5px;
  background: #eff1f3;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  color: #cf222e;
}

.hw-help-example {
  margin: 8px 0 0;
  padding: 10px 12px;
  background: #f6f8fa;
  border: 1px solid #eaeef2;
  border-radius: 6px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #1f2328;
  white-space: pre-wrap;
}

/* ----- Responsive ----- */
@media (max-width: 900px) {
  .hw-split { flex-direction: column; }
  .hw-pane-form {
    flex: 0 0 auto;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #d0d7de;
    max-height: 50vh;
  }
  .hw-pane-preview { flex: 1 1 auto; }
  .hw-toolbar { gap: 8px; }
  .hw-toolbar-section { flex-wrap: wrap; }
}

</style>
