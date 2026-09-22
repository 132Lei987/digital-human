// 工单编号：人工智能CV-AIGC-18-文旅智能体-智能导览与互动体验任务
const avatar = document.getElementById('avatar');
const audio = document.getElementById('audio');
const input = document.getElementById('input');
const send = document.getElementById('send');

const MOUTH = [
  '/assets/mouth_frames/mouth_0.png',
  '/assets/mouth_frames/mouth_1.png',
  '/assets/mouth_frames/mouth_2.png',
  '/assets/mouth_frames/mouth_3.png',
];

let words = [];
let rafId = null;

function mouthLevelForWord(word) {
  if (!word) return 0;              // 不说话 -> 闭嘴
  if (word.duration_ms < 250) return 1;  // 短音 -> 微张
  if (word.duration_ms < 450) return 2;  // 中音 -> 半张
  return 3;                             // 长音 -> 全张
}

function currentWord(tMs) {
  for (const w of words) {
    if (tMs >= w.start_ms && tMs <= w.start_ms + w.duration_ms) return w;
  }
  return null;
}

function tick() {
  const tMs = audio.currentTime * 1000;
  avatar.src = MOUTH[mouthLevelForWord(currentWord(tMs))];
  rafId = requestAnimationFrame(tick);
}

function stopPlayback() {
  cancelAnimationFrame(rafId);
  audio.pause();
  audio.currentTime = 0;
  avatar.src = MOUTH[0];
}

function base64ToBlob(b64, mime) {
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

async function sendMessage() {
  const message = input.value.trim();
  if (!message) return;
  input.value = '';
  send.disabled = true;
  stopPlayback();
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await resp.json();
    if (data.audio_base64) {
      audio.src = URL.createObjectURL(base64ToBlob(data.audio_base64, 'audio/mpeg'));
      words = data.words || [];
      await audio.play();
      tick();
    } else {
      console.warn('未返回音频', data.error);
      avatar.src = MOUTH[0];
    }
  } catch (e) {
    console.error(e);
    avatar.src = MOUTH[0];
  } finally {
    send.disabled = false;
  }
}

send.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
audio.addEventListener('ended', () => {
  cancelAnimationFrame(rafId);
  avatar.src = MOUTH[0];
});
