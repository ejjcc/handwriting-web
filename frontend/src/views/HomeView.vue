<template>
  <div class="hw-app" data-testid="app-shell">
    <header class="hw-header" data-testid="app-header">
    <!-- TOP TOOLBAR -->
    <div class="hw-toolbar">
      <div class="hw-toolbar-section hw-toolbar-left">
        <button class="hw-icon-btn hw-sidebar-toggle" data-testid="sidebar-toggle-btn" @click="toggleSidebar"
          :title="showSidebar ? '收起设置' : '展开设置'">
          {{ showSidebar ? '◀' : '☰' }}
        </button>
        <span class="hw-title">手写生成器</span>
      </div>

      <div class="hw-toolbar-section hw-toolbar-center">
        <button class="hw-btn hw-btn-sm" @click="triggerTextUpload" data-testid="text-file-btn"
          :title="$t('message.orUploadDocument') + ' (.doc/.docx/.pdf/.txt/.rtf)'">
          📄 上传文档
        </button>
        <button class="hw-btn hw-btn-sm hw-btn-letter" @click="openLetterFormatter" data-testid="letter-format-btn">
          <span class="hw-btn-letter-mark" aria-hidden="true">信</span>
          {{ $t('message.formatChineseLetter') }}
        </button>
        <button v-if="letterFormatBackup !== null" class="hw-btn hw-btn-sm hw-btn-ghost"
          @click="undoLetterFormatting" data-testid="letter-undo-btn">
          {{ $t('message.letterUndo') }}
        </button>
        <span v-if="uploadedFileName" class="hw-filename hw-toolbar-filename" data-testid="text-file-name" :title="uploadedFileName">
          {{ uploadedFileName }}
        </span>
      </div>

      <div class="hw-toolbar-section hw-toolbar-right">
        <button class="hw-btn hw-btn-primary" @click="generateHandwriting(preview = true)" data-testid="preview-btn"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.preview') }}
        </button>
        <button v-if="isDevEnv" class="hw-btn hw-btn-ghost" @click="toggleFullPreview" data-testid="full-preview-toggle-btn"
          :disabled="shouldDisableButtons">
          全量预览：{{ enableFullPreview ? '开' : '关' }}
        </button>
        <button class="hw-btn hw-btn-success" @click="generateHandwriting(preview = false)" data-testid="generate-image-btn"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.generateFullHandwritingImage') }}
        </button>
        <button class="hw-btn hw-btn-success" @click="generateHandwriting(preview = false, pdf_save = true)" data-testid="generate-pdf-btn"
          :disabled="shouldDisableButtons">
          {{ buttonText || $t('message.generatePdf') }}
        </button>
        <router-link to="/Feedback" class="hw-btn hw-btn-ghost">{{ $t('message.feedback') }}</router-link>
        <button class="hw-icon-btn hw-help-btn" @click="showHelp = true" title="语法帮助" data-testid="syntax-help-btn">?</button>
      </div>
    </div>

    <ChineseLetterFormatter v-if="showLetterFormatter" :source-text="text"
      @close="showLetterFormatter = false" @apply="applyLetterFormatting" />

    <!-- HELP MODAL -->
    <div v-if="showHelp" class="hw-modal-overlay" data-testid="syntax-help-dialog" @click.self="showHelp = false">
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
      <div v-if="message" class="alert alert-info hw-alert" data-testid="message-info">{{ message }}</div>
      <div v-if="uploadMessage" class="alert alert-info hw-alert" data-testid="message-upload">{{ uploadMessage }}</div>
    </div>

    <div v-if="downloadSavedPath" class="hw-alerts" data-testid="download-saved-hint">
      <span>{{ $t('message.downloadSavedTo') }}</span>
      <span data-testid="download-saved-path">{{ downloadSavedPath }}</span>
      <button class="hw-btn hw-btn-sm" data-testid="open-download-folder-btn" @click="openDownloadFolder">{{ $t('message.openDownloadFolder') }}</button>
    </div>
    <span v-if="lastPdfDownloadBytes > 0" data-testid="pdf-download-bytes" style="display: none;">{{ lastPdfDownloadBytes }}</span>

    </header>

    <!-- 3-PANE BODY -->
    <div class="hw-split" ref="workspace" data-testid="workspace" :style="workspaceStyle" :class="{ 'sidebar-hidden': !showSidebar }">
      <!-- LEFT: SETTINGS SIDEBAR (collapsible) -->
      <aside v-if="showSidebar" class="hw-pane hw-sidebar" ref="panelSettings" data-testid="panel-settings">
        <div class="hw-sidebar-header">
          <span class="hw-sidebar-title">设置</span>
          <button class="hw-icon-btn" @click="toggleSidebar" title="收起">◀</button>
        </div>

        <section class="hw-section">
          <h3 class="hw-section-title">预设</h3>
          <div class="hw-field">
            <select :value="selectedPreset" @change="applyPreset" :disabled="!presetOptionsReady" data-testid="builtin-preset-select" class="hw-select hw-select-grow">
              <option value="">{{ $t('message.presetNone') }}</option>
              <option value="smallUnderlined">{{ $t('message.presetSmallUnderlined') }}</option>
            </select>
          </div>
          <div class="hw-row hw-row-tight">
            <button class="hw-btn hw-btn-sm" @click="loadPreset" data-testid="load-settings-btn">{{ $t('message.loadSettings') }}</button>
            <button class="hw-btn hw-btn-sm" @click="savePreset" data-testid="save-settings-btn">{{ $t('message.saveSettings') }}</button>
            <button class="hw-btn hw-btn-sm" @click="resetSettings" data-testid="reset-settings-btn">{{ $t('message.resetSettings') }}</button>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">字体 &amp; 背景</h3>

          <div class="hw-field">
            <label class="hw-field-label">{{ $t('message.fontFile') }}</label>
            <div class="hw-field-control hw-row">
              <button class="hw-btn hw-btn-sm" @click="triggerFontFileInput" data-testid="font-file-btn">{{ $t('message.chooseFile') }}</button>
              <input type="file" ref="fontFileInput" data-testid="font-file-input" @change="onFontChange" style="display: none;" />
              <select v-model="selectedOption" data-testid="font-select" class="hw-select hw-select-grow">
                <option v-for="option in options" :value="option.value" :key="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>
          </div>

          <div class="hw-field">
            <label class="hw-field-label">{{ $t('message.backgroundImageFile') }}</label>
            <div class="hw-field-control hw-row">
              <button class="hw-btn hw-btn-sm" @click="triggerImageFileInput" data-testid="background-image-btn"
                :class="{ 'button-disabled': isDimensionSpecified }"
                :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
                {{ $t('message.chooseFile') }}
                <span v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                  <span class="clear-button-line"></span>
                  <span class="clear-button-line"></span>
                </span>
              </button>
              <span class="hw-filename" v-if="selectedImageFileName">{{ selectedImageFileName }}</span>
              <input type="file" ref="imageFileInput" data-testid="background-image-input" @change="onBackgroundImageChange" style="display: none;" />
              <span v-if="isLoading" class="loader">{{ $t('message.loading') }}...</span>
            </div>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">页面与样式</h3>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.width') }}</label>
            <input class="hw-input" type="number" v-model="width" data-testid="width-input" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
          </div>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.height') }}</label>
            <input class="hw-input" type="number" v-model="height" data-testid="height-input" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
            <button type="button" class="hw-icon-btn" title="清空宽高" @click="clearDimensions">×</button>
          </div>

          <div class="hw-field hw-field-checkbox">
            <input type="checkbox" id="optionUnderline" v-model="isUnderlined" data-testid="underline-toggle" />
            <label for="optionUnderline">增加下划线</label>
          </div>

          <div class="hw-field hw-field-checkbox">
            <input type="checkbox" id="optionEnglishSpacing" v-model="enableEnglishSpacing" data-testid="english-spacing-toggle" />
            <label for="optionEnglishSpacing">{{ $t('message.enableEnglishSpacing') }}</label>
          </div>
        </section>

        <section class="hw-section">
          <h3 class="hw-section-title">字号与间距</h3>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.fontSize') }}</label>
            <input class="hw-input" type="number" v-model="fontSize" data-testid="font-size-input" placeholder="recommend > 100" />
          </div>

          <div class="hw-field hw-field-inline">
            <label class="hw-field-label">{{ $t('message.lineSpacing') }}</label>
            <input class="hw-input" type="number" v-model="lineSpacing" data-testid="line-spacing-input" />
          </div>

          <div class="hw-grid-2">
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.topMargin')">上</label>
              <input class="hw-input" type="number" v-model="marginTop" data-testid="margin-top-input" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.bottomMargin')">下</label>
              <input class="hw-input" type="number" v-model="marginBottom" data-testid="margin-bottom-input" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.leftMargin')">左</label>
              <input class="hw-input" type="number" v-model="marginLeft" data-testid="margin-left-input" />
            </div>
            <div class="hw-field hw-field-inline">
              <label class="hw-field-label" :title="$t('message.rightMargin')">右</label>
              <input class="hw-input" type="number" v-model="marginRight" data-testid="margin-right-input" />
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

      <div v-if="showSidebar" class="resizer" data-testid="resizer-settings" role="separator" aria-orientation="vertical"
        :class="{ active: resizeState && resizeState.side === 'left' }"
        :aria-label="$t('message.resizeColumnLeft')" :title="$t('message.resizeColumnHint')" tabindex="0"
        @pointerdown="startResize('left', $event)" @pointermove="onResizeMove" @pointerup="endResize"
        @pointercancel="endResize" @dblclick="resetColumnWidth('left')"
        @keydown="onResizerKeydown('left', $event)"></div>

      <!-- MIDDLE: EDITOR (text input) -->
      <main class="hw-pane hw-editor" ref="panelText" data-testid="panel-text">
        <TextInput slim ref="textInputComp"
          @childEvent="(eventData) => { this.text = eventData }"
          @manual-input="clearLetterFormatBackup"
          @file-uploaded="handleTextFileUploaded"></TextInput>
      </main>

      <div class="resizer" data-testid="resizer-preview" role="separator" aria-orientation="vertical"
        :class="{ active: resizeState && resizeState.side === 'right' }"
        :aria-label="$t('message.resizeColumnRight')" :title="$t('message.resizeColumnHint')" tabindex="0"
        @pointerdown="startResize('right', $event)" @pointermove="onResizeMove" @pointerup="endResize"
        @pointercancel="endResize" @dblclick="resetColumnWidth('right')"
        @keydown="onResizerKeydown('right', $event)"></div>

      <!-- RIGHT: PREVIEW -->
      <aside class="hw-pane hw-pane-preview" ref="panelPreview" data-testid="panel-preview">
        <div class="hw-preview-header">
          <h2 class="hw-preview-title">{{ $t('message.preview') }}</h2>
          <span v-if="previewImages && previewImages.length > 1" class="hw-preview-page-info" data-testid="preview-page-indicator">
            共 {{ previewImages.length }} 页
          </span>
        </div>

        <div class="hw-preview-body">
          <GenerationStatus :generating="isGenerating" :cooldown-seconds="remainingCooldown" :page-count="estimatedPages" />

          <div class="hw-preview-images" data-testid="preview-area">
            <template v-if="previewImages && previewImages.length > 0">
              <div v-for="(img, idx) in previewImages" :key="idx" class="hw-preview-image-item">
                <img :src="img" data-testid="preview-image" :alt="$t('message.previewImage') + ' ' + (idx + 1)" />
                <div v-if="previewImages.length > 1" class="hw-preview-page-label" data-testid="preview-page-label">
                  第 {{ idx + 1 }} 页 / 共 {{ previewImages.length }} 页
                </div>
              </div>
            </template>
            <div v-else class="hw-preview-image-item">
              <img :src="previewImage" data-testid="preview-image" :alt="$t('message.previewImage')" />
            </div>
          </div>
        </div>
      </aside>
    </div>

    <!-- STATUS BAR -->
    <div class="hw-statusbar" data-testid="site-footer">
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
        <span v-if="appVersion" class="hw-status-item" data-testid="app-version">v{{ appVersion }}</span>
        <span class="hw-status-item hw-status-tip">{{ $t('message.freeprompt') }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import TextInput from './TextInput.vue';
import ChineseLetterFormatter from '../components/ChineseLetterFormatter.vue';
import GenerationStatus from '../components/GenerationStatus.vue';
import { hasDesktopBridge } from '../desktop';
import { MAX_PAGES, buildPageLimitDialog, exceedsPageLimit } from '../utils/pageLimit.mjs';
import Swal from 'sweetalert2';

const BUILTIN_PRESETS = {
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
};



// 三栏拖动：左右两栏各自的最小宽度、中栏的最小宽度（px），
// 以及 CSS 里那条间隔轨道的宽度（分隔条的拖动热区就画在它上面）
const MIN_COLUMN_WIDTH = 200;
const MIN_MIDDLE_WIDTH = 300;
const GUTTER_WIDTH = 16;
// 分隔条拿到键盘焦点后，左右方向键每次调整的像素
const KEYBOARD_RESIZE_STEP = 20;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

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
    GenerationStatus,

  },

  data() {
    return {
      text: "",
      // 页面底部展示的版本号，来自 /api/version；取不到就不显示
      appVersion: "",
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
      lastPdfDownloadBytes: 0,  // 最近一次 PDF 下载的字节数，供 e2e 核对
      downloadSavedPath: '',  // 桌面版：主进程回传的最后一次下载的绝对路径，网页版永远是空
      selectedFontFileName: '',
      selectedImageFileName: '',
      //字体下拉选框
      selectedOption: '1',  // 当前选中的选项
      selectedPreset: '',
      builtinPresets: BUILTIN_PRESETS,
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
      uploadedFileName: '',
      // 三栏宽度：null 表示这一栏还用 CSS 里的默认轨道（左 300px / 右 1fr），
      // 拖动过一次就钉成固定像素值，中栏吃掉剩余空间
      workspaceColumns: { left: null, right: null },
      // 实际渲染用的宽度：窗口放得下时就等于 workspaceColumns，放不下才按比例收窄。
      // 和上面分开，是为了窗口重新变宽后能还原用户自己拖出来的宽度
      appliedColumns: { left: null, right: null },
      // 拖动中的临时状态：起始指针位置、起始栏宽、可用总宽，仅拖动期间存在
      resizeState: null,
      showLetterFormatter: false,
      letterFormatBackup: null,
      localStorageItems: ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma', 'isUnderlined', 'enableEnglishSpacing'],
      // 这些项在 created() 里统一从 localStorage 还原。
      // workspaceColumns 没有配 watcher：拖动过程中每帧都写一次不值得，改成收手时才落盘
      persistentUiItems: ['enableFullPreview', 'workspaceColumns'],
    };
  },
  created() {
    window.addEventListener('handwriting-text-loaded', this.onTextLoaded);

    const savedPreset = localStorage.getItem('selectedPreset');
    if (savedPreset !== null && savedPreset !== "undefined") {
      try {
        const presetKey = JSON.parse(savedPreset);
        if (typeof presetKey === 'string' && (!presetKey || this.builtinPresets[presetKey])) {
          this.selectedPreset = presetKey;
        } else {
          localStorage.removeItem('selectedPreset');
        }
      } catch (error) {
        console.error('解析内置预设失败:', error);
        localStorage.removeItem('selectedPreset');
      }
    }

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

    if (typeof this.enableFullPreview !== 'boolean') {
      this.enableFullPreview = false;
    }

    // 存档损坏（比如被别的版本写成了字符串）时退回默认布局，别让 NaN 进 CSS
    const savedColumns = this.workspaceColumns;
    const readColumn = (value) =>
      typeof value === 'number' && Number.isFinite(value) && value > 0 ? Math.round(value) : null;
    this.workspaceColumns = {
      left: readColumn(savedColumns && savedColumns.left),
      right: readColumn(savedColumns && savedColumns.right),
    };
    this.appliedColumns = { ...this.workspaceColumns };

    this.$http.get('/api/version').then(response => {
      this.appVersion = response.data?.version || '';
    }).catch(() => {
      // 版本号只是展示信息，取不到就不显示，不打扰用户
      this.appVersion = '';
    });

    this.$http.get('/api/fonts_info').then(response => {
      this.options = response.data.map((font, index) => {
        return { value: String(index + 1), text: font };
      });
      const selected = this.builtinPresets[this.selectedPreset];
      if (selected && !this.applyPresetFont(selected.fontName)) {
        this.clearSelectedPreset();
      }
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

    // 拖动过的栏宽以 CSS 变量喂给 .workspace 的 grid-template-columns；
    // 没拖动过就不写变量，由 CSS 里的默认轨道接管
    workspaceStyle() {
      const style = {};
      const { left, right } = this.appliedColumns;
      if (left) style['--col-left'] = `${left}px`;
      if (right) style['--col-right'] = `${right}px`;
      return style;
    },

    // 按钮是否应该被禁用
    shouldDisableButtons() {
      // 字体列表还没回来时不能点：请求里要取 options[selectedOption - 1].text
      if (!Array.isArray(this.options) || this.options.length === 0) return true;
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
    // 页数提示只在生产站点显示；用 computed 避免模板里反复调用 estimatePageCount()
    estimatedPages() {
      if (!this.isProductionSite() || !this.text || this.text.length === 0) {
        return 0;
      }
      return this.estimatePageCount();
    },
    presetOptionsReady() {
      const preset = this.builtinPresets.smallUnderlined;
      return Array.isArray(this.options) && this.options.some(option => option.text === preset.fontName);
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
          ...this.toastBase(),
          icon: 'error',
          title: newVal,
          timer: 5000,
          timerProgressBar: true,
        });
      }
    },
    message(newVal) {
      if (newVal) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'success',
          title: newVal,
          timer: 3000,
          timerProgressBar: true,
        });
      }
    },
    uploadMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'info',
          title: newVal,
          timer: false, // 上传提示保持显示
          showClass: { popup: 'swal2-show' },
          hideClass: { popup: 'swal2-hide' },
        });
      }
    },
    queueFullCountdown(newVal) {
      if (newVal > 0) {
        this.$swal.fire({
          ...this.toastBase((toast) => {
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
          }),
          icon: 'warning',
          title: `服务器繁忙，队列已满，预计 ${newVal} 秒后可重试`,
          timer: newVal * 1000,
          timerProgressBar: true,
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
    enableFullPreview(newVal) {
      localStorage.setItem('enableFullPreview', JSON.stringify(newVal));
    },
  },

  methods: {
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
    openLetterFormatter() {
      if (!this.text || !this.text.trim()) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'info',
          title: this.$t('message.letterTextRequired'),
          timer: 2200,
        });
        return;
      }
      this.showLetterFormatter = true;
    },
    // 顶栏操作按钮排在页面顶部，toast 固定在右上角会盖住按钮、吞掉点击。
    // 实测按钮行最右端约 1060px，加上 toast 自身 360px 宽，所以 1440px 以下改贴右下角。
    toastPosition() {
      return window.innerWidth <= 1440 ? 'bottom-end' : 'top-end';
    },
    // toast 的公共配置；didOpen 回调可选，用于叠加自定义逻辑（如队列满的进度条）
    toastBase(didOpen) {
      return {
        toast: true,
        position: this.toastPosition(),
        showConfirmButton: false,
        didOpen: (toast) => {
          // 供 e2e 选择，不依赖 SweetAlert 自己的类名
          toast.setAttribute('data-testid', 'app-toast');
          if (didOpen) didOpen(toast);
        },
      };
    },
    applyLetterFormatting(formattedText) {
      const textInput = this.$refs.textInputComp;
      if (!textInput || typeof textInput.replaceText !== 'function') return;

      if (this.letterFormatBackup === null) {
        this.letterFormatBackup = this.text;
      }
      textInput.replaceText(formattedText);
      this.showLetterFormatter = false;
      this.message = this.$t('message.letterFormatApplied');
    },
    undoLetterFormatting() {
      const textInput = this.$refs.textInputComp;
      if (!textInput || typeof textInput.replaceText !== 'function' || this.letterFormatBackup === null) return;

      const previousText = this.letterFormatBackup;
      this.letterFormatBackup = null;
      textInput.replaceText(previousText);
    },
    clearLetterFormatBackup() {
      this.letterFormatBackup = null;
    },
    // 文本文件上传是异步的；上传途中切换布局会重建 TextInput，旧实例的 emit 会被 Vue 丢弃，
    // 所以由 TextInput 广播事件，这里再把结果喂给当前活着的输入框（见 TextInput.uploadFile）
    onTextLoaded(event) {
      const loadedText = event.detail;
      if (typeof loadedText !== 'string') return;
      this.text = loadedText;
      const input = this.$refs.textInputComp;
      if (input && typeof input.replaceText === 'function' && input.text !== loadedText) {
        input.replaceText(loadedText);
      }
    },
    clearSelectedPreset() {
      this.selectedPreset = '';
      localStorage.removeItem('selectedPreset');
    },
    applyPresetFont(fontName) {
      if (!fontName || !Array.isArray(this.options)) return false;

      const match = this.options.find(option => option.text === fontName);
      if (!match) return false;

      this.selectedOption = match.value;
      this.fontFile = null;
      this.selectedFontFileName = '';
      if (this.$refs.fontFileInput) {
        this.$refs.fontFileInput.value = '';
      }
      localStorage.setItem('selectedOption', JSON.stringify(match.value));
      localStorage.setItem('fontFile', JSON.stringify(null));
      localStorage.setItem('selectedFontFileName', JSON.stringify(''));
      return true;
    },
    applyPreset(event) {
      const presetKey = event.target.value;
      const preset = this.builtinPresets[presetKey];
      if (!preset) {
        this.clearSelectedPreset();
        return;
      }

      if (this.backgroundImage && ('width' in preset.values || 'height' in preset.values)) {
        event.target.value = this.selectedPreset;
        this.$swal.fire({
          icon: 'info',
          title: this.$t('message.presetBackgroundImageActive'),
        });
        return;
      }

      if (!this.applyPresetFont(preset.fontName)) {
        event.target.value = this.selectedPreset;
        this.$swal.fire({
          icon: 'error',
          title: this.$t('message.presetUnavailable'),
        });
        return;
      }

      Object.entries(preset.values).forEach(([key, value]) => {
        this[key] = value;
        localStorage.setItem(key, JSON.stringify(value));
      });
      this.selectedPreset = presetKey;
      localStorage.setItem('selectedPreset', JSON.stringify(this.selectedPreset));

      this.$swal.fire({
        icon: 'success',
        title: this.$t('message.presetApplied'),
        timer: 1500,
        showConfirmButton: false,
      });
    },
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
      this.$nextTick(this.clampWorkspaceColumns);
    },
    triggerTextUpload() {
      this.$refs.textInputComp?.triggerTextFileInput();
    },
    handleTextFileUploaded(name) {
      this.uploadedFileName = name;
      this.letterFormatBackup = null;
    },
    // ===== 三栏宽度调整 =====
    // 量一次工作区与左右两栏的当前尺寸。拖动开始时左右两栏会被钉成此刻的像素宽度，
    // 之后只有中栏伸缩，所以 clamp 只要守住「两栏 + 两条间隔 + 中栏最小宽度 ≤ 可用宽度」
    measureWorkspaceMetrics() {
      const workspace = this.$refs.workspace;
      if (!workspace || !this.$refs.panelSettings || !this.$refs.panelPreview) return null;
      const style = getComputedStyle(workspace);
      const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
      return {
        available: workspace.getBoundingClientRect().width - padding,
        left: this.$refs.panelSettings.getBoundingClientRect().width,
        right: this.$refs.panelPreview.getBoundingClientRect().width,
      };
    },
    // 左右两栏一起钉成固定像素宽度；中栏拿走剩下的空间。拖出来的值同时是"用户要的宽度"和"当前渲染宽度"
    applyColumnWidths(left, right) {
      const columns = { left: Math.round(left), right: Math.round(right) };
      this.workspaceColumns = columns;
      this.appliedColumns = { ...columns };
    },
    // 存储不可用（隐私模式 / 配额满）时 setItem 会抛异常。这里吞掉它，
    // 否则 resetColumnWidth 里紧跟着的那次 clamp 会被跳过，布局可能停在放不下的状态
    persistWorkspaceColumns() {
      try {
        localStorage.setItem('workspaceColumns', JSON.stringify(this.workspaceColumns));
      } catch (error) {
        console.warn('保存栏宽失败:', error);
      }
    },
    startResize(side, event) {
      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      // 先把两栏都钉成当前像素宽度：中栏剩下的宽度不变（画面不跳），
      // 且拖动期间只有中栏在伸缩，上面那条 clamp 算术才成立
      this.applyColumnWidths(metrics.left, metrics.right);
      this.resizeState = {
        side,
        startX: event.clientX,
        startLeft: Math.round(metrics.left),
        startRight: Math.round(metrics.right),
        available: metrics.available,
      };
      // 指针会移出分隔条，把事件捕获到它自己身上；同时屏蔽整页的选中与光标抖动
      if (event.currentTarget.setPointerCapture) {
        event.currentTarget.setPointerCapture(event.pointerId);
      }
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    },
    onResizeMove(event) {
      const state = this.resizeState;
      if (!state) return;
      const delta = event.clientX - state.startX;
      // 另一栏此刻是钉死的，中栏最小宽度要从可用宽度里扣掉它
      const otherWidth = state.side === 'left' ? state.startRight : state.startLeft;
      const maxSide = state.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH - otherWidth;
      if (state.side === 'left') {
        const left = clamp(state.startLeft + delta, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));
        this.applyColumnWidths(left, state.startRight);
      } else {
        const right = clamp(state.startRight - delta, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));
        this.applyColumnWidths(state.startLeft, right);
      }
    },
    endResize(event) {
      if (!this.resizeState) return;
      if (event.currentTarget.releasePointerCapture && event.currentTarget.hasPointerCapture
        && event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      this.resizeState = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      this.persistWorkspaceColumns();
    },
    // 双击分隔条：这一栏退回 CSS 的弹性默认宽度（左 300px / 右 1fr）
    resetColumnWidth(side) {
      const columns = { ...this.workspaceColumns, [side]: null };
      this.workspaceColumns = columns;
      this.appliedColumns = { ...columns };
      this.persistWorkspaceColumns();
      // 另一栏还钉着的话，退回弹性列后可能放不下，按当前窗口再收一次
      this.clampWorkspaceColumns();
    },
    onResizerKeydown(side, event) {
      // 方向键朝着分隔条该走的方向推：左分隔条按 → 加宽左栏，右分隔条按 ← 加宽右栏
      const growKey = side === 'left' ? 'ArrowRight' : 'ArrowLeft';
      const shrinkKey = side === 'left' ? 'ArrowLeft' : 'ArrowRight';
      if (event.key !== growKey && event.key !== shrinkKey) return;
      event.preventDefault();

      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      const other = side === 'left' ? metrics.right : metrics.left;
      const current = side === 'left' ? metrics.left : metrics.right;
      const maxSide = metrics.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH - other;
      const step = event.key === growKey ? KEYBOARD_RESIZE_STEP : -KEYBOARD_RESIZE_STEP;
      const next = clamp(current + step, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));

      // 键盘调整也把两栏一起钉住，否则中栏的伸缩比例会和拖动时对不上
      this.applyColumnWidths(side === 'left' ? next : metrics.left, side === 'right' ? next : metrics.right);
      this.persistWorkspaceColumns();
    },
    // 窗口变窄时把渲染宽度按比例收回来，否则左右两栏会把中栏挤到最小宽度以下、整页横向溢出。
    // 只改 appliedColumns，用户拖出来的值留在 workspaceColumns 里，窗口重新变宽时能还回去
    clampWorkspaceColumns() {
      const { left, right } = this.workspaceColumns;
      if (!left && !right) return;
      const workspace = this.$refs.workspace;
      if (!workspace) return;
      // 窄屏是单栏堆叠，栏宽存的是宽屏时的值，这时候不能拿当前宽度去压它
      if (!this.$refs.panelSettings || !this.$refs.panelPreview) return;
      const settings = this.$refs.panelSettings.getBoundingClientRect();
      const preview = this.$refs.panelPreview.getBoundingClientRect();
      if (preview.left < settings.right) return;

      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      // 没钉住的那一栏按 CSS 默认轨道渲染，但占的宽度也要算进来
      const currentLeft = left || metrics.left;
      const currentRight = right || metrics.right;
      const maxTotal = metrics.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH;
      if (currentLeft + currentRight <= maxTotal) {
        this.appliedColumns = { left, right };
        return;
      }

      const scale = maxTotal / (currentLeft + currentRight);
      let nextLeft = Math.max(MIN_COLUMN_WIDTH, Math.round(currentLeft * scale));
      let nextRight = Math.max(MIN_COLUMN_WIDTH, Math.round(currentRight * scale));
      // 两侧各自有 200px 下限，按比例缩完再抬到下限后可能仍超预算，多出来的从较宽的一侧扣掉
      const excess = nextLeft + nextRight - maxTotal;
      if (excess > 0) {
        if (nextLeft > nextRight) {
          nextLeft -= excess;
        } else {
          nextRight -= excess;
        }
      }
      this.appliedColumns = { left: nextLeft, right: nextRight };
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
    // 桌面版的文件由 Electron 自己落盘，路径随后由主进程回传；网页版我们拿不到路径，
    // 只能让用户去浏览器自己的下载目录找。
    downloadedMessage() {
      return hasDesktopBridge()
        ? this.$t('message.fileDownloaded')
        : this.$t('message.fileDownloadedBrowserHint');
    },
    openDownloadFolder() {
      window.handwritingDesktop?.revealLastDownload();
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
        link.setAttribute('download', hasDesktopBridge() ? 'images.zip' : this.filenameFromResponse(response, 'zip')); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除，7.5
        document.body.removeChild(link);
        // 设置提示信息
        this.downloadSavedPath = '';  // 新的下载开始，先撤掉上次的路径
        this.message = this.downloadedMessage();
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/pdf')) {
        // 处理.pdf文件
        const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', hasDesktopBridge() ? 'images.pdf' : this.filenameFromResponse(response, 'pdf')); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除
        document.body.removeChild(link);
        // e2e 靠这个数字核对实际交付的 PDF 体积（见 e2e/tests/home-generate.spec.js）
        this.lastPdfDownloadBytes = pdfBlob.size;
        // 设置提示信息
        this.downloadSavedPath = '';  // 新的下载开始，先撤掉上次的路径
        this.message = this.downloadedMessage();
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
          if (exceedsPageLimit(estimatedPages)) {
            const confirmed = await this.showPageLimitDialog(estimatedPages);
            if (!confirmed) {
              return; // 用户取消生成
            }
            // 用户确认继续，在前端截断文本到上限页数
            this.truncateTextToPages(MAX_PAGES);
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
      this.clearSelectedPreset();
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
        this.clearSelectedPreset();

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
      this.clearSelectedPreset();
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
      this.clearSelectedPreset();
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
      const dialog = buildPageLimitDialog(estimatedPages);
      try {
        const result = await this.$swal.fire({
          title: dialog.title,
          html: dialog.html,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: dialog.confirmText,
          cancelButtonText: '取消',
          confirmButtonColor: '#f39c12',
          cancelButtonColor: '#d33',
          width: '500px'
        });

        return result.isConfirmed;
      } catch (error) {
        console.error('SweetAlert2 error:', error);
        // 降级到原生 confirm
        return confirm(dialog.fallbackConfirmText);
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

  mounted() {
    // 还原出来的栏宽是按当初那个窗口算的，进页面时先按当前窗口收一次
    this.clampWorkspaceColumns();
    window.addEventListener('resize', this.clampWorkspaceColumns);

    // 桌面版：下载完成后主进程回传文件落在哪（见 desktop/main.js 的 setupDownloads）。
    // 网页版没有这座桥，走 downloadedMessage() 里那句「去浏览器下载目录找」。
    if (hasDesktopBridge()) {
      window.handwritingDesktop.onDownloadFinished(({ file, state }) => {
        this.downloadSavedPath = state === 'completed' ? file : '';
        this.message = state === 'completed'
          ? this.$t('message.fileDownloaded')
          : this.$t('message.downloadFailed');
      });
    }
  },

  // 组件销毁时清理定时器
  beforeUnmount() {
    window.removeEventListener('handwriting-text-loaded', this.onTextLoaded);
    window.removeEventListener('resize', this.clampWorkspaceColumns);

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

.resizer {
  position: relative;
  cursor: col-resize;
  /* 触控设备上把手势交给 pointer 事件，别让它变成滚动 */
  touch-action: none;
}

.resizer:focus {
  outline: none;
}

.resizer::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  margin-left: -1px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.15s;
}

.resizer:hover::before {
  background: #9db3cf;
}

.resizer:focus-visible::before,
.resizer.active::before {
  background: #007BFF;
}

/* 保留编辑器三栏与连续预览，接入上游的栏宽调整。 */
@media (min-width: 1001px) {
  .hw-split {
    display: grid;
    grid-template-columns: var(--col-left, 300px) 16px minmax(0, 1fr) 16px var(--col-right, minmax(0, 1fr));
  }
  .hw-split.sidebar-hidden {
    grid-template-columns: minmax(0, 1fr) 16px var(--col-right, minmax(0, 1fr));
  }
}
@media (max-width: 1000px) {
  .resizer { display: none; }
}

.hw-header { flex: 0 0 auto; }
@media (max-width: 1000px) {
  .hw-app { height: auto; min-height: 100dvh; overflow: visible; }
  .hw-split { flex: none; flex-direction: column; overflow: visible; }
  .hw-pane { height: auto; overflow: visible; }
  .hw-sidebar { flex: none; width: 100%; }
  .hw-editor { flex: none; min-height: 400px; }
  .hw-pane-preview { flex: none; min-height: 400px; }
}
</style>
