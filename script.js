const toast = document.getElementById('toast');

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('is-show');
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {
    toast.classList.remove('is-show');
  }, 2200);
}

document.getElementById('kakaoBtn').addEventListener('click', async () => {
  const shareData = {
    title: '김민수 매니저 | 오토지니',
    text: '차량 관련 문의는 편하게 연락주세요.',
    url: window.location.href
  };

  if (navigator.share) {
    try {
      await navigator.share(shareData);
      return;
    } catch (e) {}
  }

  try {
    await navigator.clipboard.writeText(window.location.href);
    showToast('명함 링크를 복사했습니다. 카카오톡에 붙여넣어 주세요.');
  } catch (e) {
    showToast('현재 환경에서는 공유 기능을 사용할 수 없습니다.');
  }
});
