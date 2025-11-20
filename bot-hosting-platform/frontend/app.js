const apiBase = '';

function getToken() {
  return localStorage.getItem('token');
}

function authRequired() {
  if (!getToken()) {
    window.location.href = '/';
  }
}

function logout() {
  localStorage.removeItem('token');
  window.location.href = '/';
}

async function apiGet(url) {
  const res = await fetch(apiBase + url, {
    headers: { 'Authorization': 'Bearer ' + getToken() }
  });
  return res.json();
}

async function apiPost(url, data, isFormUrlEncoded = false) {
  const headers = {};
  if (isFormUrlEncoded) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
  } else if (!(data instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    data = JSON.stringify(data);
  }
  if (!isFormUrlEncoded) {
    headers['Authorization'] = 'Bearer ' + getToken();
  } else {
    headers['Authorization'] = 'Bearer ' + getToken();
  }
  const res = await fetch(apiBase + url, {
    method: 'POST',
    headers,
    body: data
  });
  return res.json();
}

async function apiPostJson(url, body) {
  const res = await fetch(apiBase + url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  return res.json();
}
