// ==UserScript==
// @name         Bilibili 播放列表时长统计
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  显示播放列表视频总进度
// @author       Adrian
// @match        https://www.bilibili.com/video/*
// @grant        none
// ==/UserScript==

;(function () {
  'use strict'

  function parseTimeString(timeStr) {
    // 解析 "12:34" 或 "1:02:45" 形式的时间字符串
    const parts = timeStr.split(':').map((num) => parseInt(num, 10))
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1] // mm:ss
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2] // hh:mm:ss
    }
    return 0
  }

  function formatTime(seconds) {
    // 将秒数转换为 hh:mm:ss 或 mm:ss 形式
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return h > 0
      ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
      : `${m}:${String(s).padStart(2, '0')}`
  }

  function getCurrentTimeInCurrentVideo() {
    const currentTime = document.querySelector('.bpx-player-ctrl-time-current')
    if (!currentTime) return 0
    return parseTimeString(currentTime.innerText.trim())
  }

  function calculatePlaylistDuration() {
    console.log('calculating playlist duration')
    let totalDuration = 0
    let playedDuration = 0
    // get current video index
    const amt = document.querySelector('.amt')
    if (!amt) return
    if (!amt.innerText.includes('/')) return
    const video_n = parseInt(amt.innerText.match(/\d+/)[0], 10)
    if (!video_n) return
    console.log('video_n: ' + video_n)

    // 获取播放列表
    const playlist = document.querySelector('.video-pod__list')
    if (!playlist) return

    // 获取所有视频项
    const videoItems = playlist.querySelectorAll('.video-pod__item')
    if (!videoItems.length) return

    videoItems.forEach((item, index) => {
      const timeElement = item.querySelector('.duration') // 假设时长信息在 .duration 类中
      if (timeElement) {
        const duration = parseTimeString(timeElement.innerText.trim())
        totalDuration += duration
        if (index < video_n - 1) {
          playedDuration += duration
        }
      }
    })
    playedDuration += getCurrentTimeInCurrentVideo()

    if (totalDuration === 0) return

    const currentPercentage = ((playedDuration / totalDuration) * 100).toFixed(
      2,
    )

    displayDurationInfo(totalDuration, playedDuration, currentPercentage)
  }

  function displayDurationInfo(total, current, percentage) {
    const playerTime = document.querySelector('.bpx-player-ctrl-time-label')
    // show percentage with only 2 decimal places
    const togo = total - current
    const formattedText = `(${formatTime(current)} / ${formatTime(total)}  :  ${formatTime(togo)}   ${Math.round(percentage)}%)`
    if (!playerTime) return
    const durationInfoSpan = document.getElementById('duration-info')
    if (durationInfoSpan) {
      durationInfoSpan.innerText = formattedText
      return
    } else {
      const durationInfo = document.createElement('span')
      durationInfo.id = 'duration-info'
      // durationInfo.style.fontSize = '12px'
      // durationInfo.style.color = "#ddd"
      durationInfo.style.marginLeft = '10px'
      durationInfo.innerText = formattedText
      playerTime.appendChild(durationInfo)
    }
  }

  // 监听播放列表变化
  function observePlaylistChanges() {
    const targetNode = document.querySelector('.bpx-player-ctrl-time-current')
    if (!targetNode) return

    const observer = new MutationObserver(() => {
      calculatePlaylistDuration()
    })

    observer.observe(targetNode, { childList: true, subtree: true })
  }

  function init() {
    setTimeout(() => {
      calculatePlaylistDuration()
      observePlaylistChanges()
    }, 2000)
  }

  window.addEventListener('load', init)
})()
