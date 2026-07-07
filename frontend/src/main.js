/**
 * 应用入口 —— 初始化 Viewer 并绑定 UI 控制
 */
import { Viewer } from "./viewer.js";

// ---- 从 URL 解析模型 ID ----
function getModelIdFromURL() {
  const path = window.location.pathname;
  const match = path.match(/\/viewer\/([a-zA-Z0-9_]+)/);
  if (match) return match[1];

  // 开发阶段：尝试从 search params 读取
  const params = new URLSearchParams(window.location.search);
  return params.get("id") || "10001";
}

// ---- DOM 元素 ----
const elModelName = document.getElementById("model-name");
const elStepInfo = document.getElementById("step-info");
const elLoading = document.getElementById("loading-overlay");
const elError = document.getElementById("error-overlay");
const elErrorMsg = document.getElementById("error-message");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const btnReset = document.getElementById("btn-reset");

// ---- 应用状态 ----
const modelId = getModelIdFromURL();
let viewer = null;
let currentStep = 1;
let totalSteps = 0;

// ---- 初始化 ----
async function init() {
  try {
    showLoading(true);

    // 获取模型元信息
    const meta = await fetch(`/api/models/${modelId}/meta`).then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    });

    elModelName.textContent = meta.name || modelId;
    totalSteps = meta.totalSteps || 0;

    // 初始化 3D Viewer
    const canvas = document.getElementById("viewer-canvas");
    viewer = new Viewer(canvas);

    if (meta.hasSteps && totalSteps > 0) {
      // 分步模式：先加载第一步
      showStepInfo();
      updateNavButtons();
      await loadStep(1);
    } else {
      // 完整模型模式
      elStepInfo.classList.add("hidden");
      btnPrev.classList.add("hidden");
      btnNext.classList.add("hidden");
      await loadFullModel();
    }

    showLoading(false);
  } catch (err) {
    showLoading(false);
    showError(`图纸加载失败: ${err.message}`);
    console.error(err);
  }
}

// ---- 模型加载 ----
async function loadFullModel() {
  showLoading(true);
  hideError();

  try {
    await viewer.loadModel(`/api/models/${modelId}/packed`);
  } catch (err) {
    showError("图纸文件加载失败，请联系客服。");
    console.error(err);
  }

  showLoading(false);
}

async function loadStep(stepNo) {
  showLoading(true);
  hideError();

  try {
    await viewer.loadModel(`/api/models/${modelId}/steps/${stepNo}`);
    currentStep = stepNo;
    updateNavButtons();
    showStepInfo();
  } catch (err) {
    showError(`步骤 ${stepNo} 加载失败。`);
    console.error(err);
  }

  showLoading(false);
}

// ---- UI 更新 ----
function showStepInfo() {
  elStepInfo.classList.remove("hidden");
  elStepInfo.textContent = `第 ${currentStep} / ${totalSteps} 步`;
}

function updateNavButtons() {
  btnPrev.disabled = currentStep <= 1;
  btnNext.disabled = currentStep >= totalSteps;
}

function showLoading(visible) {
  elLoading.classList.toggle("hidden", !visible);
}

function showError(message) {
  elError.classList.remove("hidden");
  elErrorMsg.textContent = message;
}

function hideError() {
  elError.classList.add("hidden");
}

// ---- 按钮事件 ----
btnPrev.addEventListener("click", () => {
  if (currentStep > 1) {
    loadStep(currentStep - 1);
  }
});

btnNext.addEventListener("click", () => {
  if (currentStep < totalSteps) {
    loadStep(currentStep + 1);
  }
});

btnReset.addEventListener("click", () => {
  if (viewer) {
    viewer.resetCamera();
  }
});

// ---- 键盘事件 ----
document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") {
    btnPrev.click();
  } else if (e.key === "ArrowRight") {
    btnNext.click();
  } else if (e.key === "r" || e.key === "R") {
    btnReset.click();
  }
});

// 启动
init();
