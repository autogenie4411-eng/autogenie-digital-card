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


function formatPhoneNumber(value) {
  const digits = String(value || '').replace(/\D/g, '');

  if (/^01[016789]\d{7,8}$/.test(digits)) {
    if (digits.length === 10) {
      return digits.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
    }
    if (digits.length === 11) {
      return digits.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');
    }
  }

  return value || '';
}

async function loadProfile() {
  if (document.body.dataset.staticCard === 'true') {
    window.currentProfileData = {
      name: document.body.dataset.profileName || '',
      kakaoChatUrl: document.body.dataset.kakaoChatUrl || '',
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
    const kakaoChatUrl = data.kakaoChatUrl || '';
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

    if (phoneValue) {
      if (callLink) callLink.href = `tel:${phoneValue}`;
      if (smsLink) smsLink.href = `sms:${phoneValue}`;

      if (phoneText) {
        phoneText.textContent = formatPhoneNumber(phone);
        phoneText.href = `tel:${phoneValue}`;
      }
    } else {
      // phone= is optional. If omitted/blank, hide phone-only UI.
      if (callLink) callLink.hidden = true;
      if (smsLink) smsLink.hidden = true;

      if (phoneText) {
        const phoneRow = phoneText.closest('div');
        if (phoneRow) phoneRow.hidden = true;
      }
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
      kakaoChatUrl,
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
    kakaoBtn.addEventListener('click', () => {
      const profile = window.currentProfileData || {};
      const kakaoChatUrl = (profile.kakaoChatUrl || '').trim();

      if (!kakaoChatUrl) {
        showToast('등록된 카카오톡 상담 링크가 없습니다.');
        alert('profile.txt에 kakaoChatUrl을 입력해 주세요.');
        return;
      }

      window.location.href = kakaoChatUrl;
    });
  }
});
