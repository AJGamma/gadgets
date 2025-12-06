// ==UserScript==
// @name         Qwen Chat - Sync Title (Sidebar-Optimized)
// @match        https://chat.qwen.ai/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    let lastKnownTitle = document.title;
    let observer = null;

    function updateTitleIfSidebarOpen() {
        const activeLink = document.querySelector('#sidebar a.chat-item-drag-link.chat-item-drag-active');
        if (!activeLink) return;

        const titleEl = activeLink.querySelector('.chat-item-drag-link-content-tip-text');
        if (titleEl?.textContent.trim()) {
            lastKnownTitle = titleEl.textContent.trim();
            if (document.title !== lastKnownTitle) {
                document.title = lastKnownTitle;
            }
        }
    }

    function initObserver() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        // 如果已有 observer，先断开
        if (observer) observer.disconnect();

        // 仅监听侧边栏内部变化
        observer = new MutationObserver(updateTitleIfSidebarOpen);
        observer.observe(sidebar, {
            childList: true,
            subtree: true,
        });

        // 立即尝试更新一次
        updateTitleIfSidebarOpen();
    }

    // 初始尝试初始化
    initObserver();

    // 若侧边栏是动态加载的（如 SPA 路由后渲染），需等待其出现
    if (!document.getElementById('sidebar')) {
        const checkInterval = setInterval(() => {
            if (document.getElementById('sidebar')) {
                clearInterval(checkInterval);
                initObserver();
            }
        }, 500);
    }
})();
