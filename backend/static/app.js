/* Fundus-Read minimal frontend (no build step)
   - Uses cookie HttpOnly (credentials: "include")
   - Pages: index, mode, read
*/

function qs(id) { return document.getElementById(id); }

function getPage() {
  const b = document.body;
  return b ? (b.getAttribute("data-page") || "") : "";
}

function setMsg(text, kind = "error") {
  const el = qs("msg");
  if (!el) return;
  el.className = "msg " + (kind === "ok" ? "msg-ok" : "msg-error");
  el.textContent = text || "";
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    credentials: "include",
    ...opts,
  });
  const contentType = res.headers.get("content-type") || "";
  let body = null;
  if (contentType.includes("application/json")) body = await res.json().catch(() => null);
  else body = await res.text().catch(() => null);
  return { res, body };
}

async function ensureAuthOrRedirect() {
  const { res } = await api("/auth/me");
  if (!res.ok) {
    window.location.href = "/";
    return null;
  }
  const { body } = await api("/auth/me");
  return body;
}

function getModoFromQuery() {
  const p = new URLSearchParams(window.location.search);
  const v = p.get("modo_id");
  if (v === null) return null;
  const n = Number(v);
  if (!Number.isFinite(n)) return null;
  return n;
}

function modelLabel(modelo_id) {
  // Ajusta si tu mapping real difiere
  const m = {
    0: "Ensemble",
    1: "MobileNetV3Large",
    2: "EfficientNetB0",
    3: "ConvNeXtTiny",
  };
  return m[modelo_id] || ("Modelo " + modelo_id);
}

function addImageBlock(title, url) {
  const root = qs("images");
  if (!root) return;

  const block = document.createElement("div");
  block.className = "img-block";

  const h = document.createElement("div");
  h.className = "img-title";
  h.textContent = title;

  const img = document.createElement("img");
  img.className = "img";
  img.src = url;
  img.alt = title;

  block.appendChild(h);
  block.appendChild(img);
  root.appendChild(block);
}

async function pageIndex() {
  const btn = qs("btnLogin");
  const cc = qs("cc");
  const pw = qs("password");

  if (!btn || !cc || !pw) return;

  btn.addEventListener("click", async () => {
    setMsg("");

    const ccVal = cc.value.trim();
    const pwVal = pw.value;

    if (!ccVal || !pwVal) {
      setMsg("Falta: cc y/o password");
      return;
    }

    // evita el error bcrypt de 72 bytes (si en backend no lo controlas)
    if (new TextEncoder().encode(pwVal).length > 72) {
      setMsg("Password demasiado largo (límite bcrypt: 72 bytes)");
      return;
    }

    const { res, body } = await api("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cc: ccVal, password: pwVal }),
    });

    if (!res.ok) {
      const detail = (body && body.detail) ? body.detail : JSON.stringify(body);
      setMsg("HTTP " + res.status + "\n" + detail);
      return;
    }

    if (body && body.success) {
      setMsg("Login OK. Redirigiendo...", "ok");
      window.location.href = "/mode";
      return;
    }

    setMsg((body && body.message) ? body.message : "Credenciales inválidas");
  });

  // Enter para login
  pw.addEventListener("keydown", (e) => {
    if (e.key === "Enter") btn.click();
  });
}

async function pageMode() {
  setMsg("");

  const who = qs("whoami");
  const btn0 = qs("btnNoAsistido");
  const btn1 = qs("btnAsistido");
  const btnLogout = qs("btnLogout");

  const me = await ensureAuthOrRedirect();
  if (!me) return;

  if (who) who.textContent = `Sesión: cc=${me.cc} • role=${me.role}`;

  if (btn0) btn0.addEventListener("click", () => {
    window.location.href = "/na_read";
  });

  if (btn1) btn1.addEventListener("click", () => {
    window.location.href = "/read?modo_id=1";
  });

  if (btnLogout) btnLogout.addEventListener("click", async () => {
    await api("/auth/logout", { method: "POST" });
    window.location.href = "/";
  });
}

async function pageRead() {
  setMsg("");

  const meta = qs("meta");
  const btnReload = qs("btnReload");
  const root = qs("images");

  if (btnReload) btnReload.addEventListener("click", () => window.location.reload());

  const me = await ensureAuthOrRedirect();
  if (!me) return;

  const modo_id = getModoFromQuery();
  if (modo_id !== 0 && modo_id !== 1) {
    setMsg("Falta/invalid: modo_id (usa /read?modo_id=0 o /read?modo_id=1)");
    return;
  }

  if (meta) meta.textContent = `Usuario cc=${me.cc} • modo_id=${modo_id} • cargando primera lectura...`;
  if (root) root.innerHTML = "";

  // 1) reading/next
  const nextResp = await api(`/reading/next?modo_id=${modo_id}`);
  if (!nextResp.res.ok) {
    setMsg("Error /reading/next\nHTTP " + nextResp.res.status + "\n" + (nextResp.body?.detail || JSON.stringify(nextResp.body)));
    return;
  }
  if (!nextResp.body || !nextResp.body.found) {
    setMsg(nextResp.body?.message || "No hay lecturas pendientes");
    return;
  }

  const { lectura_id, img_id, posicion } = nextResp.body;
  if (meta) meta.textContent = `lectura_id=${lectura_id} • img_id=${img_id} • posicion=${posicion} • modo_id=${modo_id}`;

  // 2) images/{img_id}
  const imgResp = await api(`/images/${img_id}`);
  if (!imgResp.res.ok) {
    setMsg("Error /images/{img_id}\nHTTP " + imgResp.res.status + "\n" + (imgResp.body?.detail || JSON.stringify(imgResp.body)));
    return;
  }
  addImageBlock("Fundus", imgResp.body.url);

  // 3) gradcam/{img_id} (solo si modo asistido, como pediste siempre mostramos 4 gradcam en esa pantalla)
  // Si quieres que en modo no asistido NO se vean gradcam, cambia el if:
  // if (modo_id === 1) { ... }
  const gcResp = await api(`/gradcam/${img_id}`);
  if (!gcResp.res.ok) {
    setMsg("Error /gradcam/{img_id}\nHTTP " + gcResp.res.status + "\n" + (gcResp.body?.detail || JSON.stringify(gcResp.body)));
    return;
  }

  const gradcams = (gcResp.body && gcResp.body.gradcams) ? gcResp.body.gradcams : [];
  if (!Array.isArray(gradcams) || gradcams.length === 0) {
    // en tu diseño: igual mostramos fundus; gradcam podría estar vacío
    return;
  }

  // Querías 4 gradcam: ensemble + 3 modelos. Tomamos por modelo_id.
  const byModel = new Map();
  for (const g of gradcams) byModel.set(g.modelo_id, g);

  const order = [0, 1, 2, 3];
  for (const mid of order) {
    const g = byModel.get(mid);
    if (!g) continue;
    addImageBlock(modelLabel(mid), g.url);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const page = getPage();
  if (page === "index") pageIndex();
  else if (page === "mode") pageMode();
  else if (page === "read") pageRead();
  else if (page === "na_read") pageNaRead();
});

function addRadioOption(name, value, label) {
  const root = qs("classOptions");
  if (!root) return;

  const wrap = document.createElement("label");
  wrap.className = "label";
  wrap.style.fontWeight = "400";
  wrap.style.display = "flex";
  wrap.style.alignItems = "center";
  wrap.style.gap = "10px";
  wrap.style.marginTop = "10px";

  const input = document.createElement("input");
  input.type = "radio";
  input.name = name;
  input.value = value;

  const span = document.createElement("span");
  span.textContent = label;

  wrap.appendChild(input);
  wrap.appendChild(span);
  root.appendChild(wrap);
}

async function pageNaRead() {
  setMsg("");

  const meta = qs("meta");
  const root = qs("images");
  const optionsRoot = qs("classOptions");
  const form = qs("diagnosisForm");
  const btnNext = qs("btnNext");

  const me = await ensureAuthOrRedirect();
  if (!me) return;

  if (root) root.innerHTML = "";
  if (optionsRoot) optionsRoot.innerHTML = "";

  const nextResp = await api("/reading/next-na");
  if (!nextResp.res.ok) {
    setMsg("Error /reading/next-na\nHTTP " + nextResp.res.status + "\n" + (nextResp.body?.detail || JSON.stringify(nextResp.body)));
    return;
  }

  if (!nextResp.body || !nextResp.body.found) {
    setMsg(nextResp.body?.message || "No hay lecturas pendientes");
    return;
  }

  const { lectura_id, img_id, posicion, url } = nextResp.body;

  if (meta) {
    meta.textContent = `Usuario cc=${me.cc} • lectura_id=${lectura_id} • img_id=${img_id} • posición=${posicion}`;
  }

  addImageBlock("Fundus", url);

  const clsResp = await api("/clases");
  if (!clsResp.res.ok) {
    setMsg("Error /clases\nHTTP " + clsResp.res.status + "\n" + (clsResp.body?.detail || JSON.stringify(clsResp.body)));
    return;
  }

  const clases = (clsResp.body && clsResp.body.clases) ? clsResp.body.clases : [];
  for (const c of clases) {
    addRadioOption("diagnostico_clase_id", c.clase_id, c.nombre);
  }

  document.querySelectorAll('input[name="diagnostico_clase_id"]').forEach((el) => {
    el.addEventListener("change", () => {
      btnNext.disabled = !document.querySelector('input[name="diagnostico_clase_id"]:checked');
    });
  });

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const selected = document.querySelector('input[name="diagnostico_clase_id"]:checked');
      if (!selected) {
        setMsg("Debes seleccionar una clase diagnóstica");
        return;
      }

      btnNext.disabled = true;

      const submitResp = await api("/reading/submit-na", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lectura_id: lectura_id,
          diagnostico_clase_id: selected.value
        }),
      });

      if (!submitResp.res.ok) {
        btnNext.disabled = false;
        setMsg("Error /reading/submit-na\nHTTP " + submitResp.res.status + "\n" + (submitResp.body?.detail || JSON.stringify(submitResp.body)));
        return;
      }

      window.location.reload();
    });
  }
}