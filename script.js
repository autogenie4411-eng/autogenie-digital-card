const DEFAULT_PROFILE = '김민수';
const COMPANY_NAME = '주식회사 오토지니';

const toast = document.getElementById('toast');

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('is-show');
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => {
    toast.classList.remove('is-show');
  }, 2200);
}

function parseProfileText(text) {
  const data = {};

  text.split(/\r?\n/).forEach((line) => {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith('#')) return;

    const index = trimmed.indexOf('=');
    if (index === -1) return;

    const key = trimmed.slice(0, index).trim();
    const value = trimmed.slice(index + 1).trim();

    if (key) data[key] = value;
  });

  return data;
}

function cleanPhone(phone = '') {
  return phone.replace(/[^\d+]/g, '');
}

function setMeta(property, value) {
  const meta = document.querySelector(`meta[property="${property}"]`);
  if (meta && value) meta.setAttribute('content', value);
}

async function loadProfile() {
  if (document.body.dataset.staticCard === 'true') {
    window.currentProfileData = {
      name: document.body.dataset.profileName || '',
      siteName: document.title
    };
    return;
  }
  const params = new URLSearchParams(window.location.search);
  const profileName = (params.get('profile') || DEFAULT_PROFILE).trim();

  const profileFolder = `./sales_profiles/${encodeURIComponent(profileName)}`;
  const txtPath = `${profileFolder}/profile.txt`;

  try {
    const response = await fetch(txtPath, { cache: 'no-store' });

    if (!response.ok) {
      throw new Error(`profile.txt load failed: ${response.status}`);
    }

    const data = parseProfileText(await response.text());

    const name = data.name || profileName;
    const phone = data.phone || '';
    const email = data.email || '';
    const department = data.department || '';
    const position = data.position || '';
    const company = data.company || COMPANY_NAME;
    const siteName = data.siteName || `${name}${position ? ` ${position}` : ''} | 오토지니`;

    // photo can be a full relative path or just a filename.
    let photo = data.photo || 'profile.png';
    if (!photo.includes('/') && !photo.includes('\\')) {
      photo = `${profileFolder}/${photo}`;
    }

    const profilePhoto = document.getElementById('profilePhoto');
    const profileNameEl = document.getElementById('profileName');
    const profilePosition = document.getElementById('profilePosition');
    const profileCompany = document.getElementById('profileCompany');

    if (profilePhoto) {
      profilePhoto.src = photo;
      profilePhoto.alt = `${name} 프로필 사진`;
    }

    if (profileNameEl) profileNameEl.textContent = name;

    if (profilePosition) {
      profilePosition.innerHTML = '';
      if (department) {
        profilePosition.append(document.createTextNode(department));
      }
      if (department && position) {
        const divider = document.createElement('span');
        divider.className = 'divider';
        divider.textContent = '|';
        profilePosition.append(divider);
      }
      if (position) {
        profilePosition.append(document.createTextNode(position));
      }
    }

    if (profileCompany) profileCompany.textContent = company;

    const phoneValue = cleanPhone(phone);

    const callLink = document.getElementById('callLink');
    const smsLink = document.getElementById('smsLink');
    const phoneText = document.getElementById('phoneText');
    const emailText = document.getElementById('emailText');
    const affiliationText = document.getElementById('affiliationText');

    if (callLink && phoneValue) callLink.href = `tel:${phoneValue}`;
    if (smsLink && phoneValue) smsLink.href = `sms:${phoneValue}`;

    if (phoneText) {
      phoneText.textContent = phone;
      if (phoneValue) phoneText.href = `tel:${phoneValue}`;
    }

    if (emailText) {
      emailText.textContent = email;
      if (email) emailText.href = `mailto:${email}`;
    }

    if (affiliationText) {
      affiliationText.textContent = department;
    }

    document.title = siteName;

    // These update what a normal browser sees.
    // For Kakao crawler previews, server-rendered/static OG tags are still recommended.
    setMeta('og:title', siteName);
    setMeta('og:image:alt', `오토지니 ${name} 디지털 명함`);

    window.currentProfileData = {
      profileName,
      name,
      phone,
      email,
      department,
      position,
      company,
      siteName,
      photo
    };
  } catch (error) {
    console.error(error);

    if (window.location.protocol === 'file:') {
      showToast('profile.txt는 서버에서 열어야 자동으로 불러올 수 있습니다.');
    } else {
      showToast(`${profileName} 프로필 정보를 불러오지 못했습니다.`);
    }
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  await loadProfile();

  const kakaoBtn = document.getElementById('kakaoBtn');

  if (kakaoBtn) {
    kakaoBtn.addEventListener('click', async () => {
      const profile = window.currentProfileData || {};
      const shareData = {
        title: profile.siteName || document.title,
        text: '차량 관련 문의는 편하게 연락주세요.',
        url: window.location.href
      };

      if (navigator.share) {
        try {
          await navigator.share(shareData);
          return;
        } catch (error) {
          if (error && error.name === 'AbortError') return;
        }
      }

      try {
        await navigator.clipboard.writeText(window.location.href);
        showToast('명함 링크를 복사했습니다. 카카오톡에 붙여넣어 주세요.');
      } catch (error) {
        showToast('현재 환경에서는 공유 기능을 사용할 수 없습니다.');
      }
    });
  }
});
