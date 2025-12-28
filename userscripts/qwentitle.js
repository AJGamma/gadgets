// ==UserScript==
// @name         Qwen Chat - Sync Title (Sidebar-Optimized)
// @match        https://chat.qwen.ai/*
// @grant        none
// ==/UserScript==

(function () {
  "use strict";

  let lastKnownTitle = document.title;
  let observer = null;

  // 从活跃对话项中提取标题
  function getActiveConversationTitle() {
    // 使用更健壮的选择器：任意包含 .chat-item-drag-active 的元素
    const activeItem = document.querySelector(".chat-item-drag-active");
    if (!activeItem) return null;

    const titleEl = activeItem.querySelector(
      ".chat-item-drag-link-content-tip-text",
    );
    return titleEl?.textContent.trim() || null;
  }

  // 同步标题（仅当有活跃对话时）
  function syncDocumentTitle() {
    const title = getActiveConversationTitle();
    if (title) {
      lastKnownTitle = title;
      if (document.title !== lastKnownTitle) {
        document.title = lastKnownTitle;
      }
    }
    // 若无活跃项，保留 lastKnownTitle，不作更新
  }

  // 初始化 MutationObserver（监听整个 body，但逻辑轻量）
  function initObserver() {
    if (observer) return;

    observer = new MutationObserver(syncDocumentTitle);
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      // 可选：若性能敏感，可限定监听区域（如包含 .sidebar-container 的祖先）
    });

    // 立即尝试同步一次
    syncDocumentTitle();
  }

  // 启动
  initObserver();
})();
