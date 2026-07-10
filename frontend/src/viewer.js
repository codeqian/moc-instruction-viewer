/**
 * 3D Viewer —— 基于 Three.js 的 LDraw 模型渲染器
 *
 * 职责：
 * - 初始化 Three.js 场景、相机、灯光
 * - 加载 packed MPD 文件并渲染
 * - 支持旋转、缩放、平移、重置视角
 * - 管理当前模型的添加 / 移除
 */
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { LDrawLoader } from "three/examples/jsm/loaders/LDrawLoader.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

export class Viewer {
  /**
   * @param {HTMLCanvasElement} canvas
   */
  constructor(canvas) {
    this.canvas = canvas;
    this.currentModel = null;

    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._initLoader();
    this._initResize();

    this._animate();
  }

  // ---- 初始化 ----

  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a2e);
    this.scene.fog = new THREE.Fog(0x1a1a2e, 50, 500);
  }

  _initCamera() {
    const container = this.canvas.parentElement;
    const aspect = container.clientWidth / container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.5, 5000);
    this.camera.position.set(0, 10, -50);
    this.camera.lookAt(0, 0, 0);
  }

  _initLights() {
    // 环境光
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(ambient);

    // 主方向光
    const key = new THREE.DirectionalLight(0xffffff, 0.8);
    key.position.set(10, 20, 15);
    this.scene.add(key);

    // 补光
    const fill = new THREE.DirectionalLight(0xffffff, 0.3);
    fill.position.set(-10, 5, -10);
    this.scene.add(fill);

    // 底部补光
    const rim = new THREE.DirectionalLight(0xffffff, 0.2);
    rim.position.set(0, -5, 0);
    this.scene.add(rim);
  }

  _initControls() {
    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 1;
    this.controls.maxDistance = 2000;
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  _initLoader() {
    this.loader = new LDrawLoader();
    // 零件库路径（前端按需从后端拉取）
    this.loader.partsLibraryPath = "/api/ldraw/";
    // Three.js r170+ 必须设置条件线材质
    this.loader.setConditionalLineMaterial(LineMaterial);
  }

  _initResize() {
    const container = this.canvas.parentElement;
    const ro = new ResizeObserver(() => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;

      this.renderer.setSize(w, h, false);
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
    });
    ro.observe(container);
  }

  // ---- 渲染循环 ----

  _animate() {
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;

    const render = () => {
      requestAnimationFrame(render);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    render();
  }

  // ---- 公开方法 ----

  /**
   * 加载 packed MPD 模型
   * @param {string} url - packed MPD 接口路径
   */
  loadModel(url) {
    return new Promise((resolve, reject) => {
      this._clearModel();

      this.loader.load(
        url,
        (group) => {
          this.currentModel = group;
          this.scene.add(group);
          this._fitCameraToObject(group);
          resolve(group);
        },
        (progress) => {
          // 可选：进度回调
          if (progress.total > 0) {
            const pct = Math.round((progress.loaded / progress.total) * 100);
            console.debug(`加载进度: ${pct}%`);
          }
        },
        (error) => {
          console.error("模型加载失败:", error);
          reject(error);
        }
      );
    });
  }

  /**
   * 重置相机视角
   */
  resetCamera() {
    if (this.currentModel) {
      this._fitCameraToObject(this.currentModel);
    } else {
      this.camera.position.set(0, 10, -50);
      this.controls.target.set(0, 10, 0);
      this.controls.update();
    }
  }

  // ---- 内部方法 ----

  _clearModel() {
    if (this.currentModel) {
      this.scene.remove(this.currentModel);
      this._disposeObject(this.currentModel);
      this.currentModel = null;
    }
  }

  _disposeObject(obj) {
    obj.traverse((child) => {
      if (child.geometry) {
        child.geometry.dispose();
      }
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose());
        } else {
          child.material.dispose();
        }
      }
    });
  }

  _fitCameraToObject(object) {
    const box = new THREE.Box3().setFromObject(object);
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);

    const maxDim = Math.max(size.x, size.y, size.z);
    const distance = maxDim * 2.0;

    // 正面略微俯视：Z 轴负方向（模型前方），Y 轴略高
    this.camera.position.set(
      center.x,
      center.y + distance * 0.3,
      center.z - distance
    );
    this.controls.target.copy(center);
    this.controls.update();
  }
}
