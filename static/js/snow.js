/**
 * Let it Snow Effect
 * Canvas 기반 눈 내리는 애니메이션
 * LocalStorage로 on/off 설정 저장
 */

(function () {
    'use strict';

    const config = {
        maxFlakes: 400,
        minSize: 2,
        maxSize: 5,
        minSpeed: 1,
        maxSpeed: 3,
        wind: 0.5,
        color: 'rgba(255, 255, 255, 0.9)'
    };

    let canvas, ctx;
    let snowflakes = [];
    let animationId = null;
    let isRunning = false;

    // 눈송이 클래스
    class Snowflake {
        constructor() {
            this.reset();
        }

        reset() {
            this.x = Math.random() * (canvas ? canvas.width : window.innerWidth);
            this.y = Math.random() * -100;
            this.size = Math.random() * (config.maxSize - config.minSize) + config.minSize;
            this.speed = Math.random() * (config.maxSpeed - config.minSpeed) + config.minSpeed;
            this.wind = (Math.random() - 0.5) * config.wind;
            this.opacity = Math.random() * 0.5 + 0.5;
            this.swing = Math.random() * 2;
            this.swingSpeed = Math.random() * 0.05;
        }

        update() {
            this.y += this.speed;
            this.x += this.wind + Math.sin(this.swing) * 0.5;
            this.swing += this.swingSpeed;

            // 화면 밖으로 나가면 리셋
            if (this.y > canvas.height || this.x < -10 || this.x > canvas.width + 10) {
                this.reset();
                this.y = -10;
            }
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
            ctx.fill();
        }
    }

    function createCanvas() {
        canvas = document.createElement('canvas');
        canvas.id = 'snow-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            display: none;
        `;
        document.body.appendChild(canvas);
        ctx = canvas.getContext('2d');
        resizeCanvas();
    }

    function resizeCanvas() {
        if (canvas) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
    }

    function initSnowflakes() {
        snowflakes = [];
        for (let i = 0; i < config.maxFlakes; i++) {
            const flake = new Snowflake();
            flake.y = Math.random() * canvas.height; // 초기 위치 랜덤
            snowflakes.push(flake);
        }
    }

    function animate() {
        if (!isRunning) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        snowflakes.forEach(flake => {
            flake.update();
            flake.draw();
        });

        animationId = requestAnimationFrame(animate);
    }

    function startSnow() {
        if (isRunning) return;

        isRunning = true;
        canvas.style.display = 'block';
        initSnowflakes();
        animate();
        localStorage.setItem('snowEnabled', 'true');
        updateButton(true);
    }

    function stopSnow() {
        isRunning = false;
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
        if (ctx) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
        if (canvas) {
            canvas.style.display = 'none';
        }
        snowflakes = [];
        localStorage.setItem('snowEnabled', 'false');
        updateButton(false);
    }

    function toggleSnow() {
        if (isRunning) {
            stopSnow();
        } else {
            startSnow();
        }
    }

    function updateButton(active) {
        const btn = document.getElementById('snow-toggle');
        if (btn) {
            if (active) {
                btn.classList.remove('btn-outline-info');
                btn.classList.add('btn-info');
                btn.title = '눈 효과 끄기';
            } else {
                btn.classList.remove('btn-info');
                btn.classList.add('btn-outline-info');
                btn.title = '눈 효과 켜기';
            }
        }
    }

    function init() {
        createCanvas();

        window.addEventListener('resize', resizeCanvas);

        // 버튼 이벤트 연결
        const toggleBtn = document.getElementById('snow-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', function (e) {
                e.preventDefault();
                toggleSnow();
            });
        }

        // LocalStorage에서 설정 불러오기 (기본값: ON)
        const snowEnabled = localStorage.getItem('snowEnabled');
        if (snowEnabled !== 'false') {
            startSnow();
        }
    }

    // DOM 로드 완료 후 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 전역 접근 가능하도록 노출
    window.snowEffect = {
        start: startSnow,
        stop: stopSnow,
        toggle: toggleSnow
    };
})();
