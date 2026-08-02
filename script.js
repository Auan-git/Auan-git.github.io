/**
 * Edge's Web - JavaScript
 */

// ============================================
// Hero 翻转卡片
// ============================================
function initHeroFlip() {
    const card = document.getElementById('hero-flip');
    if (!card) return;

    card.addEventListener('click', () => {
        card.classList.toggle('flipped');
    });
}

// ============================================
// 液态玻璃背景 - 鼠标追踪
// ============================================
function initGlassBackground() {
    const root = document.documentElement;

    document.addEventListener('mousemove', (e) => {
        const x = (e.clientX / window.innerWidth) * 100;
        const y = (e.clientY / window.innerHeight) * 100;
        root.style.setProperty('--mouse-x', x + '%');
        root.style.setProperty('--mouse-y', y + '%');
    });

    // 移动端触摸支持
    document.addEventListener('touchmove', (e) => {
        const touch = e.touches[0];
        const x = (touch.clientX / window.innerWidth) * 100;
        const y = (touch.clientY / window.innerHeight) * 100;
        root.style.setProperty('--mouse-x', x + '%');
        root.style.setProperty('--mouse-y', y + '%');
    }, { passive: true });
}

// ============================================
// 主题切换 (暗色/亮色)
// ============================================
function initThemeToggle() {
    const btn = document.getElementById('nav-theme-toggle');
    if (!btn) return;

    // 读取保存的主题偏好
    const saved = localStorage.getItem('wiki-theme');
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        btn.textContent = '☀️';
    }

    btn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('wiki-theme', 'light');
            btn.textContent = '🌙';
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('wiki-theme', 'dark');
            btn.textContent = '☀️';
        }
    });
}

// ============================================
// 代码块复制按钮
// ============================================
function addCopyButtons() {
    const pres = document.querySelectorAll('.wiki pre');

    pres.forEach(pre => {
        // 避免重复添加
        if (pre.parentNode.classList.contains('code-wrapper')) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'code-wrapper';
        wrapper.style.position = 'relative';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = '复制';
        copyBtn.style.cssText = `
            position: absolute;
            top: 6px;
            right: 8px;
            background: rgba(100, 116, 139, 0.15);
            color: #64748b;
            border: none;
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        `;

        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(pre.textContent);
                copyBtn.textContent = '已复制!';
                setTimeout(() => {
                    copyBtn.textContent = '复制';
                }, 2000);
            } catch {
                // fallback
                copyBtn.textContent = '失败';
                setTimeout(() => {
                    copyBtn.textContent = '复制';
                }, 1000);
            }
        });

        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(pre);
        wrapper.appendChild(copyBtn);

        wrapper.addEventListener('mouseenter', () => {
            copyBtn.style.opacity = '1';
        });
        wrapper.addEventListener('mouseleave', () => {
            copyBtn.style.opacity = '0';
        });
    });
}

// ============================================
// 音乐播放器 - 自动播放+默认静音+歌词流动
// ============================================
function initMusicPlayer() {
    const audio = document.getElementById('music-audio');
    const lyricsEl = document.getElementById('music-lyrics');
    if (!audio || !lyricsEl) return;

    let lyrics = [];

    // 显示初始/fallback 歌词
    function showFallback() {
        lyricsEl.innerHTML = '<p>丑八怪 其实见多就不怪</p><p>放肆去high 用力踩</p><p>那不堪一击的洁白</p><p>丑八怪 这是我们的时代</p><p>我不存在 才意外</p>';
    }

    // 解析 LRC 歌词
    function parseLyrics(text) {
        lyrics = [];
        for (const line of text.split('\n')) {
            const m = line.match(/^\[(\d+):(\d+\.\d+)\](.*)$/);
            if (m) {
                const time = parseInt(m[1]) * 60 + parseFloat(m[2]);
                const txt = m[3].trim();
                if (txt) lyrics.push({ time, text: txt });
            }
        }
    }

    // 加载 LRC 文件
    function loadLyrics() {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '《丑八怪》歌词.lrc', true);
        xhr.onload = function () {
            if (xhr.status === 200 || xhr.status === 0) {
                parseLyrics(xhr.responseText);
            }
            // 立即显示初始歌词
            if (lyrics.length > 0) {
                renderAllLyrics();
            } else {
                showFallback();
            }
        };
        xhr.onerror = showFallback;
        xhr.send();
    }

    // 渲染歌词 — 全部渲染，滚动跟随
    let lastActive = -1;
    function renderAllLyrics() {
        if (lyrics.length === 0) { showFallback(); return; }
        const fragment = document.createDocumentFragment();
        lyrics.forEach((l, i) => {
            const p = document.createElement('p');
            p.textContent = l.text;
            p.dataset.index = i;
            fragment.appendChild(p);
        });
        lyricsEl.innerHTML = '';
        lyricsEl.appendChild(fragment);
        lastActive = -1;
    }

    function updateActiveLine(active) {
        if (active === lastActive) return;
        lastActive = active;
        const prev = lyricsEl.querySelector('.active-line');
        if (prev) prev.classList.remove('active-line');
        const curr = lyricsEl.querySelector(`p[data-index="${active}"]`);
        if (curr) {
            curr.classList.add('active-line');
            // JS 平滑滚动，跨浏览器一致
            const target = curr.offsetTop - lyricsEl.clientHeight / 2 + curr.offsetHeight / 2;
            smoothScrollTo(lyricsEl, target);
        }
    }

    function smoothScrollTo(el, target) {
        const start = el.scrollTop;
        const diff = target - start;
        const duration = 300;
        let startTime = null;
        function step(timestamp) {
            if (!startTime) startTime = timestamp;
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // ease-out
            const ease = 1 - Math.pow(1 - progress, 3);
            el.scrollTop = start + diff * ease;
            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    }

    function updateLyrics() {
        if (lyrics.length === 0) return;
        const t = audio.currentTime;
        let active = 0;
        for (let i = 0; i < lyrics.length; i++) {
            if (lyrics[i].time <= t) active = i;
        }
        if (active !== lastActive) {
            updateActiveLine(active);
        }
    }

    audio.addEventListener('timeupdate', updateLyrics);

    audio.addEventListener('ended', () => {
        lastActive = -1;
        lyricsEl.scrollTo({ top: 0, behavior: 'smooth' });
        audio.currentTime = 0;
        audio.play().catch(() => {});
    });

    // 自动播放（静音）——兜底：用户首次点击页面时触发
    audio.play().catch(() => {});
    document.addEventListener('click', function autoPlayOnce() {
        if (audio.paused) audio.play().catch(() => {});
    }, { once: true });

    // 立即加载歌词
    loadLyrics();

    // 点击切换静音
    const muteBtn = document.getElementById('nav-music-mute');
    if (muteBtn) {
        muteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            audio.muted = !audio.muted;
            muteBtn.textContent = audio.muted ? '🔇' : '🔊';
        });
    }
}

// ============================================
// 目录 (TOC) - 悬浮侧边栏 + 平滑滚动 + 高亮
// ============================================
function initTOC() {
    const toggleBtn = document.getElementById('toc-toggle-btn');
    const sidebar = document.getElementById('toc-sidebar');
    const closeBtn = document.getElementById('toc-close-btn');

    if (!toggleBtn || !sidebar) return;

    const tocNav = sidebar.querySelector('.toc');
    const tocLinks = sidebar.querySelectorAll('.toc a');
    const headings = [];

    // 收集页面中所有有 id 的标题
    tocLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.startsWith('#')) {
            const target = document.getElementById(href.slice(1));
            if (target) {
                headings.push({ link, target });
            }
        }
    });

    // --- 打开/关闭逻辑 ---
    function openTOC() {
        sidebar.classList.add('open');
        toggleBtn.classList.add('toc-open');
        document.body.classList.add('toc-open');
        // 聚焦关闭按钮
        if (closeBtn) setTimeout(() => closeBtn.focus(), 100);
    }

    function closeTOC() {
        sidebar.classList.remove('open');
        toggleBtn.classList.remove('toc-open');
        document.body.classList.remove('toc-open');
        toggleBtn.focus();
    }

    function toggleTOC() {
        if (sidebar.classList.contains('open')) {
            closeTOC();
        } else {
            openTOC();
        }
    }

    toggleBtn.addEventListener('click', toggleTOC);
    if (closeBtn) closeBtn.addEventListener('click', closeTOC);

    // ESC 关闭
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeTOC();
        }
    });

    // --- 点击 TOC 链接 → 平滑滚动 + 关闭面板（移动端） ---
    tocLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (!href || !href.startsWith('#')) return;
            const target = document.getElementById(href.slice(1));
            if (target) {
                e.preventDefault();
                const offset = 80;
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
                history.replaceState(null, null, href);
                // 移动端点击后关闭目录
                if (window.innerWidth < 768) {
                    closeTOC();
                }
            }
        });
    });

    if (headings.length === 0) return;

    // --- 滚动时高亮当前标题对应的 TOC 项 ---
    let activeLink = null;
    function updateActiveHeading() {
        const scrollY = window.scrollY + 120;

        let current = headings[0];
        for (let i = headings.length - 1; i >= 0; i--) {
            if (headings[i].target.offsetTop < scrollY) {
                current = headings[i];
                break;
            }
        }

        if (activeLink !== current.link) {
            // 移除旧高亮
            if (activeLink) {
                activeLink.classList.remove('toc-active');
            }
            // 添加新高亮
            current.link.classList.add('toc-active');
            activeLink = current.link;

            // TOC 内滚动跟随
            if (tocNav) {
                const linkTop = current.link.offsetTop;
                const navHeight = tocNav.offsetHeight;
                tocNav.scrollTop = linkTop - navHeight / 3;
            }
        }
    }

    // 节流滚动事件
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                updateActiveHeading();
                ticking = false;
            });
            ticking = true;
        }
    });

    // 初始高亮
    updateActiveHeading();
}

// ============================================
// 键盘快捷键
// ============================================
function handleKeyboardShortcuts(event) {
    // Escape: 移除焦点
    if (event.key === 'Escape') {
        if (document.activeElement instanceof HTMLElement) {
            document.activeElement.blur();
        }
    }
}

// ============================================
// 初始化
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initHeroFlip();
    initMusicPlayer();
    initGlassBackground();
    initThemeToggle();
    initTOC();
    addCopyButtons();

    // 向下滚动箭头
    const arrow = document.getElementById('scroll-arrow');
    if (arrow) {
        arrow.addEventListener('click', () => {
            const hero = document.querySelector('.hero');
            if (hero) {
                const heroBottom = hero.getBoundingClientRect().bottom + window.scrollY;
                window.scrollTo({ top: heroBottom - 40, behavior: 'smooth' });
            }
        });

        // 回到顶部时重新显示箭头
        window.addEventListener('scroll', () => {
            if (window.scrollY < 100) {
                arrow.style.display = 'flex';
            } else {
                arrow.style.display = 'none';
            }
        });
    }

    document.addEventListener('keydown', handleKeyboardShortcuts);

    console.log('Edge\'s Web 已加载');
});
