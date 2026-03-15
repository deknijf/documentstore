const SHARE_DB_NAME = "docstore-share-target";
const SHARE_STORE_NAME = "pending-shares";
const SHARE_REDIRECT_URL = "/#/documenten?shared=1";

self.addEventListener("install", (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname === "/share-target" && event.request.method === "POST") {
    event.respondWith(handleShareTarget(event));
  }
});

self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type === "docstore-share-consume") {
    event.waitUntil(sendPendingShares(event.source));
    return;
  }
  if (data.type === "docstore-share-ack") {
    event.waitUntil(deletePendingShares(Array.isArray(data.ids) ? data.ids : []));
  }
});

function openShareDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(SHARE_DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(SHARE_STORE_NAME)) {
        db.createObjectStore(SHARE_STORE_NAME, { keyPath: "id" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function withStore(mode, fn) {
  const db = await openShareDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(SHARE_STORE_NAME, mode);
    const store = tx.objectStore(SHARE_STORE_NAME);
    let result;
    try {
      result = fn(store);
    } catch (err) {
      reject(err);
      return;
    }
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  }).finally(() => db.close());
}

async function putPendingShare(batch) {
  await withStore("readwrite", (store) => {
    store.put(batch);
  });
}

async function listPendingShares() {
  return withStore("readonly", (store) => {
    return new Promise((resolve, reject) => {
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  });
}

async function deletePendingShares(ids) {
  const uniqueIds = Array.from(new Set((ids || []).map((x) => String(x || "").trim()).filter(Boolean)));
  if (!uniqueIds.length) return;
  await withStore("readwrite", (store) => {
    uniqueIds.forEach((id) => store.delete(id));
  });
}

async function handleShareTarget(event) {
  const formData = await event.request.formData();
  const sharedFiles = formData.getAll("shared_files").filter((entry) => entry instanceof File && entry.size > 0);
  if (sharedFiles.length) {
    await putPendingShare({
      id: self.crypto.randomUUID(),
      created_at: Date.now(),
      items: sharedFiles.map((file) => ({
        name: file.name || "shared-document",
        type: file.type || "application/octet-stream",
        lastModified: Number(file.lastModified || Date.now()),
        blob: file,
      })),
    });
  }

  const clients = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
  const primary = clients[0];
  if (primary) {
    primary.postMessage({ type: "docstore-share-available" });
    await primary.focus();
  } else {
    await self.clients.openWindow(SHARE_REDIRECT_URL);
  }
  return Response.redirect(SHARE_REDIRECT_URL, 303);
}

async function sendPendingShares(client) {
  if (!client || typeof client.postMessage !== "function") return;
  const batches = await listPendingShares();
  const sorted = (batches || [])
    .slice()
    .sort((a, b) => Number((a && a.created_at) || 0) - Number((b && b.created_at) || 0))
    .map((batch) => ({
      id: String((batch && batch.id) || ""),
      created_at: Number((batch && batch.created_at) || 0),
      items: Array.isArray(batch && batch.items)
        ? batch.items.map((item) => new File([item.blob], item.name || "shared-document", {
            type: item.type || "application/octet-stream",
            lastModified: Number(item.lastModified || Date.now()),
          }))
        : [],
    }))
    .filter((batch) => batch.id && batch.items.length);
  client.postMessage({ type: "docstore-share-files", batches: sorted });
}
