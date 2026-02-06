/**
 * Let it Snow Effect
 * Canvas 기반 눈 내리는 애니메이션
 * LocalStorage로 on/off 설정 저장
 */

class SnowEffect {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.snowflakes = [];
        this.animationId = null;
        this.isRunning = false;
        this.maxFlakes = 150;
        
        this.init();
    }
    
    init() {
        // Canvas 생성
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'snow-canvas';
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
        `;
        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        // 캔버스 크기 설정
        this.resize();
        window.addEventListener('resize', () => this.resize());
        
        // LocalStorage에서 설정 불러오기
        const snowEnabled = localStorage.getItem('snowEnabled');
        if (snowEnabled === 'true') {
            this.start();
        }
        
        // 토글 버튼 이벤트 연결
        const toggleBtn = document.getElementById('snow-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
            this.updateButtonState(toggleBtn);
        }
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createSnowflake() {
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * -100,
            radius: Math.random() * 3 + 1,
            speed: Math.random() * 1 + 0.5,
            wind: Math.random() * 0.5 - 0.25,
            opacity: Math.random() * 0.5 + 0.5
        };
    }
    
    update() {
        // 눈송이 추가
        if (this.snowflakes.length < this.maxFlakes) {
            this.snowflakes.push(this.createSnowflake());
        }
        
        // 눈송이 이동
        for (let i = this.snowflakes.length - 1; i >= 0; i--) {
            const flake = this.snowflakes[i];
            flake.y += flake.speed;
            flake.x += flake.wind;
            
            // 화면 밖으로 나가면 제거
            if (flake.y > this.canvas.height || flake.x < -10 || flake.x > this.canvas.width + 10) {
                this.snowflakes.splice(i, 1);
            }
        }
    }
    
    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        for (const flake of this.snowflakes) {
            this.ctx.beginPath();
            this.ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(255, 255, 255, ${flake.opacity})`;
            this.ctx.fill();
        }
    }
    
    animate() {
        if (!this.isRunning) return;
        
        this.update();
        this.draw();
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.canvas.style.display = 'block';
        this.animate();
        localStorage.setItem('snowEnabled', 'true');
        
        const toggleBtn = document.getElementById('snow-toggle');
        if (toggleBtn) this.updateButtonState(toggleBtn);
    }
    
    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.snowflakes = [];
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.canvas.style.display = 'none';
        localStorage.setItem('snowEnabled', 'false');
        
        const toggleBtn = document.getElementById('snow-toggle');
        if (toggleBtn) this.updateButtonState(toggleBtn);
    }
    
    toggle() {
        if (this.isRunning) {
            this.stop();
        } else {
            this.start();
        }
    }
    
    updateButtonState(btn) {
        if (this.isRunning) {
            btn.classList.add('active');
            btn.title = '눈 효과 끄기';
        } else {
            btn.classList.remove('active');
            btn.title = '눈 효과 켜기';
        }
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.snowEffect = new SnowEffect();
});
