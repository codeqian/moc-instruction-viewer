/**
 * 3D Viewer —— 基于 Three.js 的 LDraw 模型渲染器
 */
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { LDrawLoader } from "three/examples/jsm/loaders/LDrawLoader.js";
import { LineMaterial } from "three/examples/jsm/lines/LineMaterial.js";

export class Viewer {
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

  // ---- 场景 ----

  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a2e);
  }

  // ---- 相机 ----

  _initCamera() {
    const container = this.canvas.parentElement;
    const aspect = container.clientWidth / container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.5, 5000);
    this.camera.position.set(0, 0, -50);
    this.camera.up.set(0, -1, 0);
    this.camera.lookAt(0, 0, 0);
  }

  // ---- 灯光 ----

  _initLights() {
    const hemi = new THREE.HemisphereLight(0x444444, 0xffffff, 1.2);
    this.scene.add(hemi);

    // 主光：从模型上方（世界 -Y）照射
    const key = new THREE.DirectionalLight(0xffffff, 0.9);
    key.position.set(30, -200, 40);
    this.scene.add(key);

    // 补光
    const fill = new THREE.DirectionalLight(0xffffff, 0.5);
    fill.position.set(-40, -150, -30);
    this.scene.add(fill);
  }

  // ---- 交互 ----

  _initControls() {
    this.controls = new OrbitControls(this.camera, this.canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.minDistance = 1;
    this.controls.maxDistance = 2000;
    this.controls.target.set(0, 0, 0);
    this.controls.update();
  }

  // ---- 模型加载器 ----

  _initLoader() {
    this.loader = new LDrawLoader();
    this.loader.partsLibraryPath = "/api/ldraw/";
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

    const render = () => {
      requestAnimationFrame(render);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    render();
  }

  // ---- 公开方法 ----

  loadModel(url) {
    return new Promise((resolve, reject) => {
      this._clearModel();

      this.loader.load(
        url,
        (group) => {
          group.traverse((child) => {
            if (child.isLineSegments2 || child.isLineSegments) {
              child.visible = false;
            }
          });
          this.currentModel = group;
          this.scene.add(group);
          this._fitCameraToObject(group);
          resolve(group);
        },
        (progress) => {
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

  resetCamera() {
    if (this.currentModel) {
      this._fitCameraToObject(this.currentModel);
    } else {
      this.camera.position.set(0, 0, -50);
      this.camera.up.set(0, -1, 0);
      this.controls.target.set(0, 0, 0);
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
      if (child.geometry) child.geometry.dispose();
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

    this.camera.position.set(
      center.x,
      center.y,
      center.z - distance
    );
    this.camera.up.set(0, -1, 0);
    this.controls.target.copy(center);
    this.controls.saveState();
    this.controls.update();
  }
}
